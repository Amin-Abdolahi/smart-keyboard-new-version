# Smart Keyboard

تشخیص و تبدیل خودکار layout فارسی/انگلیسی در لحظه تایپ.

## ویژگی‌ها

- تشخیص خودکار اشتباه layout
- حباب شناور
- دیکشنری چندلایه و قابل توسعه
- یادگیری از کاربر
- پشتیبانی از چند زبان (فارسی، انگلیسی، آلمانی)
- تغییر خودکار layout بعد از تبدیل
- کلید میانبر Ctrl+Shift+F برای تبدیل دستی

## نصب

### روش ۱: دانلود فایل اجرایی

از صفحه Releases آخرین نسخه SmartKeyboard.exe رو دانلود کن.

### روش ۲: نصب از سورس

git clone https://github.com/Amin-Abdolahi/smart-keyboard-new-version.git
cd smart-keyboard-new-version
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py

## استفاده

۱. برنامه رو اجرا کن.
۲. آیکون آبی کنار ساعت ویندوز ظاهر می‌شه.
۳. روی آیکون راست‌کلیک کن و شروع نظارت رو بزن.
۴. حالا هر جا تایپ کنی، اگه layout اشتباه باشه، برنامه تشخیص می‌ده.

## مثال

layout: EN
تایپ: sghl phgj ]x,vi
نتیجه: سلام حالت چطوره

## مستندات

- نصب
- استفاده
- توسعه

## مشارکت

از مشارکت شما استقبال می‌کنیم. لطفا CONTRIBUTING.md رو بخون.

## لایسنس

این پروژه تحت لایسنس MIT منتشر شده.

## نویسنده

Amin Abdolahi
