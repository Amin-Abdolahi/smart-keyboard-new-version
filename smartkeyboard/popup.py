# smartkeyboard/popup.py
# حباب شناور شبیه Grammarly

import tkinter as tk
from tkinter import font as tkfont
import threading
import platform


# --- رنگ‌ها ---
BG_COLOR = "#2b2b2b"
FG_COLOR = "#ffffff"
ACCENT_COLOR = "#4a9eff"
BTN_BG = "#3c3c3c"
BTN_HOVER = "#505050"
BTN_ACCEPT = "#4a9eff"
BTN_REJECT = "#666666"
BTN_LEARN = "#6b9e3f"


class PopupBubble:
    """
    حباب شناور برای نمایش پیشنهاد.
    """

    def __init__(self, on_accept=None, on_reject=None, on_learn=None):
        self.on_accept = on_accept
        self.on_reject = on_reject
        self.on_learn = on_learn

        self.root = None
        self.current_original = ""
        self.current_suggested = ""
        self._close_timer = None
        self._is_visible = False

    def _create_window(self, original, suggested):
        """ساخت پنجره Tkinter."""
        self.root = tk.Tk()
        self.root.title("Smart Keyboard")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=BG_COLOR)

        # موقعیت: گوشه پایین راست صفحه
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w = 420
        win_h = 180
        x = screen_w - win_w - 30
        y = screen_h - win_h - 60
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")

        # فونت
        try:
            title_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")
            text_font = tkfont.Font(family="Segoe UI", size=12)
            btn_font = tkfont.Font(family="Segoe UI", size=9)
        except Exception:
            title_font = ("Arial", 10, "bold")
            text_font = ("Arial", 12)
            btn_font = ("Arial", 9)

        # --- هدر ---
        header = tk.Frame(self.root, bg=BG_COLOR)
        header.pack(fill="x", padx=12, pady=(10, 4))

        title = tk.Label(
            header, text="✨ پیشنهاد اصلاح",
            font=title_font, bg=BG_COLOR, fg=ACCENT_COLOR
        )
        title.pack(side="right")

        close_btn = tk.Label(
            header, text="✕", font=btn_font,
            bg=BG_COLOR, fg="#888888", cursor="hand2"
        )
        close_btn.pack(side="left")
        close_btn.bind("<Button-1>", lambda e: self._on_reject())

        # --- متن پیشنهادی ---
        text_frame = tk.Frame(self.root, bg=BG_COLOR)
        text_frame.pack(fill="both", expand=True, padx=12, pady=4)

        text_label = tk.Label(
            text_frame,
            text=suggested,
            font=text_font,
            bg=BG_COLOR,
            fg=FG_COLOR,
            wraplength=380,
            justify="right",
            anchor="e",
        )
        text_label.pack(fill="both", expand=True)

        # --- دکمه‌ها ---
        btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        btn_frame.pack(fill="x", padx=12, pady=(4, 10))

        # دکمه جایگزین
        accept_btn = tk.Label(
            btn_frame, text="✓ جایگزین", font=btn_font,
            bg=BTN_ACCEPT, fg="white", padx=12, pady=5, cursor="hand2"
        )
        accept_btn.pack(side="right", padx=(4, 0))
        accept_btn.bind("<Button-1>", lambda e: self._on_accept())

        # دکمه رد
        reject_btn = tk.Label(
            btn_frame, text="✕ رد", font=btn_font,
            bg=BTN_REJECT, fg="white", padx=12, pady=5, cursor="hand2"
        )
        reject_btn.pack(side="right", padx=4)
        reject_btn.bind("<Button-1>", lambda e: self._on_reject())

        # دکمه یاد بگیر
        learn_btn = tk.Label(
            btn_frame, text="📚 یاد بگیر", font=btn_font,
            bg=BTN_LEARN, fg="white", padx=12, pady=5, cursor="hand2"
        )
        learn_btn.pack(side="right", padx=4)
        learn_btn.bind("<Button-1>", lambda e: self._on_learn())

        # بستن با Escape
        self.root.bind("<Escape>", lambda e: self._on_reject())

    def show(self, original, suggested, timeout=10):
        """نمایش حباب."""
        if self._is_visible:
            self.close()

        self.current_original = original
        self.current_suggested = suggested

        def run():
            self._is_visible = True
            self._create_window(original, suggested)

            if timeout > 0:
                self._close_timer = threading.Timer(timeout, self._auto_close)
                self._close_timer.daemon = True
                self._close_timer.start()

            self.root.mainloop()
            self._is_visible = False

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def _auto_close(self):
        """بستن خودکار بعد از timeout."""
        try:
            if self.root:
                self.root.after(0, self.root.destroy)
        except Exception:
            pass

    def _on_accept(self):
        """کاربر روی 'جایگزین' کلیک کرد."""
        if self._close_timer:
            self._close_timer.cancel()
        # اول ببند
        self._close()
        # بعد callback رو توی ترد جدا صدا بزن
        if self.on_accept:
            threading.Thread(
                target=self.on_accept,
                args=(self.current_original, self.current_suggested),
                daemon=True
            ).start()

    def _on_reject(self):
        """کاربر روی 'رد' کلیک کرد."""
        if self._close_timer:
            self._close_timer.cancel()
        self._close()
        if self.on_reject:
            threading.Thread(
                target=self.on_reject,
                args=(self.current_original, self.current_suggested),
                daemon=True
            ).start()

    def _on_learn(self):
        """کاربر روی 'یاد بگیر' کلیک کرد."""
        if self._close_timer:
            self._close_timer.cancel()
        self._close()
        if self.on_learn:
            threading.Thread(
                target=self.on_learn,
                args=(self.current_suggested,),
                daemon=True
            ).start()

    def _close(self):
        try:
            if self.root:
                self.root.after(0, self.root.destroy)
        except Exception:
            pass
        self._is_visible = False

    def close(self):
        """بستن حباب از بیرون."""
        self._close()


def play_ding():
    """پخش صدای دینگ (فقط روی ویندوز)."""
    try:
        if platform.system() == "Windows":
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass


if __name__ == "__main__":
    print("تست popup (۵ ثانیه نمایش داده میشه)...")

    def on_accept(o, s):
        print(f"قبول شد: '{o}' -> '{s}'")

    def on_reject(o, s):
        print(f"رد شد: '{o}' -> '{s}'")

    def on_learn(s):
        print(f"یاد گرفته شد: '{s}'")

    bubble = PopupBubble(
        on_accept=on_accept,
        on_reject=on_reject,
        on_learn=on_learn,
    )

    play_ding()
    bubble.show("sghl", "سلام", timeout=5)

    import time
    time.sleep(6)
    print("پایان تست.")