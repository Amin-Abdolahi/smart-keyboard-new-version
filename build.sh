#!/bin/bash
# build.sh - ساخت فایل اجرایی Smart Keyboard برای لینوکس/مک
# استفاده: chmod +x build.sh && ./build.sh

set -e

echo "============================================"
echo "   Smart Keyboard - Build Script"
echo "============================================"
echo ""

# بررسی وجود پوشه .venv
if [ ! -f ".venv/bin/activate" ]; then
    echo "[ERROR] Virtual environment یافت نشد."
    echo "لطفا اول این دستور رو بزن:"
    echo "  python3 -m venv .venv"
    exit 1
fi

# فعال کردن venv
echo "[1/5] فعال کردن virtual environment..."
source .venv/bin/activate

# بررسی نصب pyinstaller
if ! pip show pyinstaller > /dev/null 2>&1; then
    echo "[2/5] نصب pyinstaller..."
    pip install pyinstaller
else
    echo "[2/5] pyinstaller نصب شده است."
fi

# ساخت آیکون اگه وجود نداره
if [ ! -f "smart-keyboard-icon.ico" ]; then
    echo "[3/5] ساخت آیکون..."
    python -c "from PIL import Image; img = Image.new('RGB', (256, 256), color=(0, 120, 215)); img.save('smart-keyboard-icon.ico', format='ICO', sizes=[(256, 256), (64, 64), (32, 32), (16, 16)])"
else
    echo "[3/5] آیکون موجود است."
fi

# پاک کردن build قبلی
echo "[4/5] پاک کردن build قبلی..."
rm -rf build dist

# build
echo "[5/5] ساخت فایل اجرایی..."
pyinstaller --onefile --windowed \
    --name SmartKeyboard \
    --icon smart-keyboard-icon.ico \
    --add-data "smartkeyboard/data:smartkeyboard/data" \
    --hidden-import keyboard \
    --hidden-import pynput.keyboard._win32 \
    --hidden-import pynput.mouse._win32 \
    --hidden-import pyperclip \
    --collect-all pystray \
    main.py

echo ""
echo "============================================"
echo "   Build با موفقیت انجام شد!"
echo "   خروجی: dist/SmartKeyboard"
echo "============================================"
echo ""