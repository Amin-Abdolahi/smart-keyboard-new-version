# smartkeyboard/learner.py
# یادگیری از کاربر و مدیریت لاگ تبدیل‌ها

import json
import time
from datetime import datetime
from pathlib import Path

from .config import USER_DATA_DIR, LOGS_DIR
from .dictionary import get_dictionary


# فایل لاگ تبدیل‌ها
CONVERSIONS_LOG = USER_DATA_DIR / "conversions.json"


class Learner:
    """مدیریت یادگیری از کاربر."""

    def __init__(self):
        self.dictionary = get_dictionary()
        self.conversions = []
        self._load_conversions()

    def _load_conversions(self):
        """بارگذاری لاگ تبدیل‌ها."""
        if CONVERSIONS_LOG.exists():
            try:
                with open(CONVERSIONS_LOG, "r", encoding="utf-8") as f:
                    self.conversions = json.load(f)
            except Exception as e:
                print(f"[Learner] خطا در خواندن لاگ: {e}")
                self.conversions = []

    def _save_conversions(self):
        """ذخیره لاگ تبدیل‌ها."""
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
        - کلمه پیشنهادی به دیکشنری اضافه میشه.
        - لاگ ثبت میشه.
        """
        # اضافه کردن کلمه پیشنهادی
        self.dictionary.add_learned_word(suggested)

        # اگه جمله بود، کلماتش رو هم اضافه کن
        if ' ' in suggested:
            self.dictionary.add_sentence_words(suggested, lang=to_lang)

        # ثبت لاگ
        self._log(original, suggested, from_lang, to_lang, confidence, "accepted")

        # ذخیره
        self.dictionary.save_learned_words()

    def on_reject(self, original, suggested, from_lang, to_lang, confidence):
        """
        کاربر پیشنهاد رو رد کرد.
        - کلمه اصلی به لیست ignored اضافه میشه.
        """
        self.dictionary.add_ignored_word(original)
        self._log(original, suggested, from_lang, to_lang, confidence, "rejected")

    def on_learn(self, word):
        """
        کاربر یه کلمه جدید یاد داد.
        """
        self.dictionary.add_learned_word(word)
        self._log(word, word, "", "", 1.0, "learned")

    def _log(self, original, suggested, from_lang, to_lang, confidence, action):
        """ثبت یه رویداد توی لاگ."""
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
        """آمار یادگیری."""
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
        """آخرین n رویداد."""
        return self.conversions[-n:]

    def clear_log(self):
        """پاک کردن لاگ."""
        self.conversions = []
        self._save_conversions()


# --- Singleton ---
_learner_instance = None


def get_learner():
    """گرفتن نمونه واحد Learner."""
    global _learner_instance
    if _learner_instance is None:
        _learner_instance = Learner()
    return _learner_instance


if __name__ == "__main__":
    print("=== تست learner ===\n")

    learner = get_learner()

    # شبیه‌سازی رویدادها
    print("1. کاربر پیشنهاد 'سلام' رو قبول میکنه:")
    learner.on_accept('sghl', 'سلام', 'en', 'fa', 0.95)
    print("   انجام شد.\n")

    print("2. کاربر پیشنهاد 'hello' رو رد میکنه:")
    learner.on_reject('hello', 'اثممخ', 'en', 'fa', 0.6)
    print("   انجام شد.\n")

    print("3. کاربر کلمه 'پشمام' رو یاد میده:")
    learner.on_learn('پشمام')
    print("   انجام شد.\n")

    # آمار
    print("=== آمار ===")
    stats = learner.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n=== آخرین رویدادها ===")
    for entry in learner.get_recent(5):
        print(f"  [{entry['action']}] '{entry['original']}' -> '{entry['suggested']}'")

    # بررسی دیکشنری
    d = get_dictionary()
    print("\n=== بررسی دیکشنری ===")
    print(f"  'سلام' توی learned؟ {'سلام' in d.learned_words}")
    print(f"  'hello' توی ignored؟ {'hello' in d.ignored_words}")
    print(f"  'پشمام' توی learned؟ {'پشمام' in d.learned_words}")