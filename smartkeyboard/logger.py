# smartkeyboard/logger.py
# سیستم لاگ حرفه‌ای

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

from .config import USER_DATA_DIR


# مسیر فایل لاگ
LOG_DIR = USER_DATA_DIR / "logs"
LOG_FILE = LOG_DIR / "smartkeyboard.log"

# حداکثر حجم هر فایل لاگ (۵ مگابایت)
MAX_LOG_SIZE = 5 * 1024 * 1024
# تعداد فایل‌های پشتیبان
BACKUP_COUNT = 3


def _ensure_log_dir():
    """ساخت پوشه لاگ اگه وجود نداشت."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logger(name="smartkeyboard", level=logging.DEBUG, console=True):
    """
    ساخت و تنظیم logger.
    
    Args:
        name: اسم logger
        level: سطح لاگ (DEBUG, INFO, WARNING, ERROR)
        console: نمایش توی کنسول
    
    Returns:
        logger
    """
    _ensure_log_dir()
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # اگه قبلاً تنظیم شده، دوباره تنظیم نکن
    if logger.handlers:
        return logger
    
    # فرمت لاگ
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=date_fmt)
    
    # --- فایل handler با rotation ---
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"[Logger] خطا در ساخت file handler: {e}")
    
    # --- کنسول handler ---
    if console:
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        except Exception:
            pass
    
    return logger


# --- Singleton ---
_logger = None


def get_logger():
    """گرفتن logger اصلی."""
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger


# --- توابع راحتی ---

def debug(msg, *args, **kwargs):
    get_logger().debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    get_logger().info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    get_logger().warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    get_logger().error(msg, *args, **kwargs)


def exception(msg, *args, **kwargs):
    get_logger().exception(msg, *args, **kwargs)


def log_exception(exc, context=""):
    """ثبت یه exception با context."""
    get_logger().exception(f"[{context}] {exc}")


def get_log_file_path():
    """مسیر فایل لاگ."""
    return str(LOG_FILE)


def get_recent_logs(n=100):
    """خوندن آخرین n خط از لاگ."""
    if not LOG_FILE.exists():
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines[-n:]
    except Exception as e:
        return [f"خطا در خواندن لاگ: {e}"]


def clear_logs():
    """پاک کردن همه لاگ‌ها."""
    try:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
        for backup in LOG_DIR.glob("smartkeyboard.log.*"):
            backup.unlink()
        return True
    except Exception as e:
        print(f"[Logger] خطا در پاک کردن لاگ: {e}")
        return False


if __name__ == "__main__":
    print("=== تست logger ===\n")
    
    logger = get_logger()
    
    debug("این یه پیام debug هست")
    info("این یه پیام info هست")
    warning("این یه پیام warning هست")
    error("این یه پیام error هست")
    
    try:
        x = 1 / 0
    except Exception as e:
        log_exception(e, context="تست تقسیم بر صفر")
    
    print(f"\nفایل لاگ: {get_log_file_path()}")
    print("\nآخرین ۵ خط لاگ:")
    for line in get_recent_logs(5):
        print(f"  {line.rstrip()}")