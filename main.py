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
    26: '[', 27: ']', 43: '\\',
    30: 'a', 31: 's', 32: 'd', 33: 'f', 34: 'g', 35: 'h', 36: 'j', 37: 'k', 38: 'l',
    39: ';', 40: "'",
    44: 'z', 45: 'x', 46: 'c', 47: 'v', 48: 'b', 49: 'n', 50: 'm',
    51: ',', 52: '.', 53: '/',
    2: '1', 3: '2', 4: '3', 5: '4', 6: '5', 7: '6', 8: '7', 9: '8', 10: '9', 11: '0',
    12: '-', 13: '=',
}


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

            # حروف و اعداد
            if scan in SCANCODE_TO_CHAR:
                char = SCANCODE_TO_CHAR[scan]
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
            text = self._input_buffer.strip()
            self._input_buffer = ""

        if not text:
            return

        # cooldown
        now = time.time()
        if now - self._last_conversion_time < self.cooldown_seconds:
            return

        current_lang = get_current_layout()
        result = detect(text, current_lang, self.active_langs, self.dictionary)

        if result.action == 'keep':
            return

        print(f"[Detect] {result}")

        if result.action == 'auto' and self.auto_replace:
            # تبدیل خودکار
            self._do_replace(result.original, result.suggested)
            self.learner.on_accept(result.original, result.suggested,
                                   result.from_lang, result.to_lang, result.confidence)
            self._last_conversion_time = now
            self.tray.set_status("فعال", COLOR_ACTIVE)

        elif result.action == 'suggest':
            # نمایش حباب
            if self.sound_enabled:
                play_ding()
            self.tray.set_status("پیشنهاد", COLOR_SUGGEST)
            self.popup.show(result.original, result.suggested,
                            timeout=self.config.get("ui", "bubble_timeout", default=10))

    def _do_replace(self, old_text, new_text):
        """جایگزینی متن تایپ‌شده با متن جدید."""
        try:
            import keyboard as kb
            for _ in range(len(old_text)):
                kb.send('backspace')
                time.sleep(0.005)
            kb.write(new_text, delay=0.005)
        except Exception as e:
            print(f"[Replace Error] {e}")

    # --- Handlerهای حباب ---

    def _on_popup_accept(self, original, suggested):
        """کاربر پیشنهاد رو قبول کرد."""
        print(f"[Popup] قبول: '{original}' -> '{suggested}'")
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
        print("[Main] نظارت متوقف شد.")

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