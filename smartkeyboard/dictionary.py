# smartkeyboard/dictionary.py
# مدیریت دیکشنری چندلایه

import os
import json
from pathlib import Path

from .config import USER_DATA_DIR, USER_WORDS_FILE, IGNORED_WORDS_FILE, LEARNED_WORDS_FILE


# مسیر فایل‌های دیکشنری داخلی
DATA_DIR = Path(__file__).parent / "data"


class Dictionary:
    """مدیریت دیکشنری چندلایه."""

    def __init__(self):
        self.builtin_fa = set()
        self.builtin_en = set()
        self.whitelist = set()
        self.user_words = set()
        self.ignored_words = set()
        self.learned_words = set()
        self.load_all()

    # --- بارگذاری ---

    def _load_lines(self, filepath):
        """خوندن خطوط یه فایل به عنوان set."""
        result = set()
        if not filepath.exists():
            return result
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith("#"):
                        result.add(word)
        except Exception as e:
            print(f"[Dictionary] خطا در خواندن {filepath}: {e}")
        return result

    def _load_json(self, filepath):
        """خوندن یه فایل JSON به عنوان set."""
        if not filepath.exists():
            return set()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return set(data)
                elif isinstance(data, dict) and "words" in data:
                    return set(data["words"])
        except Exception as e:
            print(f"[Dictionary] خطا در خواندن {filepath}: {e}")
        return set()

    def _save_json(self, filepath, words):
        """ذخیره set توی فایل JSON."""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(sorted(list(words)), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Dictionary] خطا در ذخیره {filepath}: {e}")

    def load_all(self):
        """بارگذاری همه لایه‌ها."""
        self.builtin_fa = self._load_lines(DATA_DIR / "fa_words.txt")
        self.builtin_en = self._load_lines(DATA_DIR / "en_words.txt")
        self.whitelist = self._load_lines(DATA_DIR / "whitelist.txt")
        self.user_words = self._load_json(USER_WORDS_FILE)
        self.ignored_words = self._load_json(IGNORED_WORDS_FILE)
        self.learned_words = self._load_json(LEARNED_WORDS_FILE)

    def reload(self):
        """بارگذاری مجدد."""
        self.load_all()

    # --- ذخیره ---

    def save_user_words(self):
        self._save_json(USER_WORDS_FILE, self.user_words)

    def save_ignored_words(self):
        self._save_json(IGNORED_WORDS_FILE, self.ignored_words)

    def save_learned_words(self):
        self._save_json(LEARNED_WORDS_FILE, self.learned_words)

    # --- چک کردن ---

    def is_persian_word(self, word):
        """آیا کلمه یه کلمه فارسی معتبره؟"""
        w = word.strip()
        if not w:
            return False
        if w in self.builtin_fa:
            return True
        if w in self.user_words:
            return True
        if w in self.learned_words:
            return True
        return False

    def is_english_word(self, word):
        """آیا کلمه یه کلمه انگلیسی معتبره؟"""
        w = word.strip().lower()
        if not w:
            return False
        if w in self.builtin_en:
            return True
        if w in self.user_words:
            return True
        if w in self.learned_words:
            return True
        return False

    def is_whitelisted(self, word):
        """آیا کلمه توی لیست سفید (اصطلاحات فنی) هست؟"""
        w = word.strip()
        if not w:
            return False
        if w in self.whitelist:
            return True
        if w.lower() in {x.lower() for x in self.whitelist}:
            return True
        return False

    def is_ignored(self, word):
        """آیا کاربر این کلمه رو رد کرده؟"""
        return word.strip() in self.ignored_words

    def is_known(self, word):
        """آیا کلمه توی هر کدوم از لایه‌ها هست؟"""
        w = word.strip()
        if not w:
            return False
        return (
            self.is_persian_word(w)
            or self.is_english_word(w)
            or self.is_whitelisted(w)
            or self.is_ignored(w)
        )

    # --- اضافه کردن ---

    def add_user_word(self, word):
        """اضافه کردن کلمه به لیست کاربر."""
        w = word.strip()
        if w and w not in self.user_words:
            self.user_words.add(w)
            self.save_user_words()
            return True
        return False

    def add_ignored_word(self, word):
        """اضافه کردن کلمه به لیست رد‌شده‌ها."""
        w = word.strip()
        if w and w not in self.ignored_words:
            self.ignored_words.add(w)
            self.save_ignored_words()
            return True
        return False

    def add_learned_word(self, word):
        """اضافه کردن کلمه به لیست یادگرفته‌ها."""
        w = word.strip()
        if w and w not in self.learned_words:
            self.learned_words.add(w)
            self.save_learned_words()
            return True
        return False

    def add_sentence_words(self, sentence, lang="fa"):
        """اضافه کردن کلمات یه جمله به دیکشنری."""
        words = sentence.strip().split()
        count = 0
        for w in words:
            if len(w) < 2:
                continue
            if lang == "fa" and self.add_learned_word(w):
                count += 1
            elif lang == "en" and self.add_learned_word(w.lower()):
                count += 1
        return count

    # --- آمار ---

    def stats(self):
        """آمار دیکشنری."""
        return {
            "builtin_fa": len(self.builtin_fa),
            "builtin_en": len(self.builtin_en),
            "whitelist": len(self.whitelist),
            "user_words": len(self.user_words),
            "ignored_words": len(self.ignored_words),
            "learned_words": len(self.learned_words),
        }


# --- Singleton ---
_dict_instance = None


def get_dictionary():
    """گرفتن نمونه واحد دیکشنری."""
    global _dict_instance
    if _dict_instance is None:
        _dict_instance = Dictionary()
    return _dict_instance


if __name__ == "__main__":
    d = get_dictionary()
    print("=== آمار دیکشنری ===")
    for k, v in d.stats().items():
        print(f"  {k}: {v}")
    print()
    print("تست چک کردن:")
    print(f"  'سلام' فارسیه؟ {d.is_persian_word('سلام')}")
    print(f"  'hello' انگلیسیه؟ {d.is_english_word('hello')}")
    print(f"  'sghl' شناخته‌شده‌ست؟ {d.is_known('sghl')}")
    print(f"  'AI' توی whitelist هست؟ {d.is_whitelisted('AI')}")