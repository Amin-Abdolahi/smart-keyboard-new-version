# smartkeyboard/detector.py
# تشخیص نیاز به تبدیل layout

from .converter import convert_text, get_conversion_candidates
from .dictionary import get_dictionary
from .languages import get_language_info


# --- آستانه‌ها ---
AUTO_CONVERT_THRESHOLD = 0.9
SUGGEST_THRESHOLD = 0.5
MIN_WORD_LENGTH = 2


class DetectionResult:
    """نتیجه تشخیص."""

    def __init__(self, action, original, suggested, confidence, from_lang, to_lang):
        self.action = action          # 'auto' | 'suggest' | 'keep'
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
        # حذف علائم نگارشی از ابتدا و انتهای کلمه
        clean = w.strip('.,!?;:؟،!؛')
        if len(clean) < MIN_WORD_LENGTH:
            continue
        total += 1
        if lang == "fa":
            if dictionary.is_persian_word(clean):
                known += 1
        elif lang == "en":
            if dictionary.is_english_word(clean):
                known += 1
        elif lang == "de":
            # فعلاً آلمانی رو ساده بگیر
            if dictionary.is_english_word(clean):
                known += 1

    return known, total


def _score_conversion(original, converted, dictionary, from_lang, to_lang):
    """
    امتیازدهی به یه تبدیل.
    برمی‌گردونه: (اطمینان، توضیح)
    """
    # کلمات شناخته‌شده توی متن اصلی
    orig_known, orig_total = _count_known_words(original, dictionary, from_lang)

    # کلمات شناخته‌شده توی متن تبدیل‌شده
    conv_known, conv_total = _count_known_words(converted, dictionary, to_lang)

    if conv_total == 0:
        return 0.0, "متن تبدیل‌شده کلمه معتبری نداره"

    # نسبت کلمات معنی‌دار
    orig_ratio = orig_known / orig_total if orig_total > 0 else 0.0
    conv_ratio = conv_known / conv_total if conv_total > 0 else 0.0

    # اطمینان: چقدر متن تبدیل‌شده بهتر از متن اصلیه
    if conv_ratio > orig_ratio:
        confidence = conv_ratio - (orig_ratio * 0.5)
    else:
        confidence = 0.0

    # اگه متن اصلی کاملاً معنی‌داره، تبدیل نکن
    if orig_ratio >= 0.8:
        confidence = 0.0

    return min(confidence, 1.0), f"orig={orig_known}/{orig_total}, conv={conv_known}/{conv_total}"


def detect(text, current_lang, active_langs, dictionary=None):
    """
    تشخیص نیاز به تبدیل برای یه متن.

    Args:
        text: متن تایپ‌شده
        current_lang: زبان layout فعلی
        active_langs: لیست زبان‌های فعال
        dictionary: نمونه دیکشنری (اگه None، از singleton استفاده میشه)

    Returns:
        DetectionResult
    """
    if dictionary is None:
        dictionary = get_dictionary()

    text = text.strip()
    if not text:
        return DetectionResult('keep', text, text, 0.0, current_lang, current_lang)

    # اگه متن توی whitelist یا ignored هست، هیچ کاری نکن
    if dictionary.is_ignored(text) or dictionary.is_whitelisted(text):
        return DetectionResult('keep', text, text, 0.0, current_lang, current_lang)

    # تولید تبدیل‌های ممکن
    candidates = get_conversion_candidates(text, current_lang, active_langs)
    if not candidates:
        return DetectionResult('keep', text, text, 0.0, current_lang, current_lang)

    # امتیازدهی به هر تبدیل
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

    # تعیین action
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
    """
    تشخیص کلمه به کلمه (برای متن‌های طولانی).
    برمی‌گردونه لیست DetectionResult.
    """
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

    # تست ۱: sghl با layout انگلیسی
    print("1. 'sghl' با layout=en:")
    r = detect('sghl', 'en', ['fa', 'en'])
    print(f"   {r}\n")

    # تست ۲: hello با layout انگلیسی (نباید تبدیل بشه)
    print("2. 'hello' با layout=en:")
    r = detect('hello', 'en', ['fa', 'en'])
    print(f"   {r}\n")

    # تست ۳: سلام با layout فارسی (نباید تبدیل بشه)
    print("3. 'سلام' با layout=fa:")
    r = detect('سلام', 'fa', ['fa', 'en'])
    print(f"   {r}\n")

    # تست ۴: جمله کامل
    print("4. 'sghl ,hkd' با layout=en:")
    r = detect('sghl ,hkd', 'en', ['fa', 'en'])
    print(f"   {r}\n")

    # تست ۵: متن بی‌معنی
    print("5. 'asdfgh' با layout=en:")
    r = detect('asdfgh', 'en', ['fa', 'en'])
    print(f"   {r}\n")

    # تست ۶: AI (whitelist)
    print("6. 'AI' با layout=fa:")
    r = detect('AI', 'fa', ['fa', 'en'])
    print(f"   {r}\n")