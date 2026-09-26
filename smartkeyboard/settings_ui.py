# smartkeyboard/settings_ui.py
# پنجره تنظیمات گرافیکی

import tkinter as tk
from tkinter import ttk, messagebox
import threading

from .config import get_config
from .dictionary import get_dictionary
from .languages import LANGUAGES, get_available_languages
from .learner import get_learner


# --- رنگ‌ها ---
BG = "#f0f0f0"
FG = "#202020"
ACCENT = "#0078d4"
CARD_BG = "#ffffff"


class SettingsWindow:
    """پنجره تنظیمات."""

    def __init__(self, on_save=None):
        self.config = get_config()
        self.dictionary = get_dictionary()
        self.learner = get_learner()
        self.on_save = on_save

        self.root = None
        self._vars = {}

    def _create_window(self):
        self.root = tk.Tk()
        self.root.title("تنظیمات Smart Keyboard")
        self.root.geometry("600x700")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.root.bind("<Escape>", lambda e: self.root.destroy())

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=[16, 8], font=("Segoe UI", 10))

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_languages_tab(notebook)
        self._build_conversion_tab(notebook)
        self._build_ui_tab(notebook)
        self._build_dictionary_tab(notebook)

        btn_frame = tk.Frame(self.root, bg=BG)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        save_btn = tk.Button(
            btn_frame, text="ذخیره", command=self._on_save,
            bg=ACCENT, fg="white", font=("Segoe UI", 10, "bold"),
            padx=20, pady=6, bd=0, cursor="hand2"
        )
        save_btn.pack(side="right", padx=4)

        cancel_btn = tk.Button(
            btn_frame, text="انصراف", command=self.root.destroy,
            bg="#cccccc", fg=FG, font=("Segoe UI", 10),
            padx=20, pady=6, bd=0, cursor="hand2"
        )
        cancel_btn.pack(side="right", padx=4)

    # --- تب زبان‌ها ---

    def _build_languages_tab(self, notebook):
        frame = tk.Frame(notebook, bg=BG)
        notebook.add(frame, text="زبان‌ها")

        tk.Label(
            frame, text="زبان‌های فعال:", bg=BG, fg=FG,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="e", padx=10, pady=(15, 5))

        active_frame = tk.Frame(frame, bg=BG)
        active_frame.pack(fill="x", padx=10)

        active_langs = self.config.get("languages", "active", default=["fa", "en"])

        for code, info in LANGUAGES.items():
            var = tk.BooleanVar(value=(code in active_langs))
            self._vars[f"lang_{code}"] = var
            cb = tk.Checkbutton(
                active_frame, text=f"{info['native_name']} ({info['name']})",
                variable=var, bg=BG, fg=FG, font=("Segoe UI", 10),
                anchor="e", justify="right"
            )
            cb.pack(anchor="e", pady=2)

        tk.Label(
            frame, text="زبان اصلی:", bg=BG, fg=FG,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="e", padx=10, pady=(20, 5))

        primary_var = tk.StringVar(
            value=self.config.get("languages", "primary", default="fa")
        )
        self._vars["primary_lang"] = primary_var

        primary_frame = tk.Frame(frame, bg=BG)
        primary_frame.pack(fill="x", padx=10)

        for code, info in LANGUAGES.items():
            rb = tk.Radiobutton(
                primary_frame, text=info['native_name'],
                variable=primary_var, value=code,
                bg=BG, fg=FG, font=("Segoe UI", 10),
                anchor="e", justify="right"
            )
            rb.pack(anchor="e", pady=2)

    # --- تب تبدیل ---

    def _build_conversion_tab(self, notebook):
        frame = tk.Frame(notebook, bg=BG)
        notebook.add(frame, text="تبدیل")

        self._add_slider(
            frame, "آستانه تبدیل خودکار:",
            "auto_threshold",
            self.config.get("conversion", "auto_convert_threshold", default=0.75),
            0.5, 1.0, 0.05
        )

        self._add_slider(
            frame, "آستانه نمایش پیشنهاد:",
            "suggest_threshold",
            self.config.get("conversion", "suggest_threshold", default=0.30),
            0.1, 0.9, 0.05
        )

        self._add_slider(
            frame, "زمان توقف قبل از بررسی (ثانیه):",
            "pause_seconds",
            self.config.get("conversion", "pause_seconds", default=1.0),
            0.3, 3.0, 0.1
        )

        self._add_slider(
            frame, "فاصله بین پیشنهادها (ثانیه):",
            "cooldown_seconds",
            self.config.get("conversion", "cooldown_seconds", default=2.0),
            0.5, 10.0, 0.5
        )

        auto_var = tk.BooleanVar(
            value=self.config.get("conversion", "auto_replace", default=True)
        )
        self._vars["auto_replace"] = auto_var
        tk.Checkbutton(
            frame, text="جایگزینی خودکار در اطمینان بالا",
            variable=auto_var, bg=BG, fg=FG, font=("Segoe UI", 10),
            anchor="e", justify="right"
        ).pack(anchor="e", padx=20, pady=10)

        # ← قابلیت جدید: تغییر خودکار layout
        switch_var = tk.BooleanVar(
            value=self.config.get("conversion", "auto_switch_layout", default=False)
        )
        self._vars["auto_switch_layout"] = switch_var
        tk.Checkbutton(
            frame, text="تغییر خودکار layout بعد از تبدیل",
            variable=switch_var, bg=BG, fg=FG, font=("Segoe UI", 10),
            anchor="e", justify="right"
        ).pack(anchor="e", padx=20, pady=10)

    # --- تب رابط کاربری ---

    def _build_ui_tab(self, notebook):
        frame = tk.Frame(notebook, bg=BG)
        notebook.add(frame, text="رابط کاربری")

        bubble_var = tk.BooleanVar(
            value=self.config.get("ui", "bubble_enabled", default=True)
        )
        self._vars["bubble_enabled"] = bubble_var
        tk.Checkbutton(
            frame, text="نمایش حباب شناور",
            variable=bubble_var, bg=BG, fg=FG, font=("Segoe UI", 10),
            anchor="e", justify="right"
        ).pack(anchor="e", padx=20, pady=10)

        sound_var = tk.BooleanVar(
            value=self.config.get("ui", "sound_enabled", default=True)
        )
        self._vars["sound_enabled"] = sound_var
        tk.Checkbutton(
            frame, text="پخش صدای دینگ",
            variable=sound_var, bg=BG, fg=FG, font=("Segoe UI", 10),
            anchor="e", justify="right"
        ).pack(anchor="e", padx=20, pady=10)

        self._add_slider(
            frame, "زمان بسته شدن خودکار حباب (ثانیه):",
            "bubble_timeout",
            self.config.get("ui", "bubble_timeout", default=10),
            3, 30, 1
        )

    # --- تب دیکشنری ---

    def _build_dictionary_tab(self, notebook):
        frame = tk.Frame(notebook, bg=BG)
        notebook.add(frame, text="دیکشنری")

        stats = self.dictionary.stats()

        tk.Label(
            frame, text="آمار دیکشنری:", bg=BG, fg=FG,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="e", padx=20, pady=(15, 10))

        stats_frame = tk.Frame(frame, bg=CARD_BG, relief="solid", bd=1)
        stats_frame.pack(fill="x", padx=20, pady=5)

        labels = {
            "builtin_fa": "کلمات پایه فارسی",
            "builtin_en": "کلمات پایه انگلیسی",
            "whitelist": "اصطلاحات فنی",
            "user_words": "کلمات شخصی",
            "ignored_words": "کلمات رد‌شده",
            "learned_words": "کلمات یادگرفته",
        }

        for key, label in labels.items():
            row = tk.Frame(stats_frame, bg=CARD_BG)
            row.pack(fill="x", padx=10, pady=3)
            tk.Label(
                row, text=label, bg=CARD_BG, fg=FG,
                font=("Segoe UI", 10), anchor="e"
            ).pack(side="right")
            tk.Label(
                row, text=str(stats.get(key, 0)), bg=CARD_BG, fg=ACCENT,
                font=("Segoe UI", 10, "bold"), anchor="w"
            ).pack(side="left")

        clear_btn = tk.Button(
            frame, text="پاک کردن لاگ تبدیل‌ها",
            command=self._clear_log,
            bg="#dc3545", fg="white", font=("Segoe UI", 10),
            padx=15, pady=6, bd=0, cursor="hand2"
        )
        clear_btn.pack(anchor="e", padx=20, pady=20)

    # --- کمکی ---

    def _add_slider(self, parent, label, key, value, from_, to, step):
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="x", padx=20, pady=10)

        tk.Label(
            frame, text=label, bg=BG, fg=FG,
            font=("Segoe UI", 10), anchor="e"
        ).pack(anchor="e")

        var = tk.DoubleVar(value=float(value))
        self._vars[key] = var

        value_label = tk.Label(
            frame, text=f"{value:.2f}", bg=BG, fg=ACCENT,
            font=("Segoe UI", 10, "bold"), anchor="e"
        )
        value_label.pack(anchor="e")

        def on_change(v):
            value_label.config(text=f"{float(v):.2f}")

        scale = tk.Scale(
            frame, from_=from_, to=to, resolution=step,
            orient="horizontal", variable=var,
            bg=BG, fg=FG, highlightthickness=0,
            troughcolor="#cccccc", activebackground=ACCENT,
            command=on_change
        )
        scale.pack(fill="x")

    def _clear_log(self):
        if messagebox.askyesno("تایید", "لاگ تبدیل‌ها پاک بشه؟"):
            self.learner.clear_log()
            messagebox.showinfo("انجام شد", "لاگ پاک شد.")

    def _on_save(self):
        # زبان‌های فعال
        active = [code for code in LANGUAGES if self._vars[f"lang_{code}"].get()]
        if not active:
            messagebox.showerror("خطا", "حداقل یه زبان باید فعال باشه.")
            return
        self.config.set("languages", "active", value=active)

        self.config.set("languages", "primary",
                        value=self._vars["primary_lang"].get())

        # تبدیل
        self.config.set("conversion", "auto_convert_threshold",
                        value=self._vars["auto_threshold"].get())
        self.config.set("conversion", "suggest_threshold",
                        value=self._vars["suggest_threshold"].get())
        self.config.set("conversion", "pause_seconds",
                        value=self._vars["pause_seconds"].get())
        self.config.set("conversion", "cooldown_seconds",
                        value=self._vars["cooldown_seconds"].get())
        self.config.set("conversion", "auto_replace",
                        value=self._vars["auto_replace"].get())
        self.config.set("conversion", "auto_switch_layout",
                        value=self._vars["auto_switch_layout"].get())

        # UI
        self.config.set("ui", "bubble_enabled",
                        value=self._vars["bubble_enabled"].get())
        self.config.set("ui", "sound_enabled",
                        value=self._vars["sound_enabled"].get())
        self.config.set("ui", "bubble_timeout",
                        value=int(self._vars["bubble_timeout"].get()))

        if self.on_save:
            self.on_save()

        messagebox.showinfo("ذخیره شد", "تنظیمات با موفقیت ذخیره شد.")
        self.root.destroy()

    def show(self):
        def run():
            self._create_window()
            self.root.mainloop()

        thread = threading.Thread(target=run, daemon=True)
        thread.start()


def open_settings(on_save=None):
    w = SettingsWindow(on_save=on_save)
    w.show()


if __name__ == "__main__":
    print("تست پنجره تنظیمات...")
    open_settings()
    import time
    time.sleep(15)