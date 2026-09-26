# راهنمای نصب

## پیش‌نیازها

- ویندوز ۱۰ یا بالاتر
- Python 3.10+ (اگه از سورس نصب می‌کنی)

## روش ۱: دانلود فایل اجرایی

1. برو به صفحه Releases.
2. آخرین نسخه SmartKeyboard.exe رو دانلود کن.
3. فایل رو توی یه پوشه دلخواه بذار.
4. دابل‌کلیک کن.

نکته: اگه آنتی‌ویروست به فایل گیر داد، یه استثنا اضافه کن.

## روش ۲: نصب از سورس

### ۱. کلون کردن

git clone https://github.com/Amin-Abdolahi/smart-keyboard-new-version.git
cd smart-keyboard-new-version

### ۲. ساخت virtual environment

python -m venv .venv

فعال کردن در ویندوز:

.venv\Scripts\activate

### ۳. نصب وابستگی‌ها

pip install -r requirements.txt

### ۴. اجرا

python main.py

## روش ۳: نصب به عنوان پکیج

pip install -e .
smart-keyboard

## رفع مشکلات

### آنتی‌ویروس فایل رو پاک می‌کنه

فایل SmartKeyboard.exe رو توی لیست استثناهای آنتی‌ویروس اضافه کن.

### برنامه کار نمی‌کنه

PowerShell رو Run as Administrator باز کن و برنامه رو از اونجا اجرا کن.

### ModuleNotFoundError

مطمئن شو virtual environment فعاله و وابستگی‌ها نصب شدن:

pip install -r requirements.txt