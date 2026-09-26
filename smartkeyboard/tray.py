# smartkeyboard/tray.py
# آیکون system tray

import os
import threading
from pathlib import Path

from PIL import Image, ImageDraw
from pystray import Icon, MenuItem, Menu


# رنگ‌های آیکون بر اساس وضعیت
COLOR_IDLE = (100, 100, 100)      # خاکستری - غیرفعال
COLOR_ACTIVE = (0, 120, 215)      # آبی - فعال
COLOR_SUGGEST = (255, 165, 0)     # نارنجی - در حال پیشنهاد
COLOR_ERROR = (220, 50, 50)       # قرمز - خطا


def create_icon_image(color, size=64):
    """ساخت یه آیکون ساده با یه رنگ خاص."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # دایره پر
    margin = 6
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=color + (255,),
        outline=(255, 255, 255, 200),
        width=2,
    )
    # یه حرف K توش
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("segoeui.ttf", size // 2)
    except Exception:
        font = None
    draw.text(
        (size // 2, size // 2), "K",
        fill=(255, 255, 255, 255),
        font=font, anchor="mm"
    )
    return img


class TrayIcon:
    """مدیریت آیکون system tray."""

    def __init__(self, app=None):
        self.app = app
        self.icon = None
        self._thread = None
        self._current_color = COLOR_IDLE
        self._status_text = "غیرفعال"

        self.icon_image = create_icon_image(COLOR_IDLE)

    def _build_menu(self):
        """ساخت منوی راست‌کلیک."""
        return Menu(
            MenuItem(
                lambda text: f"وضعیت: {self._status_text}",
                None,
                enabled=False,
            ),
            Menu.SEPARATOR,
            MenuItem('شروع نظارت', self._on_start),
            MenuItem('توقف نظارت', self._on_stop),
            Menu.SEPARATOR,
            MenuItem('تنظیمات', self._on_settings),
            MenuItem('آمار', self._on_stats),
            Menu.SEPARATOR,
            MenuItem('خروج', self._on_exit),
        )

    # --- Handlerها ---

    def _on_start(self, icon=None, item=None):
        if self.app:
            self.app.start_monitoring()
        self.set_status("فعال", COLOR_ACTIVE)

    def _on_stop(self, icon=None, item=None):
        if self.app:
            self.app.stop_monitoring()
        self.set_status("غیرفعال", COLOR_IDLE)

    def _on_settings(self, icon=None, item=None):
        print("[Tray] تنظیمات (به زودی)")
        # TODO: باز کردن پنجره تنظیمات

    def _on_stats(self, icon=None, item=None):
        print("[Tray] آمار:")
        if self.app and hasattr(self.app, "get_stats"):
            stats = self.app.get_stats()
            for k, v in stats.items():
                print(f"  {k}: {v}")

    def _on_exit(self, icon=None, item=None):
        print("[Tray] خروج...")
        if self.app:
            self.app.stop_monitoring()
        if self.icon:
            self.icon.stop()

    # --- تغییر وضعیت ---

    def set_status(self, text, color):
        """تغییر وضعیت و رنگ آیکون."""
        self._status_text = text
        if color != self._current_color:
            self._current_color = color
            try:
                self.icon_image = create_icon_image(color)
                if self.icon:
                    self.icon.icon = self.icon_image
            except Exception as e:
                print(f"[Tray] خطا در تغییر آیکون: {e}")

        # به‌روزرسانی منو
        try:
            if self.icon:
                self.icon.update_menu()
        except Exception:
            pass

    # --- اجرا ---

    def run(self):
        """اجرای آیکون tray (blocking)."""
        self.icon = Icon(
            name="SmartKeyboard",
            icon=self.icon_image,
            title="Smart Keyboard",
            menu=self._build_menu(),
        )
        print("[Tray] آیکون tray اجرا شد.")
        self.icon.run()

    def run_detached(self):
        """اجرای آیکون tray توی یه ترد جدا (non-blocking)."""
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def stop(self):
        """توقف آیکون tray."""
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass


if __name__ == "__main__":
    print("تست tray (آیکون کنار ساعت ویندوز ظاهر میشه)...")
    print("روی آیکون راست‌کلیک کن و 'خروج' رو بزن تا بسته بشه.")

    tray = TrayIcon()
    tray.run()