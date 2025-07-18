@echo off
echo VALO360 指令通 - 建置腳本 (UTF-8 版本)
echo.

rem 檢查依賴
echo 檢查依賴項...

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

rem 檢查psutil
python -c "import psutil" > nul 2>&1
if %errorlevel% neq 0 (
  echo 正在安裝 psutil...
  pip install psutil
  if %errorlevel% neq 0 (
    echo 錯誤: 無法安裝 psutil
    goto end
  )
)

rem 生成版本資訊檔案
echo 生成版本資訊檔案...
python version_info_zh.py

rem 清理舊的編譯檔案
echo 清理舊的編譯檔案...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /f /q "*.spec"

rem 開始打包
echo 開始打包程式...
pyinstaller --onefile --clean --noconfirm --icon=app.ico -w --version-file=version_info_zh.txt --add-data "command.txt;." --add-data "user_guide.txt;." --add-data "setup.json;." --add-data "app.ico;." --name "VALO360指令通" main_utf8.py

echo.
if %ERRORLEVEL% EQU 0 (
    echo 建置成功! 輸出檔案位於 dist/VALO360指令通.exe
) else (
    echo 建置失敗，錯誤碼: %ERRORLEVEL%
)

echo.
:end
pause 