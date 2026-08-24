@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
pyinstaller --noconfirm --clean PrincipaisCapas.spec
if errorlevel 1 pause
