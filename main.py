# main.py
# Smart Keyboard v2 - نقطه ورود برنامه

import os
import sys
import time
import threading
import platform

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smartkeyboard.logger import get_logger, log_exception, info, debug, warning, error
from smartkeyboard.config import get_config
from smartkeyboard.dictionary import get_dictionary
from smartkeyboard.detector import detect
from smartkeyboard.learner import get_learner
from smartkeyboard.converter import convert_text
from smartkeyboard.languages import EN_TO_FA, FA_TO_EN, EN_TO_DE_SPECIAL, DE_TO_EN_SPECIAL
from smartkeyboard.popup import PopupBubble, play_ding
from smartkeyboard.tray import TrayIcon, COLOR_ACTIVE, COLOR_IDLE, COLOR_SUGGEST


PYWIN_AVAILABLE = False
win32gui = None
win32api = None
win32process = None
win32con = None

if platform.system() == "Windows":
    try:
        import win32gui
        import win32api
        import win32process
        import win32con
        PYWIN_AVAILABLE = True
    except ImportError as e:
        print(f"[Warning] pywin32 پیدا نشد: {e}")


BACKGROUND_LEARN_DELAY = 5.0
MAX_TEXT_LENGTH = 300
COOLDOWN_AFTER_REPLACE = 1.5


LANG_IDS = {
    "fa": 0x0429,
    "en": 0x0409,
    "de": 0x0407,
    "ar": 0x0401,
}

SHIFTED_CHARS = {
    '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
    '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
    '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
    ';': ':', "'": '"', ',': '<', '.': '>', '/': '?',
    '`': '~',
}


def get_current_layout():
    if not PYWIN_AVAILABLE or win32gui is None or win32api is None or win32process is None:
        return "en"
    try:
        hwnd = win32gui.GetForegroundWindow()
        thread_id = win32process.GetWindowThreadProcessId(hwnd)[0]
        layout_id = win32api.GetKeyboardLayout(thread_id)
        lang_id = layout_id & 0xFFFF
        for code, lid in LANG_IDS.items():
            if lang_id == lid:
                return code
        return "en"
    except Exception as e:
        debug(f"خطا در تشخیص layout: {e}")
        return "en"


def get_real_char(physical_char, layout):
    if layout == "fa":
        return EN_TO_FA.get(physical_char, physical_char)
    elif layout == "de":
        return EN_TO_DE_SPECIAL.get(physical_char, physical_char)
    return physical_char


def switch_keyboard_layout(lang_code):
    if not PYWIN_AVAILABLE or win32gui is None or win32api is None or win32con is None:
        return False

    try:
        layouts = win32api.GetKeyboardLayoutList()
        if not layouts:
            return False

        target_lang_id = LANG_IDS.get(lang_code)
        if target_lang_id is None:
            return False

        target_hkl = None
        for hkl in layouts:
            if (hkl & 0xFFFF) == target_lang_id:
                target_hkl = hkl
                break

        if not target_hkl:
            warning(f"زبان {lang_code} نصب نیست.")
            return False

        hwnd = win32gui.GetForegroundWindow()
        win32api.SendMessage(
            hwnd,
            win32con.WM_INPUTLANGCHANGEREQUEST,
            0,
            target_hkl  # type: ignore
        )
        info(f"تغییر layout به {lang_code}")
        return True
    except Exception as e:
        log_exception(e, context="switch_keyboard_layout")
        return False


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
        self._last_conversion_time = 0.0
        self._is_replacing = False
        self._buffer_layout = None

        self._pending_learn_text = ""
        self._pending_learn_lang = "en"
        self._pending_learn_timer = None
        self._last_hwnd = None

        self.popup = PopupBubble(
            on_accept=self._on_popup_accept,
            on_reject=self._on_popup_reject,
            on_learn=self._on_popup_learn,
        )

        self.tray = TrayIcon(app=self)

        self.pause_seconds = float(
            self.config.get("conversion", "pause_seconds", default=1.0) or 1.0
        )
        self.cooldown_seconds = float(
            self.config.get("conversion", "cooldown_seconds", default=2.0) or 2.0
        )
        self.auto_replace = bool(
            self.config.get("conversion", "auto_replace", default=True)
        )
        self.auto_switch_layout = bool(
            self.config.get("conversion", "auto_switch_layout", default=False)
        )
        self.sound_enabled = bool(
            self.config.get("ui", "sound_enabled", default=True)
        )
        self.bubble_timeout = int(
            self.config.get("ui", "bubble_timeout", default=10) or 10
        )

        self.active_langs = self.config.get("languages", "active", default=["fa", "en"])
        if not isinstance(self.active_langs, list):
            self.active_langs = ["fa", "en"]

        info("SmartKeyboardApp ساخته شد")

    def _on_key_event(self, event):
        if not self.is_monitoring:
            return

        try:
            if event.event_type != 'down':
                return

            name = event.name
            scan = event.scan_code

            if name == 'f' and self._is_hotkey_pressed():
                self._force_convert_buffer()
                return

            self._cancel_pending_learn()

            if self._is_replacing:
                debug(f"در حال replace، نادیده گرفتن: name={name}")
                return

            now = time.time()
            if now - self._last_conversion_time < COOLDOWN_AFTER_REPLACE:
                debug(f"cooldown، نادیده گرفتن: name={name}")
                return

            current_layout = get_current_layout()

            if name and len(name) == 1:
                try:
                    import keyboard as kb
                    if kb.is_pressed('shift'):
                        name = SHIFTED_CHARS.get(name, name)
                except Exception:
                    pass

                with self._lock:
                    if not self._input_buffer:
                        self._buffer_layout = current_layout
                    real_char = get_real_char(name, current_layout)
                    self._input_buffer += real_char
                self._reset_pause_timer()

            elif name == 'space':
                with self._lock:
                    if not self._input_buffer:
                        self._buffer_layout = current_layout
                    self._input_buffer += ' '
                self._reset_pause_timer()

            elif name == 'backspace':
                with self._lock:
                    if self._input_buffer:
                        self._input_buffer = self._input_buffer[:-1]
                self._reset_pause_timer()

            elif name in ('enter', 'tab'):
                self._process_buffer()

        except Exception as e:
            log_exception(e, context="key_event")

    def _reset_pause_timer(self):
        if self._pause_timer:
            self._pause_timer.cancel()
        self._pause_timer = threading.Timer(self.pause_seconds, self._process_buffer)
        self._pause_timer.daemon = True
        self._pause_timer.start()

    def _process_buffer(self):
        with self._lock:
            raw = self._input_buffer
            self._input_buffer = ""
            buffer_layout = self._buffer_layout or "en"
            self._buffer_layout = None

        text = raw.strip()
        if not text:
            return

        if len(text) > MAX_TEXT_LENGTH:
            warning(f"متن طولانی ({len(text)} کاراکتر)، نادیده گرفته میشه.")
            return

        now = time.time()
        if now - self._last_conversion_time < self.cooldown_seconds:
            debug("cooldown فعال، نادیده گرفته میشه")
            return

        current_lang = buffer_layout
        debug(f"بررسی: text='{text}', layout={current_lang}")

        result = detect(text, current_lang, self.active_langs, self.dictionary)

        if result.action == 'keep':
            debug(f"keep: '{text}'")
            self._schedule_pending_learn(text, current_lang)
            return

        info(f"تشخیص: action={result.action}, confidence={result.confidence:.2f}, "
             f"'{result.original}' -> '{result.suggested}'")

        if result.action == 'auto' and self.auto_replace:
            with self._lock:
                self._input_buffer = ""

            self._is_replacing = True
            self._last_conversion_time = time.time()

            self._save_foreground_window()
            self._do_replace(raw, result.suggested)
            self.learner.on_accept(result.original, result.suggested,
                                   result.from_lang, result.to_lang, result.confidence)

            if self.auto_switch_layout:
                time.sleep(0.2)
                switch_keyboard_layout(result.to_lang)

            with self._lock:
                self._input_buffer = ""
            self._is_replacing = False
            self._last_conversion_time = time.time()

            self.tray.set_status("فعال", COLOR_ACTIVE)

        elif result.action == 'suggest':
            self._save_foreground_window()
            if self.sound_enabled:
                play_ding()
            self.tray.set_status("پیشنهاد", COLOR_SUGGEST)
            self.popup.show(raw, result.suggested, timeout=self.bubble_timeout)

    def _schedule_pending_learn(self, text, lang):
        if not self.config.get("learning", "enabled", default=True):
            return
        if len(text) < 3:
            return

        self._pending_learn_text = text
        self._pending_learn_lang = lang

        if self._pending_learn_timer:
            self._pending_learn_timer.cancel()

        self._pending_learn_timer = threading.Timer(
            BACKGROUND_LEARN_DELAY, self._do_pending_learn
        )
        self._pending_learn_timer.daemon = True
        self._pending_learn_timer.start()

    def _cancel_pending_learn(self):
        if self._pending_learn_timer:
            self._pending_learn_timer.cancel()
            self._pending_learn_timer = None

    def _do_pending_learn(self):
        text = self._pending_learn_text
        lang = self._pending_learn_lang
        self._pending_learn_text = ""

        if not text:
            return

        self.learner.on_background_learn(text, lang)

    def _save_foreground_window(self):
        if not PYWIN_AVAILABLE or win32gui is None:
            return
        try:
            self._last_hwnd = win32gui.GetForegroundWindow()
        except Exception as e:
            debug(f"خطا در ذخیره پنجره: {e}")
            self._last_hwnd = None

    def _restore_foreground_window(self):
        if not PYWIN_AVAILABLE or win32gui is None or not self._last_hwnd:
            return
        try:
            win32gui.SetForegroundWindow(self._last_hwnd)
        except Exception as e:
            debug(f"خطا در بازیابی پنجره: {e}")

    def _do_replace(self, old_text, new_text):
        try:
            import keyboard as kb
            has_trailing_space = old_text.endswith(' ')
            old_text_clean = old_text.rstrip()
            time.sleep(0.1)
            backspace_count = len(old_text_clean)
            if has_trailing_space:
                backspace_count += 1
            for i in range(backspace_count):
                kb.send('backspace')
                time.sleep(0.02)
            time.sleep(0.15)
            kb.write(new_text, delay=0.025)
            debug(f"جایگزینی: '{old_text_clean}' -> '{new_text}'")
        except Exception as e:
            log_exception(e, context="do_replace")

    def _on_popup_accept(self, original, suggested):
        info(f"پاپ‌آپ قبول: '{original}' -> '{suggested}'")
        self._is_replacing = True
        self._last_conversion_time = time.time()
        time.sleep(0.3)
        self._restore_foreground_window()
        time.sleep(0.15)
        with self._lock:
            self._input_buffer = ""
        self._do_replace(original, suggested)
        self.learner.on_accept(original, suggested, "", "", 1.0)
        if self.auto_switch_layout:
            time.sleep(0.2)
            if any('\u0600' <= c <= '\u06FF' for c in suggested):
                switch_keyboard_layout("fa")
            else:
                switch_keyboard_layout("en")
        with self._lock:
            self._input_buffer = ""
        self._is_replacing = False
        self._last_conversion_time = time.time()
        self.tray.set_status("فعال", COLOR_ACTIVE)

    def _on_popup_reject(self, original, suggested):
        info(f"پاپ‌آپ رد: '{original}' -> '{suggested}'")
        self.learner.on_reject(original, suggested, "", "", 0.0)
        self._cancel_pending_learn()
        self.tray.set_status("فعال", COLOR_ACTIVE)

    def _on_popup_learn(self, word):
        info(f"پاپ‌آپ یاد بگیر: '{word}'")
        self._is_replacing = True
        self._last_conversion_time = time.time()
        self.learner.on_learn(word)
        self.dictionary.add_sentence_words(word, lang="fa")
        time.sleep(0.3)
        self._restore_foreground_window()
        time.sleep(0.15)
        with self._lock:
            self._input_buffer = ""
        original = self.popup.current_original.rstrip()
        self._do_replace(original, word)
        if self.auto_switch_layout:
            time.sleep(0.2)
            if any('\u0600' <= c <= '\u06FF' for c in word):
                switch_keyboard_layout("fa")
            else:
                switch_keyboard_layout("en")
        with self._lock:
            self._input_buffer = ""
        self._is_replacing = False
        self._last_conversion_time = time.time()
        self.tray.set_status("فعال", COLOR_ACTIVE)

    def start_monitoring(self):
        if self.is_monitoring:
            return
        try:
            import keyboard as kb
            self._hook = kb.hook(self._on_key_event)
            self.is_monitoring = True
            info("نظارت فعال شد.")
        except Exception as e:
            log_exception(e, context="start_monitoring")

    def stop_monitoring(self):
        if not self.is_monitoring:
            return
        try:
            import keyboard as kb
            if self._hook:
                kb.unhook(self._hook)
                self._hook = None
        except Exception as e:
            log_exception(e, context="stop_monitoring")
        self.is_monitoring = False
        if self._pause_timer:
            self._pause_timer.cancel()
        if self._pending_learn_timer:
            self._pending_learn_timer.cancel()
        info("نظارت متوقف شد.")

    def _is_hotkey_pressed(self):
        try:
            import keyboard as kb
            return kb.is_pressed('ctrl') and kb.is_pressed('shift')
        except Exception:
            return False

    def _force_convert_buffer(self):
        with self._lock:
            raw = self._input_buffer
            self._input_buffer = ""
            buffer_layout = self._buffer_layout or "en"
            self._buffer_layout = None
        text = raw.strip()
        if not text:
            return
        current_lang = buffer_layout
        for target in self.active_langs:
            if target != current_lang:
                converted = convert_text(text, current_lang, target)
                if converted != text:
                    info(f"تبدیل دستی: '{text}' -> '{converted}'")
                    self._is_replacing = True
                    self._last_conversion_time = time.time()
                    self._save_foreground_window()
                    self._do_replace(raw, converted)
                    if self.auto_switch_layout:
                        time.sleep(0.2)
                        switch_keyboard_layout(target)
                    with self._lock:
                        self._input_buffer = ""
                    self._is_replacing = False
                    self._last_conversion_time = time.time()
                    return

    def run(self):
        info("=" * 50)
        info("Smart Keyboard v2 شروع شد")
        info("=" * 50)
        print("=" * 50)
        print("Smart Keyboard v2")
        print("=" * 50)
        self.tray.run_detached()
        time.sleep(0.5)
        self.start_monitoring()
        print("\nبرنامه در حال اجراست.")
        print("راست‌کلیک روی آیکون tray برای گزینه‌ها.")
        print("برای خروج: Ctrl+C\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            info("خروج با Ctrl+C")
            print("\n[Main] خروج...")
            self.stop_monitoring()
            self.tray.stop()


if __name__ == "__main__":
    app = SmartKeyboardApp()
    app.run()