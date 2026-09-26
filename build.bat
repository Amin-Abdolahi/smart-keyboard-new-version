@echo off
REM build.bat - ساخت فایل اجرایی Smart Keyboard برای ویندوز
REM استفاده: build.bat

setlocal

echo ============================================
echo   Smart Keyboard - Build Script
echo ============================================
echo.

REM بررسی وجود پوشه .venv
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment یافت نشد.
    echo لطفا اول این دستور رو بزن:
    echo   python -m venv .venv
    exit /b 1
)

REM فعال کردن venv
echo [1/5] فعال کردن virtual environment...
call .venv\Scripts\activate.bat

REM بررسی نصب pyinstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [2/5] نصب pyinstaller...
    pip install pyinstaller
) else (
    echo [2/5] pyinstaller نصب شده است.
)

REM ساخت آیکون اگه وجود نداره
if not exist "smart-keyboard-icon.ico" (
    echo [3/5] ساخت آیکون...
    python -c "from PIL import Image; img = Image.new('RGB', (256, 256), color=(0, 120, 215)); img.save('smart-keyboard-icon.ico', format='ICO', sizes=[(256, 256), (64, 64), (32, 32), (16, 16)])"
) else (
    echo [3/5] آیکون موجود است.
)

REM پاک کردن build قبلی
echo [4/5] پاک کردن build قبلی...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM build
echo [5/5] ساخت فایل اجرایی...
pyinstaller --onefile --windowed ^
    --name SmartKeyboard ^
    --icon smart-keyboard-icon.ico ^
    --add-data "smartkeyboard/data;smartkeyboard/data" ^
    --hidden-import keyboard ^
    --hidden-import pynput.keyboard._win32 ^
    --hidden-import pynput.mouse._win32 ^
    --hidden-import pyperclip ^
    --collect-all pystray ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build با خطا مواجه شد.
    exit /b 1
)

echo.
echo ============================================
echo   Build با موفقیت انجام شد!
echo   خروجی: dist\SmartKeyboard.exe
echo ============================================
echo.

endlocal
pause