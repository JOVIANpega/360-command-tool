@echo off
echo VALO360 指令通 - 打包腳本
echo.

rem 檢查Python環境
python --version > nul 2>&1
if %errorlevel% neq 0 (
  echo 錯誤: 未安裝Python或Python不在系統路徑中
  goto end
)

rem 檢查PyInstaller
python -c "import PyInstaller" > nul 2>&1
if %errorlevel% neq 0 (
  echo 正在安裝 PyInstaller...
  pip install pyinstaller
  if %errorlevel% neq 0 (
    echo 錯誤: 無法安裝 PyInstaller
    goto end
  )
)

rem 檢查PySerial
python -c "import serial" > nul 2>&1
if %errorlevel% neq 0 (
  echo 正在安裝 PySerial...
  pip install pyserial
  if %errorlevel% neq 0 (
    echo 錯誤: 無法安裝 PySerial
    goto end
  )
)

echo 所有依賴已準備就緒，開始打包...
echo.

rem 創建必要的目錄
if not exist "dist" mkdir dist
if not exist "dist\backup" mkdir dist\backup
if not exist "dist\logs" mkdir dist\logs

rem 更新主程式中的版本號
echo 更新 main.py 中的版本號...
powershell -Command "(Get-Content main.py) -replace 'VERSION = \"V1\.[0-9]+\"', 'VERSION = \"V1.38\"' | Set-Content main.py"

rem 打包應用程式
echo 開始打包應用程式...
pyinstaller --onefile --noconsole --icon=app.ico ^
    --version-file=version_info.txt ^
    --name="VALO360CommandTool" ^
    --add-data "command.txt;." ^
    --add-data "setup.json;." ^
    --add-data "user_guide.txt;." ^
    --add-data "app.ico;." ^
    main.py

rem 複製必要的檔案
echo 複製必要檔案到輸出目錄...
copy command.txt dist\
copy setup.json dist\
copy user_guide.txt dist\
copy app.ico dist\

echo.
echo 打包完成! 執行檔位於 dist\VALO360CommandTool.exe
echo.

:end
pause 