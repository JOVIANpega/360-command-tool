@echo off
echo Building VALO360 Command Tool...

REM Install dependencies if needed
python -c "import PyInstaller" 2>nul || pip install pyinstaller
python -c "import serial" 2>nul || pip install pyserial

REM Clean old files
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "main.spec" del "main.spec"
if exist "VALO360指令通.spec" del "VALO360指令通.spec"

REM Build with PyInstaller
pyinstaller --onefile --windowed --clean --noconfirm --name "VALO360指令通" --icon "assets/app.ico" --add-data "Command_TABLE;Command_TABLE" --add-data "FIXTURE;FIXTURE" --add-data "user_guide.txt;." --add-data "setup.json;." --add-data "assets;assets" --add-data "ui_parts;ui_parts" --add-data "command.txt;." --add-data "color_word.txt;." main.py

REM Create directories
if not exist "dist\backup" mkdir "dist\backup"
if not exist "dist\logs" mkdir "dist\logs"
if not exist "dist\Command_TABLE" mkdir "dist\Command_TABLE"
if not exist "dist\FIXTURE" mkdir "dist\FIXTURE"

REM Copy files
copy "command.txt" "dist\" 2>nul
copy "setup.json" "dist\" 2>nul
copy "user_guide.txt" "dist\" 2>nul
copy "color_word.txt" "dist\" 2>nul
copy "Command_TABLE\*.txt" "dist\Command_TABLE\" 2>nul
copy "FIXTURE\*.txt" "dist\FIXTURE\" 2>nul

echo Build complete! Check dist folder for VALO360指令通.exe
pause