# main.py
# Smart Keyboard v2 - نقطه ورود برنامه

import os
import sys
import time
import threading
import platform

# اضافه کردن مسیر پروژه به sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smartkeyboard.config import get_config
from smartkeyboard.dictionary import get_dictionary
from smartkeyboard.detector import detect
from smartkeyboard.learner import get_learner
from smartkeyboard.converter import convert_text
from smartkeyboard.popup import PopupBubble, play_ding
from smartkeyboard.tray import TrayIcon, COLOR_ACTIVE, COLOR_IDLE, COLOR_SUGGEST


# --- Windows-specific imports ---
PYWIN_AVAILABLE = False
if platform.system() == "Windows":
    try:
        import win32gui
        import win32api
        import win32process
        PYWIN_AVAILABLE = True
    except ImportError as e:
        print(f"[Warning] pywin32 پیدا نشد: {e}")


# --- نقشه scan code به حرف انگلیسی ---
SCANCODE_TO_CHAR = {
    16: 'q', 17: 'w', 18: 'e', 19: 'r', 20: 't', 21: 'y', 22: 'u', 23: 'i', 24: 'o', 25: 'p',
    30: 'a', 31: 's', 32: 'd', 33: 'f', 34: 'g', 35: 'h', 36: 'j', 37: 'k', 38: 'l',
    44: 'z', 45: 'x', 46: 'c', 47: 'v', 48: 'b', 49: 'n', 50: 'm',
    2: '1', 3: '2', 4: '3', 5: '4', 6: '5', 7: '6', 8: '7', 9: '8', 10: '9', 11: '0',
}

# --- نقشه scan code علائم نگارشی ---
SCANCODE_PUNCTUATION = {
    26: '[', 27: ']', 43: '\\',
    39: ';', 40: "'",
    51: ',', 52: '.', 53: '/',
    12: '-', 13: '=',
    41: '`',
}

# زمان انتظار برای یادگیری پس‌زمینه (ثانیه)
BACKGROUND_LEARN_DELAY = 5.0


def get_current_layout():
    """تشخیص layout فعال پنجره جاری."""
    if not PYWIN_AVAILABLE:
        return "en"
    try:
        hwnd = win32gui.GetForegroundWindow()
        thread_id = win32process.GetWindowThreadProcessId(hwnd)[0]
        layout_id = win32api.GetKeyboardLayout(thread_id)
        lang_id = layout_id & 0xFFFF
        if lang_id == 0x0429:
            return "fa"
        elif lang_id == 0x0409:
            return "en"
        elif lang_id == 0x0407:
            return "de"
        return "en"
    except Exception:
        return "en"


class SmartKeyboardApp:
    """برنامه اصلی."""

    def __init__(self):
        self.config = get_config()
        self.dictionary = get_dictionary()
        self.learner = get_learner()

        self.is_monitoring = False
        self._hook = None
        self._input_buffer = ""
        self._pause_timer = None
        self._lock = threading.Lock()
        self._last_conversion_time = 0

        # --- برای یادگیری پس‌زمینه ---
        self._pending_learn_text = ""       # متنی که ممکنه یاد گرفته بشه
        self._pending_learn_lang = "en"     # زبان متن
        self._pending_learn_timer = None    # تایمر یادگیری
        self._last_hwnd = None              # هندل پنجره قبلی

        # حباب شناور
        self.popup = PopupBubble(
            on_accept=self._on_popup_accept,
            on_reject=self._on_popup_reject,
            on_learn=self._on_popup_learn,
        )

        # آیکون tray
        self.tray = TrayIcon(app=self)

        # خواندن تنظیمات
        self.pause_seconds = self.config.get("conversion", "pause_seconds", default=1.0)
        self.cooldown_seconds = self.config.get("conversion", "cooldown_seconds", default=2.0)
        self.auto_replace = self.config.get("conversion", "auto_replace", default=True)
        self.sound_enabled = self.config.get("ui", "sound_enabled", default=True)

        self.active_langs = self.config.get("languages", "active", default=["fa", "en"])

    # --- مدیریت کیبورد ---

    def _on_key_event(self, event):
        """مدیریت رویدادهای کیبورد."""
        if not self.is_monitoring:
            return

        try:
            if event.event_type != 'down':
                return

            name = event.name
            scan = event.scan_code

            # --- کلید میانبر دستی: Ctrl+Shift+F ---
            if name == 'f' and self._is_hotkey_pressed():
                self._force_convert_buffer()
                return

            # هر کلیدی که زده شد، تایمر یادگیری رو کنسل کن
            self._cancel_pending_learn()

            # حروف و اعداد
            if scan in SCANCODE_TO_CHAR:
                char = SCANCODE_TO_CHAR[scan]
                with self._lock:
                    self._input_buffer += char
                self._reset_pause_timer()

            # علائم نگارشی
            elif scan in SCANCODE_PUNCTUATION:
                char = SCANCODE_PUNCTUATION[scan]
                with self._lock:
                    self._input_buffer += char
                self._reset_pause_timer()

            # space
            elif name == 'space':
                with self._lock:
                    self._input_buffer += ' '
                self._reset_pause_timer()

            # backspace
            elif name == 'backspace':
                with self._lock:
                    if self._input_buffer:
                        self._input_buffer = self._input_buffer[:-1]
                self._reset_pause_timer()

            # enter و tab → بررسی فوری
            elif name in ('enter', 'tab'):
                self._process_buffer()

        except Exception as e:
            print(f"[Key Error] {e}")

    def _reset_pause_timer(self):
        """ریست کردن تایمر توقف."""
        if self._pause_timer:
            self._pause_timer.cancel()
        self._pause_timer = threading.Timer(self.pause_seconds, self._process_buffer)
        self._pause_timer.daemon = True
        self._pause_timer.start()

    def _process_buffer(self):
        """بررسی متن جمع‌شده و تبدیل در صورت نیاز."""
        with self._lock:
            raw = self._input_buffer
            self._input_buffer = ""

        text = raw.strip()
        if not text:
            return

        # cooldown
        now = time.time()
        if now - self._last_conversion_time < self.cooldown_seconds:
            return

        current_lang = get_current_layout()
        result = detect(text, current_lang, self.active_langs, self.dictionary)

        if result.action == 'keep':
            # متن معنی‌داره یا whitelist هست → برای یادگیری پس‌زمینه ذخیره کن
            self._schedule_pending_learn(text, current_lang)
            return

        print(f"[Detect] {result}")

        if result.action == 'auto' and self.auto_replace:
            # ذخیره هندل پنجره فعلی
            self._save_foreground_window()
            # متن توی صفحه = raw (با space و علائم)
            self._do_replace(raw, result.suggested)
            self.learner.on_accept(result.original, result.suggested,
                                   result.from_lang, result.to_lang, result.confidence)
            self._last_conversion_time = now
            self.tray.set_status("فعال", COLOR_ACTIVE)

        elif result.action == 'suggest':
            # ذخیره هندل پنجره فعلی
            self._save_foreground_window()
            if self.sound_enabled:
                play_ding()
            self.tray.set_status("پیشنهاد", COLOR_SUGGEST)
            self.popup.show(raw, result.suggested,
                            timeout=self.config.get("ui", "bubble_timeout", default=10))

    # --- یادگیری پس‌زمینه ---

    def _schedule_pending_learn(self, text, lang):
        """
        برنامه‌ریزی برای یادگیری متن بعد از چند ثانیه.
        اگه کاربر متن رو تغییر نده یا backspace نزنه، متن یاد گرفته میشه.
        """
        if not self.config.get("learning", "enabled", default=True):
            return
        if len(text) < 3:
            return

        self._pending_learn_text = text
        self._pending_learn_lang = lang

        # کنسل تایمر قبلی
        if self._pending_learn_timer:
            self._pending_learn_timer.cancel()

        # تایمر جدید
        self._pending_learn_timer = threading.Timer(
            BACKGROUND_LEARN_DELAY, self._do_pending_learn
        )
        self._pending_learn_timer.daemon = True
        self._pending_learn_timer.start()

    def _cancel_pending_learn(self):
        """کنسل کردن یادگیری پس‌زمینه (وقتی کاربر داره تایپ میکنه)."""
        if self._pending_learn_timer:
            self._pending_learn_timer.cancel()
            self._pending_learn_timer = None

    def _do_pending_learn(self):
        """یادگیری واقعی متن بعد از تاخیر."""
        text = self._pending_learn_text
        lang = self._pending_learn_lang
        self._pending_learn_text = ""

        if not text:
            return

        # اضافه کردن کلمات به لیست کاربر
        count = self.dictionary.add_sentence_words(text, lang=lang)
        if count > 0:
            print(f"[Learn] {count} کلمه از '{text[:50]}...' یاد گرفته شد.")

    # --- ذخیره/بازیابی پنجره ---

    def _save_foreground_window(self):
        """ذخیره هندل پنجره فعال."""
        if not PYWIN_AVAILABLE:
            return
        try:
            self._last_hwnd = win32gui.GetForegroundWindow()
        except Exception:
            self._last_hwnd = None

    def _restore_foreground_window(self):
        """برگرداندن focus به پنجره قبلی."""
        if not PYWIN_AVAILABLE or not self._last_hwnd:
            return
        try:
            win32gui.SetForegroundWindow(self._last_hwnd)
        except Exception:
            pass

    # --- جایگزینی متن ---

    def _do_replace(self, old_text, new_text):
        """جایگزینی متن تایپ‌شده با متن جدید."""
        try:
            import keyboard as kb
            backspace_count = len(old_text)
            for _ in range(backspace_count):
                kb.send('backspace')
                time.sleep(0.005)
            kb.write(new_text, delay=0.005)
        except Exception as e:
            print(f"[Replace Error] {e}")

    # --- Handlerهای حباب ---

    def _on_popup_accept(self, original, suggested):
        """کاربر پیشنهاد رو قبول کرد."""
        print(f"[Popup] قبول: '{original}' -> '{suggested}'")

        # صبر کن پاپ‌آپ بسته بشه
        time.sleep(0.3)

        # برگرداندن focus به پنجره قبلی
        self._restore_foreground_window()
        time.sleep(0.1)

        self._do_replace(original, suggested)
        self.learner.on_accept(original, suggested, "", "", 1.0)
        self._last_conversion_time = time.time()
        self.tray.set_status("فعال", COLOR_ACTIVE)

    def _on_popup_reject(self, original, suggested):
        """کاربر پیشنهاد رو رد کرد."""
        print(f"[Popup] رد: '{original}' -> '{suggested}'")
        self.learner.on_reject(original, suggested, "", "", 0.0)
        self.tray.set_status("فعال", COLOR_ACTIVE)

    def _on_popup_learn(self, word):
        """کاربر کلمه رو یاد داد."""
        print(f"[Popup] یاد بگیر: '{word}'")
        self.learner.on_learn(word)
        # همچنین کلمات جمله رو هم اضافه کن
        self.dictionary.add_sentence_words(word, lang="fa")
        self.tray.set_status("فعال", COLOR_ACTIVE)

    # --- شروع/توقف ---

    def start_monitoring(self):
        """شروع نظارت روی کیبورد."""
        if self.is_monitoring:
            return
        try:
            import keyboard as kb
            self._hook = kb.hook(self._on_key_event)
            self.is_monitoring = True
            print("[Main] نظارت فعال شد.")
        except Exception as e:
            print(f"[Main] خطا در شروع نظارت: {e}")

    def stop_monitoring(self):
        """توقف نظارت."""
        if not self.is_monitoring:
            return
        try:
            import keyboard as kb
            if self._hook:
                kb.unhook(self._hook)
                self._hook = None
        except Exception:
            pass
        self.is_monitoring = False
        if self._pause_timer:
            self._pause_timer.cancel()
        if self._pending_learn_timer:
            self._pending_learn_timer.cancel()
        print("[Main] نظارت متوقف شد.")

    # --- کلید میانبر دستی ---

    def _is_hotkey_pressed(self):
        """چک کن آیا Ctrl+Shift+F فشرده شده."""
        try:
            import keyboard as kb
            return kb.is_pressed('ctrl') and kb.is_pressed('shift')
        except Exception:
            return False

    def _force_convert_buffer(self):
        """تبدیل اجباری متن تایپ‌شده (بدون تشخیص خودکار)."""
        with self._lock:
            raw = self._input_buffer
            self._input_buffer = ""

        text = raw.strip()
        if not text:
            return

        current_lang = get_current_layout()
        for target in self.active_langs:
            if target != current_lang:
                converted = convert_text(text, current_lang, target)
                if converted != text:
                    print(f"[Force Convert] '{text}' -> '{converted}'")
                    self._save_foreground_window()
                    self._do_replace(raw, converted)
                    return

    # --- اجرا ---

    def run(self):
        """اجرای برنامه."""
        print("=" * 50)
        print("Smart Keyboard v2")
        print("=" * 50)

        # شروع آیکون tray توی ترد جدا
        self.tray.run_detached()

        # صبر کن tray بالا بیاد
        time.sleep(0.5)

        # شروع نظارت
        self.start_monitoring()

        print("\nبرنامه در حال اجراست.")
        print("راست‌کلیک روی آیکون tray برای گزینه‌ها.")
        print("برای خروج: Ctrl+C\n")

        # حلقه اصلی
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Main] خروج...")
            self.stop_monitoring()
            self.tray.stop()


if __name__ == "__main__":
    app = SmartKeyboardApp()
    app.run()