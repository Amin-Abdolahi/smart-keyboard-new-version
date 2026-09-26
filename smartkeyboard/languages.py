# smartkeyboard/languages.py
# مدیریت زبان‌ها و layoutهای کیبورد

import platform


# --- تعریف زبان‌ها ---
LANGUAGES = {
    "fa": {
        "name": "فارسی",
        "native_name": "فارسی",
        "code": "fa",
        "lang_id": 0x0429,  # Windows language ID
        "rtl": True,
    },
    "en": {
        "name": "English",
        "native_name": "English",
        "code": "en",
        "lang_id": 0x0409,
        "rtl": False,
    },
    "de": {
        "name": "German",
        "native_name": "Deutsch",
        "code": "de",
        "lang_id": 0x0407,
        "rtl": False,
    },
    "ar": {
        "name": "Arabic",
        "native_name": "العربية",
        "code": "ar",
        "lang_id": 0x0401,
        "rtl": True,
    },
}


# --- نقشه تبدیل: انگلیسی ↔ فارسی ---
# بر اساس layout استاندارد کیبورد فارسی
EN_TO_FA = {
    'q': 'ض', 'w': 'ص', 'e': 'ث', 'r': 'ق', 't': 'ف', 'y': 'غ', 'u': 'ع',
    'i': 'ه', 'o': 'خ', 'p': 'ح', '[': 'ج', ']': 'چ', '\\': '\\',
    'a': 'ش', 's': 'س', 'd': 'ی', 'f': 'ب', 'g': 'ل', 'h': 'ا', 'j': 'ت',
    'k': 'ن', 'l': 'م', ';': 'ک', "'": 'گ',
    'z': 'ظ', 'x': 'ط', 'c': 'ز', 'v': 'ر', 'b': 'ذ', 'n': 'د', 'm': 'پ',
    ',': 'و', '.': '.', '/': '/',
    '`': '`', '~': '~',
    '1': '۱', '2': '۲', '3': '۳', '4': '۴', '5': '۵',
    '6': '۶', '7': '۷', '8': '۸', '9': '۹', '0': '۰',
    '-': '-', '=': '=',
    'Q': 'ض', 'W': 'ص', 'E': 'ث', 'R': 'ق', 'T': 'ف', 'Y': 'غ', 'U': 'ع',
    'I': 'ه', 'O': 'خ', 'P': 'ح', '{': 'ج', '}': 'چ', '|': '|',
    'A': 'ش', 'S': 'س', 'D': 'ی', 'F': 'ب', 'G': 'ل', 'H': 'ا', 'J': 'ت',
    'K': 'ن', 'L': 'م', ':': 'ک', '"': 'گ',
    'Z': 'ظ', 'X': 'ط', 'C': 'ز', 'V': 'ر', 'B': 'ذ', 'N': 'د', 'M': 'پ',
    '<': 'و', '>': '.', '?': '/',
}

FA_TO_EN = {v: k for k, v in EN_TO_FA.items() if len(v) == 1}


# --- نقشه تبدیل: انگلیسی ↔ آلمانی ---
# فقط حروف خاص آلمانی (بقیه مثل انگلیسی هستن)
EN_TO_DE_SPECIAL = {
    '[': 'ü', ']': '+', ';': 'ö', "'": 'ä',
    '{': 'Ü', '}': '*', ':': 'Ö', '"': 'Ä',
    '-': 'ß', '_': '?',
}

DE_TO_EN_SPECIAL = {v: k for k, v in EN_TO_DE_SPECIAL.items()}


# --- توابع ---

def get_language_info(lang_code):
    """گرفتن اطلاعات یه زبان."""
    return LANGUAGES.get(lang_code)


def get_lang_id(lang_code):
    """گرفتن Windows language ID برای یه زبان."""
    info = LANGUAGES.get(lang_code)
    return info["lang_id"] if info else None


def get_lang_from_id(lang_id):
    """تشخیص کد زبان از روی Windows language ID."""
    for code, info in LANGUAGES.items():
        if info["lang_id"] == lang_id:
            return code
    return None


def convert_en_to_fa(text):
    """تبدیل حروف انگلیسی به فارسی."""
    return ''.join(EN_TO_FA.get(c, c) for c in text)


def convert_fa_to_en(text):
    """تبدیل حروف فارسی به انگلیسی."""
    return ''.join(FA_TO_EN.get(c, c) for c in text)


def convert_en_to_de(text):
    """تبدیل حروف انگلیسی به آلمانی (فقط حروف خاص)."""
    return ''.join(EN_TO_DE_SPECIAL.get(c, c) for c in text)


def convert_de_to_en(text):
    """تبدیل حروف آلمانی به انگلیسی."""
    return ''.join(DE_TO_EN_SPECIAL.get(c, c) for c in text)


def convert(text, from_lang, to_lang):
    """
    تبدیل متن از یه زبان به زبان دیگه.
    فعلاً فقط جفت‌های fa↔en و en↔de پشتیبانی میشن.
    """
    if from_lang == to_lang:
        return text

    if from_lang == "en" and to_lang == "fa":
        return convert_en_to_fa(text)
    elif from_lang == "fa" and to_lang == "en":
        return convert_fa_to_en(text)
    elif from_lang == "en" and to_lang == "de":
        return convert_en_to_de(text)
    elif from_lang == "de" and to_lang == "en":
        return convert_de_to_en(text)
    else:
        return text


def get_available_languages():
    """لیست زبان‌های موجود."""
    return list(LANGUAGES.keys())


def get_rtl_languages():
    """لیست زبان‌های راست‌به‌چپ."""
    return [code for code, info in LANGUAGES.items() if info["rtl"]]


if __name__ == "__main__":
    # تست
    print("زبان‌های موجود:", get_available_languages())
    print("زبان‌های RTL:", get_rtl_languages())
    print()
    print("تست تبدیل EN→FA:")
    print(f"  sghl → {convert_en_to_fa('sghl')}")
    print(f"  hello → {convert_en_to_fa('hello')}")
    print()
    print("تست تبدیل FA→EN:")
    print(f"  سلام → {convert_fa_to_en('سلام')}")
    print()
    print("تست تبدیل EN→DE:")
    test_input = "[ ] ; '"
    print(f"  {test_input} → {convert_en_to_de(test_input)}")