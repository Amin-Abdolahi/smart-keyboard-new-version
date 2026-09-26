# smartkeyboard/config.py
# مدیریت تنظیمات برنامه

import os
import json
import platform
from pathlib import Path


# --- مسیرها ---
if platform.system() == "Windows":
    APP_DATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / "SmartKeyboard"
else:
    APP_DATA_DIR = Path.home() / ".smartkeyboard"

USER_DATA_DIR = APP_DATA_DIR / "user_data"
LOGS_DIR = USER_DATA_DIR / "logs"

CONFIG_FILE = USER_DATA_DIR / "config.json"
USER_WORDS_FILE = USER_DATA_DIR / "user_words.json"
IGNORED_WORDS_FILE = USER_DATA_DIR / "ignored_words.json"
LEARNED_WORDS_FILE = USER_DATA_DIR / "learned_words.json"


# --- تنظیمات پیش‌فرض ---
DEFAULT_CONFIG = {
    "version": "2.0.0",
    "languages": {
        "active": ["fa", "en"],           # زبان‌های فعال
        "primary": "fa",                   # زبان اصلی کاربر
        "installed": ["fa", "en", "de"],   # زبان‌های نصب‌شده
    },
    "conversion": {
        "auto_convert_threshold": 0.9,     # آستانه تبدیل خودکار
        "suggest_threshold": 0.5,          # آستانه نمایش پیشنهاد
        "pause_seconds": 1.0,              # ثانیه توقف قبل از بررسی
        "cooldown_seconds": 2.0,           # فاصله بین پیشنهادها
        "auto_replace": True,              # جایگزینی خودکار در اطمینان بالا
    },
    "ui": {
        "bubble_enabled": True,            # نمایش حباب شناور
        "sound_enabled": True,             # صدای دینگ
        "bubble_position": "cursor",       # cursor | bottom-right | top-right
        "bubble_timeout": 10,              # ثانیه تا بسته شدن خودکار
    },
    "learning": {
        "enabled": True,                   # یادگیری از کاربر
        "save_converted_sentences": True,  # ذخیره جمله‌های تبدیل‌شده
        "min_word_length": 2,              # حداقل طول کلمه برای یادگیری
    },
    "dictionary": {
        "use_builtin_fa": True,
        "use_builtin_en": True,
        "use_builtin_de": False,
        "use_user_words": True,
        "use_learned_words": True,
    },
}


class Config:
    """مدیریت تنظیمات برنامه."""

    def __init__(self):
        self._config = {}
        self._ensure_dirs()
        self.load()

    def _ensure_dirs(self):
        """ساخت پوشه‌های لازم اگه وجود نداشته باشن."""
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

    def load(self):
        """بارگذاری تنظیمات از فایل."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                # ادغام با تنظیمات پیش‌فرض (برای اضافه شدن کلیدهای جدید)
                self._config = self._deep_merge(DEFAULT_CONFIG.copy(), loaded)
            except Exception as e:
                print(f"[Config] خطا در خواندن تنظیمات: {e}")
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self.save()

    def save(self):
        """ذخیره تنظیمات توی فایل."""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Config] خطا در ذخیره تنظیمات: {e}")

    def get(self, *keys, default=None):
        """گرفتن یه مقدار با مسیر کلیدها."""
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, *keys, value):
        """تنظیم یه مقدار با مسیر کلیدها."""
        if not keys:
            return
        target = self._config
        for key in keys[:-1]:
            if key not in target or not isinstance(target[key], dict):
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value
        self.save()

    def reset(self):
        """برگرداندن تنظیمات به حالت پیش‌فرض."""
        self._config = DEFAULT_CONFIG.copy()
        self.save()

    @staticmethod
    def _deep_merge(base, override):
        """ادغام عمیق دو دیکشنری."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def __repr__(self):
        return f"Config(active_langs={self.get('languages', 'active')})"


# --- Singleton ---
_config_instance = None


def get_config():
    """گرفتن نمونه واحد تنظیمات."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


if __name__ == "__main__":
    cfg = get_config()
    print(f"مسیر تنظیمات: {CONFIG_FILE}")
    print(f"زبان‌های فعال: {cfg.get('languages', 'active')}")
    print(f"زبان اصلی: {cfg.get('languages', 'primary')}")
    print(f"آستانه تبدیل خودکار: {cfg.get('conversion', 'auto_convert_threshold')}")