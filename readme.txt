
pyinstaller --noconfirm --onefile --windowed --icon=app.ico --add-data "ui_parts;ui_parts" --add-data "command.txt;." --add-data "setup.json;." --add-data "user_guide.txt;." --add-data "FIXTURE;FIXTURE" --add-data "VALO360 指令通使用指南.html;." --add-data "VALO360 指令通使用指南_files;VALO360 指令通使用指南_files" main.py


pyinstaller --noconfirm --onefile --windowed --icon=app.ico --add-data "ui_parts;ui_parts" --add-data "command.txt;." --add-data "setup.json;." --add-data "user_guide.txt;." --add-data "FIXTURE;FIXTURE" --add-data "VALO360 指令通使用指南.html;." main.py


git status

cd "D:\((Python TOOL\指令工具-20250428T020034Z-001\V1.12"

git log --oneline -5