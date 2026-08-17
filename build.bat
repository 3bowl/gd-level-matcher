@echo off
cd /d "%~dp0"
call .venv\Scripts\Activate
pyinstaller --clean --onefile --hidden-import=_cffi_backend src/Match.py
pause