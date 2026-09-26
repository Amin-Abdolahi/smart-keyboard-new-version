# smartkeyboard/detector.py
# تشخیص نیاز به تبدیل layout

from .converter import convert_text, get_conversion_candidates
from .dictionary import get_dictionary
from .languages import get_language_info


# --- آستانه‌ها ---
AUTO_CONVERT_THRESHOLD = 0.8
SUGGEST_THRESHOLD = 0.4
MIN_WORD_LENGTH = 2


class DetectionResult:
    """نتیجه تشخیص."""

    def __init__(self, action, original, suggested, confidence, from_lang, to_lang):
        self.action = action
        self.original = original
        self.suggested = suggested
        self.confidence = confidence
        self.from_lang = from_lang
        self.to_lang = to_lang

    def __repr__(self):
        return (
            f"DetectionResult(action={self.action}, "
            f"confidence={self.confidence:.2f}, "
            f"'{self.original}' -> '{self.suggested}')"
        )


def _char_ratio(text, lang):
    """
    نسبت حروف معتبر یه زبان به کل حروف.
    """
    if not text:
        return 0.0

    if lang == "fa":
        valid = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        total = sum(1 for c in text if c.isalpha() or '\u0600' <= c <= '\u06FF')
    elif lang == "en":
        valid = sum(1 for c in text if c.isascii() and c.isalpha())
        total = sum(1 for c in text if c.isalpha())
    else:
        valid = 0
        total = 0

    if total == 0:
        return 0.0
    return valid / total


def _count_known_words(text, dictionary, lang):
    """شمارش کلمات شناخته‌شده توی یه متن."""
    if not text:
        return 0, 0

    words = text.strip().split()
    if not words:
        return 0, 0

    known = 0
    total = 0
    for w in words:
        clean = w.strip('.,!?;:؟،!؛')
        if len(clean) < MIN_WORD_LENGTH:
            continue
        total += 1
        if lang == "fa":
            if dictionary.is_persian_word(clean):
                known += 1
        elif lang == "en":
            if dictionary.is_english_word(clean.lower()):
                known += 1
        elif lang == "de":
            if dictionary.is_english_word(clean.lower()):
                known += 1

    return known, total


def _score_conversion(original, converted, dictionary, from_lang, to_lang):
    """
    امتیازدهی به یه تبدیل.
    ترکیبی از امتیاز کلمه‌ای و امتیاز حرفی.
    """
    # کلمات شناخته‌شده
    orig_known, orig_total = _count_known_words(original, dictionary, from_lang)
    conv_known, conv_total = _count_known_words(converted, dictionary, to_lang)

    # نسبت حروف
    orig_char_ratio = _char_ratio(original, from_lang)
    conv_char_ratio = _char_ratio(converted, to_lang)

    # امتیاز کلمه‌ای (چقدر کلمات معنی‌دارن)
    orig_word_score = orig_known / orig_total if orig_total > 0 else 0.0
    conv_word_score = conv_known / conv_total if conv_total > 0 else 0.0

    # امتیاز نهایی: ترکیب کلمه‌ای (70%) و حرفی (30%)
    orig_score = (orig_word_score * 0.7) + (orig_char_ratio * 0.3)
    conv_score = (conv_word_score * 0.7) + (conv_char_ratio * 0.3)

    # اطمینان
    if conv_score > orig_score:
        confidence = conv_score - (orig_score * 0.5)
    else:
        confidence = 0.0

    # اگه متن اصلی کاملاً معنی‌داره، تبدیل نکن
    if orig_score >= 0.8:
        confidence = 0.0

    reason = f"orig_word={orig_known}/{orig_total}, conv_word={conv_known}/{conv_total}, orig_char={orig_char_ratio:.2f}, conv_char={conv_char_ratio:.2f}"
    return min(confidence, 1.0), reason


def detect(text, current_lang, active_langs, dictionary=None):
    """تشخیص نیاز به تبدیل برای یه متن."""
    if dictionary is None:
        dictionary = get_dictionary()

    text = text.strip()
    if not text:
        return DetectionResult('keep', text, text, 0.0, current_lang, current_lang)

    if dictionary.is_ignored(text) or dictionary.is_whitelisted(text):
        return DetectionResult('keep', text, text, 0.0, current_lang, current_lang)

    candidates = get_conversion_candidates(text, current_lang, active_langs)
    if not candidates:
        return DetectionResult('keep', text, text, 0.0, current_lang, current_lang)

    best = None
    best_confidence = 0.0
    best_reason = ""

    for c in candidates:
        confidence, reason = _score_conversion(
            text, c['text'], dictionary, c['from'], c['to']
        )
        if confidence > best_confidence:
            best_confidence = confidence
            best = c
            best_reason = reason

    if best is None or best_confidence < SUGGEST_THRESHOLD:
        return DetectionResult('keep', text, text, best_confidence, current_lang, current_lang)

    if best_confidence >= AUTO_CONVERT_THRESHOLD:
        action = 'auto'
    else:
        action = 'suggest'

    return DetectionResult(
        action=action,
        original=text,
        suggested=best['text'],
        confidence=best_confidence,
        from_lang=best['from'],
        to_lang=best['to'],
    )


def detect_word_by_word(text, current_lang, active_langs, dictionary=None):
    """تشخیص کلمه به کلمه (برای متن‌های طولانی)."""
    if dictionary is None:
        dictionary = get_dictionary()

    results = []
    words = text.split()
    for w in words:
        clean = w.strip('.,!?;:؟،!؛')
        if len(clean) < MIN_WORD_LENGTH:
            continue
        result = detect(clean, current_lang, active_langs, dictionary)
        if result.action != 'keep':
            results.append(result)
    return results


if __name__ == "__main__":
    print("=== تست detector ===\n")

    tests = [
        ('sghl', 'en', ['fa', 'en']),
        ('hello', 'en', ['fa', 'en']),
        ('سلام', 'fa', ['fa', 'en']),
        ('sghl phgj ]x,vi', 'en', ['fa', 'en']),
        ('asdfgh', 'en', ['fa', 'en']),
        ('AI', 'fa', ['fa', 'en']),
    ]

    for text, lang, langs in tests:
        r = detect(text, lang, langs)
        print(f"'{text}' (layout={lang}):")
        print(f"   {r}\n")