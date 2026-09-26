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
        "active": ["fa", "en"],
        "primary": "fa",
        "installed": ["fa", "en", "de"],
    },
    "conversion": {
        "auto_convert_threshold": 0.75,
        "suggest_threshold": 0.30,
        "pause_seconds": 1.0,
        "cooldown_seconds": 2.0,
        "auto_replace": True,
        "auto_switch_layout": False,
    },
    "ui": {
        "bubble_enabled": True,
        "sound_enabled": True,
        "bubble_position": "cursor",
        "bubble_timeout": 10,
    },
    "learning": {
        "enabled": True,
        "save_converted_sentences": True,
        "min_word_length": 2,
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
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self._config = self._deep_merge(DEFAULT_CONFIG.copy(), loaded)
            except Exception as e:
                print(f"[Config] خطا در خواندن تنظیمات: {e}")
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self.save()

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Config] خطا در ذخیره تنظیمات: {e}")

    def get(self, *keys, default=None):
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, *keys, value):
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
        self._config = DEFAULT_CONFIG.copy()
        self.save()

    @staticmethod
    def _deep_merge(base, override):
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def __repr__(self):
        return f"Config(active_langs={self.get('languages', 'active')})"


_config_instance = None


def get_config():
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