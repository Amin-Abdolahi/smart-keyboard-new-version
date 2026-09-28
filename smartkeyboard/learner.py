# smartkeyboard/learner.py
# یادگیری از کاربر با وزن‌دهی

import json
import time
from datetime import datetime
from pathlib import Path

from .config import USER_DATA_DIR, LOGS_DIR
from .dictionary import get_dictionary, WEIGHT_CHANGES


CONVERSIONS_LOG = USER_DATA_DIR / "conversions.json"

# آستانه‌ها
LEARN_THRESHOLD = 5.0     # وزن لازم برای ورود به learned_words
FORGET_THRESHOLD = 1.0    # وزن لازم برای حذف از learned_words


class Learner:
    """مدیریت یادگیری از کاربر."""

    def __init__(self):
        self.dictionary = get_dictionary()
        self.conversions = []
        self._load_conversions()

    def _load_conversions(self):
        if CONVERSIONS_LOG.exists():
            try:
                with open(CONVERSIONS_LOG, "r", encoding="utf-8") as f:
                    self.conversions = json.load(f)
            except Exception as e:
                print(f"[Learner] خطا در خواندن لاگ: {e}")
                self.conversions = []

    def _save_conversions(self):
        try:
            CONVERSIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(CONVERSIONS_LOG, "w", encoding="utf-8") as f:
                json.dump(self.conversions[-500:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Learner] خطا در ذخیره لاگ: {e}")

    # --- رویدادها ---

    def on_accept(self, original, suggested, from_lang, to_lang, confidence):
        """
        کاربر پیشنهاد رو قبول کرد.
        - کلمه پیشنهادی وزن میگیره.
        - کلمه اصلی وزن از دست میده.
        """
        # کلمه پیشنهادی وزن میگیره
        for word in suggested.split():
            word = word.strip()
            if len(word) >= 2:
                self._add_weight(word, WEIGHT_CHANGES["accept"], to_lang or "fa")

        # کلمه اصلی وزن از دست میده
        for word in original.split():
            word = word.strip()
            if len(word) >= 2:
                self._add_weight(word, WEIGHT_CHANGES["reject"], from_lang or "en")

        self._log(original, suggested, from_lang, to_lang, confidence, "accepted")

    def on_reject(self, original, suggested, from_lang, to_lang, confidence):
        """
        کاربر پیشنهاد رو رد کرد.
        - کلمه اصلی وزن میگیره (چون کاربر گفت درسته).
        - کلمه پیشنهادی وزن از دست میده.
        """
        # کلمه اصلی وزن میگیره
        for word in original.split():
            word = word.strip()
            if len(word) >= 2:
                self._add_weight(word, WEIGHT_CHANGES["accept"], from_lang or "en")

        # کلمه پیشنهادی وزن از دست میده
        for word in suggested.split():
            word = word.strip()
            if len(word) >= 2:
                self._add_weight(word, WEIGHT_CHANGES["reject"], to_lang or "fa")

        # اگه وزن کلمه اصلی به صفر رسید، به ignored اضافه کن
        for word in original.split():
            word = word.strip()
            if len(word) >= 2:
                weight = self.dictionary.get_word_weight(word, from_lang or "en")
                if weight < FORGET_THRESHOLD:
                    self.dictionary.add_ignored_word(word)

        self._log(original, suggested, from_lang, to_lang, confidence, "rejected")

    def on_learn(self, word):
        """
        کاربر یه کلمه جدید یاد داد (دستی).
        وزن زیاد میگیره و فوراً به learned اضافه میشه.
        """
        for w in word.split():
            w = w.strip()
            if len(w) >= 2:
                self._add_weight(w, WEIGHT_CHANGES["learn"], "fa")
                # فوراً به learned اضافه کن
                self.dictionary.add_learned_word(w)
        self._log(word, word, "", "", 1.0, "learned")

    def on_background_learn(self, text, lang="fa"):
        """
        یادگیری پس‌زمینه.
        وزن +1 اضافه میشه. اگه وزن به آستانه رسید، به learned اضافه میشه.
        """
        words_added = []
        for word in text.split():
            word = word.strip()
            if len(word) < 2:
                continue

            # اگه کلمه توی دیکشنری پایه هست، نادیده بگیر
            if self.dictionary.is_persian_word(word) or self.dictionary.is_english_word(word):
                continue

            # اگه کلمه توی ignored هست، نادیده بگیر
            if self.dictionary.is_ignored(word):
                continue

            # وزن +1
            new_weight = self._add_weight(word, WEIGHT_CHANGES["background_learn"], lang)

            # اگه وزن به آستانه رسید، به learned اضافه کن
            if new_weight >= LEARN_THRESHOLD:
                if self.dictionary.add_learned_word(word):
                    words_added.append(word)

        if words_added:
            info = f"یادگیری پس‌زمینه: {len(words_added)} کلمه به دیکشنری اضافه شد: {words_added[:5]}"
            from .logger import info as log_info
            log_info(info)

    def on_wrong(self, text, lang="fa"):
        """
        کاربر اشتباه تایپ کرده.
        وزن منفی میگیره.
        """
        for word in text.split():
            word = word.strip()
            if len(word) >= 2:
                new_weight = self._add_weight(word, WEIGHT_CHANGES["wrong"], lang)

                # اگه وزن به صفر رسید، از learned حذف کن
                if new_weight < FORGET_THRESHOLD:
                    self.dictionary.remove_learned_word(word)

    def _add_weight(self, word, delta, lang="fa"):
        """
        اضافه کردن وزن به یه کلمه.
        اگه وزن به آستانه رسید، به learned اضافه کن.
        """
        new_weight = self.dictionary.update_word_weight(word, delta, lang)

        # اگه وزن به آستانه رسید، به learned اضافه کن
        if new_weight >= LEARN_THRESHOLD:
            self.dictionary.add_learned_word(word)
        # اگه وزن به صفر رسید، از learned حذف کن
        elif new_weight < FORGET_THRESHOLD:
            self.dictionary.remove_learned_word(word)

        return new_weight

    def _log(self, original, suggested, from_lang, to_lang, confidence, action):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "original": original,
            "suggested": suggested,
            "from": from_lang,
            "to": to_lang,
            "confidence": confidence,
            "action": action,
        }
        self.conversions.append(entry)
        self._save_conversions()

    # --- آمار ---

    def get_stats(self):
        accepted = sum(1 for c in self.conversions if c["action"] == "accepted")
        rejected = sum(1 for c in self.conversions if c["action"] == "rejected")
        learned = sum(1 for c in self.conversions if c["action"] == "learned")
        return {
            "total": len(self.conversions),
            "accepted": accepted,
            "rejected": rejected,
            "learned": learned,
        }

    def get_recent(self, n=10):
        return self.conversions[-n:]

    def clear_log(self):
        self.conversions = []
        self._save_conversions()


_learner_instance = None


def get_learner():
    global _learner_instance
    if _learner_instance is None:
        _learner_instance = Learner()
    return _learner_instance


if __name__ == "__main__":
    from .logger import setup_logger
    setup_logger()

    print("=== تست learner با وزن‌دهی و آستانه ===\n")

    learner = get_learner()
    d = get_dictionary()

    print(f"آستانه یادگیری: {LEARN_THRESHOLD}")
    print(f"آستانه فراموشی: {FORGET_THRESHOLD}\n")

    # شبیه‌سازی: ۵ بار تایپ 'پشمام'
    print("شبیه‌سازی ۵ بار تایپ 'پشمام':")
    for i in range(5):
        learner.on_background_learn('پشمام', 'fa')
        weight = d.get_word_weight('پشمام')
        in_learned = 'پشمام' in d.learned_words
        print(f"  بار {i+1}: وزن={weight:.1f}, توی learned={in_learned}")

    print()
    print("شبیه‌سازی رد کردن 'sghl':")
    for i in range(3):
        learner.on_reject('sghl', 'سلام', 'en', 'fa', 0.5)
        weight = d.get_word_weight('sghl')
        in_learned = 'sghl' in d.learned_words
        print(f"  بار {i+1}: وزن={weight:.1f}, توی learned={in_learned}")

    print()
    print("=== پرکاربردترین کلمات ===")
    for word, weight in d.get_top_words(10):
        print(f"  {word}: {weight:.1f}")