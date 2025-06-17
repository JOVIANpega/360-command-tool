@echo off
echo 正在打包 VALO360指令通 V1.35...
pyinstaller --onefile --clean --noconfirm --icon=app.ico -w --version-file=version_info.txt --add-data "command.txt;." --add-data "user_guide.txt;." --add-data "setup.json;." --add-data "ui_parts;ui_parts" --name "VALO360指令通" main.py
echo 打包完成，產生檔案位於 dist/VALO360指令通.exe
pause 