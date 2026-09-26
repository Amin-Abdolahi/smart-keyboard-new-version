# Smart Keyboard v2

<div align="center">

**تشخیص و تبدیل خودکار layout فارسی/انگلیسی در لحظه تایپ**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)]()

</div>

---

## ✨ ویژگی‌ها

- 🔍 **تشخیص خودکار**: تشخیص اشتباه layout در لحظه تایپ
- 💬 **حباب شناور**: نمایش پیشنهاد شبیه Grammarly
- 📚 **دیکشنری چندلایه**: فارسی، انگلیسی، محاوره‌ای
- 🧠 **یادگیری از کاربر**: دیکشنری خودش رو با سبک نوشتاری شما هماهنگ می‌کنه
- 🌐 **چندزبانه**: پشتیبانی از فارسی، انگلیسی، آلمانی و...
- ⌨️ **تغییر خودکار layout**: بعد از تبدیل، layout خودکار عوض میشه
- 🎯 **کلید میانبر**: `Ctrl+Shift+F` برای تبدیل دستی
- 🔒 **حریم خصوصی**: همه چیز محلی اجرا میشه، هیچ داده‌ای ارسال نمیشه

---

## 📸 اسکرین‌شات

*(به زودی)*

---

## 🚀 نصب

### روش ۱: دانلود فایل اجرایی

1.  از [Releases](https://github.com/YOUR_USERNAME/smart-keyboard/releases) آخرین نسخه رو دانلود کن.
2.  فایل `SmartKeyboard.exe` رو اجرا کن.
3.  تمومه!

### روش ۲: نصب از سورس

```bash
# کلون کردن
git clone https://github.com/YOUR_USERNAME/smart-keyboard.git
cd smart-keyboard

# ساخت virtual environment
python -m venv .venv
.venv\Scripts\activate  # ویندوز
# source .venv/bin/activate  # لینوکس/مک

# نصب وابستگی‌ها
pip install -r requirements.txt

# اجرا
python main.py
```

---

## 🎯 استفاده

1.  برنامه رو اجرا کن.
2.  آیکون **آبی** کنار ساعت ویندوز ظاهر میشه.
3.  روی آیکون راست‌کلیک کن → **شروع نظارت**.
4.  حالا هر جا تایپ کنی، اگه layout اشتباه باشه، برنامه تشخیص میده.

### مثال

فرض کن layout روی **انگلیسی** هست ولی میخوای فارسی تایپ کنی:

```
شما تایپ میکنی: sghl phgj ]x,vi
برنامه تبدیل میکنه: سلام حالت چطوره
```

### کلیدهای میانبر

| کلید | عملکرد |
|---|---|
| `Ctrl+Shift+F` | تبدیل دستی متن تایپ‌شده |
| `Escape` | بستن پاپ‌آپ |

---

## ⚙️ تنظیمات

از منوی tray → **تنظیمات** می‌تونی:

- **زبان‌ها**: زبان‌های فعال رو انتخاب کنی
- **تبدیل**: آستانه‌ها و زمان‌بندی رو تنظیم کنی
- **رابط کاربری**: حباب، صدا و...
- **دیکشنری**: آمار و مدیریت

---

## 🏗️ ساختار پروژه

```
smart-keyboard-v2/
├── main.py                    # نقطه ورود
├── requirements.txt
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── build.bat / build.sh
├── smartkeyboard/
│   ├── config.py              # مدیریت تنظیمات
│   ├── languages.py           # زبان‌ها و layoutها
│   ├── converter.py           # تبدیل متن
│   ├── dictionary.py          # دیکشنری چندلایه
│   ├── detector.py            # تشخیص اشتباه
│   ├── learner.py             # یادگیری
│   ├── popup.py               # حباب شناور
│   ├── tray.py                # آیکون tray
│   ├── settings_ui.py         # پنجره تنظیمات
│   └── data/
│       ├── fa_words.txt       # کلمات پایه فارسی
│       ├── en_words.txt       # کلمات پایه انگلیسی
│       └── whitelist.txt      # اصطلاحات فنی
└── user_data/                 # داده‌های شخصی (git-ignored)
```

---

## 🤝 مشارکت

از مشارکت شما استقبال می‌کنیم! لطفاً [CONTRIBUTING.md](CONTRIBUTING.md) رو بخون.

### اضافه کردن کلمات به دیکشنری

می‌تونی کلمات جدید رو به فایل‌های `smartkeyboard/data/fa_words.txt` و `smartkeyboard/data/en_words.txt` اضافه کنی و PR بدی.

---

## 📝 لایسنس

این پروژه تحت لایسنس [MIT](LICENSE) منتشر شده.

---

## 👨‍💻 نویسنده

**Amin Abdolahi**

- GitHub: [@YOUR_USERNAME](https://github.com/YOUR_USERNAME)

---

## 🙏 تشکر

- [pynput](https://github.com/moses-palmer/pynput) - برای مدیریت کیبورد
- [pystray](https://github.com/moses-palmer/pystray) - برای آیکون tray
- [Pillow](https://python-pillow.org/) - برای پردازش تصویر

---

<div align="center">

**⭐ اگه این پروژه برات مفید بود، یه ستاره بده!**

</div>