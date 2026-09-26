# راهنمای مشارکت

از اینکه می‌خوای به این پروژه کمک کنی، ممنون! 🎉

## 🐛 گزارش باگ

اگه باگی پیدا کردی، لطفاً یه [Issue](https://github.com/Amin-Abdolahi/smart-keyboard-new-version/issues) باز کن با این اطلاعات:

* **توضیح باگ**: چه اتفاقی افتاد؟
* **انتظار**: چه اتفاقی باید می‌افتاد؟
* **مراحل بازتولید**: چطور می‌تونیم باگ رو ببینیم؟
* **محیط**: ویندوز/لینوکس/مک، نسخه پایتون
* **اسکرین‌شات**: اگه ممکنه

## 💡 پیشنهاد ویژگی

برای پیشنهاد ویژگی جدید، یه [Issue](https://github.com/Amin-Abdolahi/smart-keyboard-new-version/issues) باز کن با:

* **توضیح ویژگی**: چی می‌خوای؟
* **چرا مفیده**: چه مشکلی رو حل می‌کنه؟
* **مثال**: اگه ممکنه

## 🔧 مشارکت در کد

### راه‌اندازی محیط توسعه

```bash
git clone https://github.com/Amin-Abdolahi/smart-keyboard-new-version.git
cd smart-keyboard-new-version

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### ساختار پروژه

```text
smartkeyboard/
├── config.py
├── languages.py
├── converter.py
├── dictionary.py
├── detector.py
├── learner.py
├── popup.py
├── tray.py
└── settings_ui.py
```

### مراحل مشارکت

1. **Fork** کن.

2. یه **Branch** جدید بساز:

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. تغییرات رو اعمال کن.

4. **تست‌ها** رو اجرا کن:

   ```bash
   pytest
   ```

5. **کد رو فرمت کن**:

   ```bash
   black smartkeyboard/
   ```

6. **کامیت** کن:

   ```bash
   git commit -m "feat: add your feature"
   ```

7. **Push** کن:

   ```bash
   git push origin feature/your-feature-name
   ```

8. یه **Pull Request** باز کن.

### استاندارد کد

* از **PEP 8** پیروی کن.
* از **type hints** استفاده کن.
* برای توابع **docstring** بنویس.
* کد رو با `black` فرمت کن.
* تست‌ها رو با `pytest` بنویس.

### پیام‌های کامیت

از [Conventional Commits](https://www.conventionalcommits.org/) استفاده کن:

* `feat:` ویژگی جدید
* `fix:` رفع باگ
* `docs:` تغییرات مستندات
* `test:` تغییرات تست
* `chore:` کارهای نگهداری
* `refactor:` بازسازی کد
* `style:` تغییرات ظاهری

مثال:

```text
feat: add support for Arabic language
fix: resolve popup focus issue
docs: update README with screenshots
```

## 📚 اضافه کردن کلمات به دیکشنری

ساده‌ترین راه مشارکت! کافیه کلمات جدید رو به این فایل‌ها اضافه کنی:

* `smartkeyboard/data/fa_words.txt` - کلمات فارسی
* `smartkeyboard/data/en_words.txt` - کلمات انگلیسی
* `smartkeyboard/data/whitelist.txt` - اصطلاحات فنی

هر کلمه توی یه خط جدا. بعد یه PR بده.

## 🌍 اضافه کردن زبان جدید

برای اضافه کردن زبان جدید:

1. توی `smartkeyboard/languages.py` یه ورودی جدید به `LANGUAGES` اضافه کن.
2. نقشه تبدیل `XX_TO_EN` و `EN_TO_XX` رو بساز.
3. فایل کلمات `XX_words.txt` رو توی `smartkeyboard/data/` بساز.
4. تست بنویس.

## ❓ سوال

اگه سوالی داری، یه [Issue](https://github.com/Amin-Abdolahi/smart-keyboard-new-version/issues) باز کن.

**ممنون از مشارکتت! ❤️**
