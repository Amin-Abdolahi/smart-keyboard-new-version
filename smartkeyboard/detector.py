# smartkeyboard/detector.py
# تشخیص نیاز به تبدیل layout - با الگوی آماری

from .converter import convert_text, get_conversion_candidates
from .dictionary import get_dictionary
from .languages import get_language_info


# --- آستانه‌ها ---
AUTO_CONVERT_THRESHOLD = 0.70
SUGGEST_THRESHOLD = 0.30
MIN_WORD_LENGTH = 2

# --- وزن‌های امتیازدهی ---
W_WORD = 0.30   # امتیاز کلمه‌ای
W_CHAR = 0.20   # امتیاز حرفی
W_STAT = 0.50   # امتیاز آماری


# --- حروف پرکاربرد فارسی ---
FA_COMMON_CHARS = set("ایردنتسهبمفکعلحوقپجشخزضغذثقظط")

# --- حروف پرکاربرد انگلیسی ---
EN_COMMON_CHARS = set("etaoinshrdlucmfwypvbgkjqxz")


# --- بی‌گرام‌های رایج فارسی ---
FA_BIGRAMS = {
    "ان", "را", "ها", "یه", "می", "ای", "او", "یی", "ست", "که",
    "از", "با", "در", "بر", "تا", "هم", "یا", "ما", "تو", "شو",
    "ین", "ون", "ار", "ور", "رد", "دی", "به", "بی", "پی",
    "اب", "اد", "اس", "اش", "اص", "اط", "اع", "اف", "اق", "ال",
    "ام", "اه", "اند", "انی", "اول", "اید", "این", "بد", "بعد",
    "بعض", "بود", "بین", "پس", "پیش", "توی", "جان", "جای",
    "چند", "چون", "حال", "حتی", "حق", "خوب", "خود", "دار",
    "داشت", "دان", "دست", "دل", "دو", "روز", "روی", "ریز",
    "زیر", "سال", "سری", "شان", "شد", "شده", "شکل", "شور",
    "صور", "طور", "طول", "کار", "کش", "کم", "کن", "کیف",
    "گفت", "گون", "گیر", "مان", "مثل", "مر", "مرد", "مق",
    "مل", "مو", "نار", "نام", "نتر", "ند", "نظر", "نمی",
    "نه", "نور", "نیز", "های", "هر", "هست", "هم", "هیچ",
    "یاب", "یافت", "یک", "یکی",
}

# --- بی‌گرام‌های رایج انگلیسی ---
EN_BIGRAMS = {
    "th", "he", "in", "er", "an", "re", "on", "at", "en",
    "es", "or", "te", "of", "ed", "is", "it", "al", "ar",
    "st", "to", "nt", "ng", "se", "ha", "as", "ou", "io", "le",
}


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
    """نسبت حروف معتبر یه زبان به کل حروف."""
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


def _statistical_score(text, lang):
    """امتیاز آماری بر اساس فراوانی حروف و بی‌گرام‌ها."""
    if not text:
        return 0.0

    if lang == "fa":
        chars = [c for c in text if '\u0600' <= c <= '\u06FF']
        common_chars = FA_COMMON_CHARS
        bigrams = FA_BIGRAMS
    elif lang == "en":
        chars = [c.lower() for c in text if c.isascii() and c.isalpha()]
        common_chars = EN_COMMON_CHARS
        bigrams = EN_BIGRAMS
    else:
        return 0.0

    if not chars:
        return 0.0

    # امتیاز فراوانی حروف
    char_score = sum(1 for c in chars if c in common_chars) / len(chars)

    # امتیاز بی‌گرام
    text_lower = ''.join(chars)
    bigram_count = 0
    total_bigrams = max(len(text_lower) - 1, 1)
    for i in range(len(text_lower) - 1):
        if text_lower[i:i+2] in bigrams:
            bigram_count += 1
    bigram_score = bigram_count / total_bigrams

    # ترکیب: ۵۰٪ حروف + ۵۰٪ بی‌گرام
    return (char_score * 0.5) + (bigram_score * 0.5)


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
    ترکیبی از:
      - امتیاز کلمه‌ای (۳۰٪)
      - امتیاز حرفی (۲۰٪)
      - امتیاز آماری (۵۰٪)
    """
    orig_known, orig_total = _count_known_words(original, dictionary, from_lang)
    conv_known, conv_total = _count_known_words(converted, dictionary, to_lang)

    orig_char_ratio = _char_ratio(original, from_lang)
    conv_char_ratio = _char_ratio(converted, to_lang)

    orig_stat = _statistical_score(original, from_lang)
    conv_stat = _statistical_score(converted, to_lang)

    orig_word_score = orig_known / orig_total if orig_total > 0 else 0.0
    conv_word_score = conv_known / conv_total if conv_total > 0 else 0.0

    orig_score = (
        (orig_word_score * W_WORD)
        + (orig_char_ratio * W_CHAR)
        + (orig_stat * W_STAT)
    )
    conv_score = (
        (conv_word_score * W_WORD)
        + (conv_char_ratio * W_CHAR)
        + (conv_stat * W_STAT)
    )

    if conv_score > orig_score:
        confidence = conv_score - (orig_score * 0.5)
    else:
        confidence = 0.0

    # اگه متن اصلی کاملاً معنی‌داره، تبدیل نکن
    if orig_score >= 0.80:
        confidence = 0.0

    reason = (
        f"orig_word={orig_known}/{orig_total}, conv_word={conv_known}/{conv_total}, "
        f"orig_stat={orig_stat:.2f}, conv_stat={conv_stat:.2f}"
    )
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
        ('h,qhu vndti', 'en', ['fa', 'en']),
        ('asdfgh', 'en', ['fa', 'en']),
        ('AI', 'fa', ['fa', 'en']),
        ('man', 'en', ['fa', 'en']),
        ('o,fd ]i ofv', 'en', ['fa', 'en']),
    ]

    for text, lang, langs in tests:
        r = detect(text, lang, langs)
        print(f"'{text}' (layout={lang}):")
        print(f"   {r}\n")