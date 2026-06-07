@echo off
echo Installing build dependencies...
pip install ".[build]" pillow

echo Building MemBoard...
pyinstaller memboard.spec --clean --noconfirm

echo.
echo Done. Distributable is in dist\MemBoard\
echo Copy the entire dist\MemBoard\ folder to share the app.
pause
