# smartkeyboard/dictionary.py
# مدیریت دیکشنری چندلایه با وزن‌دهی

import os
import json
from pathlib import Path

from .config import USER_DATA_DIR, USER_WORDS_FILE, IGNORED_WORDS_FILE, LEARNED_WORDS_FILE


DATA_DIR = Path(__file__).parent / "data"
WORD_WEIGHTS_FILE = USER_DATA_DIR / "word_weights.json"


DEFAULT_WEIGHTS = {
    "builtin": 10.0,
    "learned": 5.0,
    "user": 3.0,
    "background": 0.0,
    "unknown": 0.0,
}

WEIGHT_CHANGES = {
    "accept": 2.0,
    "reject": -3.0,
    "learn": 5.0,
    "background_learn": 1.0,
    "wrong": -2.0,
}

WEIGHT_THRESHOLD = 0.5


class Dictionary:
    """مدیریت دیکشنری چندلایه با وزن‌دهی."""

    def __init__(self):
        self.builtin_fa = set()
        self.builtin_en = set()
        self.whitelist = set()
        self.user_words = set()
        self.ignored_words = set()
        self.learned_words = set()
        self.word_weights = {}
        self.load_all()

    def _load_lines(self, filepath):
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
        if not filepath.exists():
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Dictionary] خطا در خواندن {filepath}: {e}")
            return None

    def _load_json_set(self, filepath):
        data = self._load_json(filepath)
        if data is None:
            return set()
        if isinstance(data, list):
            return set(data)
        elif isinstance(data, dict) and "words" in data:
            return set(data["words"])
        return set()

    def _save_json(self, filepath, data):
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Dictionary] خطا در ذخیره {filepath}: {e}")

    def load_all(self):
        self.builtin_fa = self._load_lines(DATA_DIR / "fa_words.txt")
        self.builtin_en = self._load_lines(DATA_DIR / "en_words.txt")
        self.whitelist = self._load_lines(DATA_DIR / "whitelist.txt")
        self.user_words = self._load_json_set(USER_WORDS_FILE)
        self.ignored_words = self._load_json_set(IGNORED_WORDS_FILE)
        self.learned_words = self._load_json_set(LEARNED_WORDS_FILE)

        weights = self._load_json(WORD_WEIGHTS_FILE)
        if isinstance(weights, dict):
            self.word_weights = weights
        else:
            self.word_weights = {}

    def reload(self):
        self.load_all()

    def save_user_words(self):
        self._save_json(USER_WORDS_FILE, sorted(self.user_words))

    def save_ignored_words(self):
        self._save_json(IGNORED_WORDS_FILE, sorted(self.ignored_words))

    def save_learned_words(self):
        self._save_json(LEARNED_WORDS_FILE, sorted(self.learned_words))

    def save_word_weights(self):
        self._save_json(WORD_WEIGHTS_FILE, self.word_weights)

    def is_persian_word(self, word):
        w = word.strip()
        if not w:
            return False
        return w in self.builtin_fa or w in self.user_words or w in self.learned_words

    def is_english_word(self, word):
        w = word.strip().lower()
        if not w:
            return False
        return w in self.builtin_en or w in self.user_words or w in self.learned_words

    def is_whitelisted(self, word):
        w = word.strip()
        if not w:
            return False
        return w in self.whitelist or w.lower() in {x.lower() for x in self.whitelist}

    def is_ignored(self, word):
        return word.strip() in self.ignored_words

    def is_known(self, word):
        w = word.strip()
        if not w:
            return False
        return (
            self.is_persian_word(w)
            or self.is_english_word(w)
            or self.is_whitelisted(w)
            or self.is_ignored(w)
        )

    def get_word_weight(self, word, lang="fa"):
        if not word:
            return DEFAULT_WEIGHTS["unknown"]

        w = word.strip().lower() if lang == "en" else word.strip()

        if w in self.word_weights:
            return float(self.word_weights[w])

        if w in self.builtin_fa or w in self.builtin_en:
            return DEFAULT_WEIGHTS["builtin"]
        if w in self.learned_words:
            return DEFAULT_WEIGHTS["learned"]
        if w in self.user_words:
            return DEFAULT_WEIGHTS["user"]

        return DEFAULT_WEIGHTS["unknown"]

    def update_word_weight(self, word, delta, lang="fa"):
        if not word:
            return 0.0

        w = word.strip().lower() if lang == "en" else word.strip()

        current = self.word_weights.get(w)
        if current is None:
            current = self.get_word_weight(w, lang)

        new_weight = max(0.0, float(current) + delta)
        self.word_weights[w] = new_weight
        self.save_word_weights()
        return new_weight

    def add_user_word(self, word):
        w = word.strip()
        if w and w not in self.user_words:
            self.user_words.add(w)
            self.save_user_words()
            return True
        return False

    def add_ignored_word(self, word):
        w = word.strip()
        if w and w not in self.ignored_words:
            self.ignored_words.add(w)
            self.save_ignored_words()
            return True
        return False

    def add_learned_word(self, word):
        w = word.strip()
        if w and w not in self.learned_words:
            self.learned_words.add(w)
            self.save_learned_words()
            return True
        return False

    def remove_learned_word(self, word):
        w = word.strip()
        if w in self.learned_words:
            self.learned_words.discard(w)
            self.save_learned_words()
            return True
        return False

    def add_sentence_words(self, sentence, lang="fa"):
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

    def stats(self):
        return {
            "builtin_fa": len(self.builtin_fa),
            "builtin_en": len(self.builtin_en),
            "whitelist": len(self.whitelist),
            "user_words": len(self.user_words),
            "ignored_words": len(self.ignored_words),
            "learned_words": len(self.learned_words),
            "word_weights": len(self.word_weights),
        }

    def get_top_words(self, n=20):
        sorted_words = sorted(
            self.word_weights.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_words[:n]


_dict_instance = None


def get_dictionary():
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
    print("تست وزن‌دهی:")
    print(f"  وزن 'سلام': {d.get_word_weight('سلام')}")
    print(f"  وزن 'پشمام': {d.get_word_weight('پشمام')}")
    print(f"  وزن 'sghl': {d.get_word_weight('sghl')}")