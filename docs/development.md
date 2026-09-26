# راهنمای توسعه

## ساختار پروژه

smart-keyboard-v2/
├── main.py
├── smartkeyboard/
│   ├── config.py
│   ├── languages.py
│   ├── converter.py
│   ├── dictionary.py
│   ├── detector.py
│   ├── learner.py
│   ├── popup.py
│   ├── tray.py
│   ├── settings_ui.py
│   └── data/
├── tests/
├── docs/
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── build.bat

## معماری

مراحل کار:

۱. کاربر تایپ می‌کنه
۲. keyboard hook کاراکترها رو جمع می‌کنه
۳. تایمر ۱ ثانیه‌ای صبر می‌کنه
۴. detector تشخیص می‌ده که تبدیل لازمه یا نه
۵. converter متن رو تبدیل می‌کنه
۶. dictionary چک می‌کنه که متن معنی‌داره یا نه
۷. تصمیم نهایی:
   - auto: تبدیل خودکار
   - suggest: پاپ‌آپ پیشنهاد
   - keep: هیچ کاری
۸. learner از نتیجه یاد می‌گیره

## ماژول‌ها

### config.py
مدیریت تنظیمات. از config.json می‌خونه و ذخیره می‌کنه.

### languages.py
تعریف زبان‌ها و layoutها. نقشه‌های تبدیل EN_TO_FA و FA_TO_EN.

### converter.py
تبدیل متن بین زبان‌ها. حفظ حالت حروف مثل lower و upper و title.

### dictionary.py
دیکشنری چندلایه. بارگذاری از فایل‌ها، ذخیره کلمات کاربر.

### detector.py
قلب پروژه. الگوریتم تشخیص با امتیازدهی:
- ۳۰ درصد امتیاز کلمه‌ای
- ۲۰ درصد امتیاز حرفی
- ۵۰ درصد امتیاز آماری

### learner.py
یادگیری از کاربر. رویدادهای accept و reject و learn.

### popup.py
حباب شناور با Tkinter. سه دکمه: جایگزین، رد، یاد بگیر.

### tray.py
آیکون system tray با pystray.

### settings_ui.py
پنجره تنظیمات گرافیکی با ۴ تب.

## اضافه کردن زبان جدید

مرحله ۱: توی languages.py یه ورودی جدید به LANGUAGES اضافه کن.

مرحله ۲: نقشه تبدیل EN_TO_XX و XX_TO_EN رو بساز.

مرحله ۳: فایل data/xx_words.txt رو بساز.

مرحله ۴: تست بنویس.

## تست

اجرای همه تست‌ها:

pytest

اجرای یه فایل خاص:

pytest tests/test_detector.py

با coverage:

pytest --cov=smartkeyboard

## فرمت کردن کد

black smartkeyboard/
flake8 smartkeyboard/

## Build

ویندوز:

build.bat

لینوکس یا مک:

chmod +x build.sh
./build.sh

## انتشار نسخه جدید

۱. CHANGELOG.md رو به‌روز کن.
۲. pyproject.toml رو آپدیت کن.
۳. smartkeyboard/__init__.py رو آپدیت کن.
۴. کامیت کن با پیام chore: bump version to X.Y.Z
۵. تگ بزن: git tag vX.Y.Z
۶. تگ رو push کن: git push origin vX.Y.Z
۷. توی گیت‌هاب، یه Release جدید بساز.