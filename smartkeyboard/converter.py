# smartkeyboard/converter.py
# تبدیل متن بین layoutها با در نظر گرفتن context

from .languages import (
    convert_en_to_fa,
    convert_fa_to_en,
    convert_en_to_de,
    convert_de_to_en,
    get_language_info,
)


def detect_case(text):
    """
    تشخیص حالت حروف متن.
    خروجی: 'lower' | 'upper' | 'title' | 'mixed'
    """
    if not text:
        return 'lower'
    if text.islower():
        return 'lower'
    if text.isupper():
        return 'upper'
    if text.istitle():
        return 'title'
    return 'mixed'


def apply_case(text, case):
    """اعمال حالت حروف روی متن."""
    if case == 'lower':
        return text.lower()
    elif case == 'upper':
        return text.upper()
    elif case == 'title':
        return text.title()
    return text


def convert_text(text, from_lang, to_lang, preserve_case=True):
    """
    تبدیل متن از یه زبان به زبان دیگه.
    
    Args:
        text: متن ورودی
        from_lang: کد زبان مبدأ ('fa', 'en', 'de')
        to_lang: کد زبان مقصد ('fa', 'en', 'de')
        preserve_case: حفظ حالت حروف بزرگ/کوچک
    
    Returns:
        متن تبدیل‌شده
    """
    if not text:
        return text
    if from_lang == to_lang:
        return text

    # تشخیص حالت حروف قبل از تبدیل
    original_case = detect_case(text) if preserve_case else 'lower'

    # تبدیل بر اساس جفت زبان‌ها
    if from_lang == "en" and to_lang == "fa":
        result = convert_en_to_fa(text)
    elif from_lang == "fa" and to_lang == "en":
        result = convert_fa_to_en(text)
    elif from_lang == "en" and to_lang == "de":
        result = convert_en_to_de(text)
    elif from_lang == "de" and to_lang == "en":
        result = convert_de_to_en(text)
    else:
        # جفت‌های پشتیبانی‌نشده: از انگلیسی به عنوان واسطه استفاده کن
        result = text
        if from_lang != "en":
            result = convert_to_en(text, from_lang)
        if to_lang != "en":
            result = convert_from_en(result, to_lang)

    # اعمال حالت حروف
    if preserve_case and to_lang == "en":
        result = apply_case(result, original_case)

    return result


def convert_to_en(text, from_lang):
    """تبدیل از هر زبانی به انگلیسی."""
    if from_lang == "fa":
        return convert_fa_to_en(text)
    elif from_lang == "de":
        return convert_de_to_en(text)
    return text


def convert_from_en(text, to_lang):
    """تبدیل از انگلیسی به هر زبانی."""
    if to_lang == "fa":
        return convert_en_to_fa(text)
    elif to_lang == "de":
        return convert_en_to_de(text)
    return text


def get_conversion_candidates(text, current_lang, active_langs):
    """
    تولید همه تبدیل‌های ممکن برای یه متن.
    
    Args:
        text: متن ورودی
        current_lang: زبان فعلی layout
        active_langs: لیست زبان‌های فعال کاربر
    
    Returns:
        لیست دیکشنری‌هایی با کلیدهای:
          - 'text': متن تبدیل‌شده
          - 'from': زبان مبدأ
          - 'to': زبان مقصد
    """
    candidates = []
    for target_lang in active_langs:
        if target_lang == current_lang:
            continue
        converted = convert_text(text, current_lang, target_lang)
        if converted != text:
            candidates.append({
                'text': converted,
                'from': current_lang,
                'to': target_lang,
            })
    return candidates


if __name__ == "__main__":
    # تست
    print("=== تست converter ===\n")

    # تست ۱: تبدیل ساده
    print("1. sghl (en) -> fa:")
    print(f"   {convert_text('sghl', 'en', 'fa')}")

    print("\n2. سلام (fa) -> en:")
    print(f"   {convert_text('سلام', 'fa', 'en')}")

    print("\n3. Hello (en) -> fa با حفظ حالت:")
    print(f"   {convert_text('Hello', 'en', 'fa')}")

    print("\n4. HELLO (en) -> fa با حفظ حالت:")
    print(f"   {convert_text('HELLO', 'en', 'fa')}")

    # تست ۲: تبدیل‌های ممکن
    print("\n5. تبدیل‌های ممکن برای 'sghl' (layout=en):")
    candidates = get_conversion_candidates('sghl', 'en', ['fa', 'en'])
    for c in candidates:
        print(f"   {c['from']} -> {c['to']}: {c['text']}")

    # تست ۳: تشخیص case
    print("\n6. تشخیص case:")
    for t in ['hello', 'HELLO', 'Hello', 'HeLLo']:
        print(f"   '{t}' -> {detect_case(t)}")