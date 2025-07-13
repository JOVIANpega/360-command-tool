@echo off
chcp 65001 > nul
echo VALO360 指令通 - 打包脚本 (V1.4.3.5)
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

echo 所有依賴已準備就緒，開始打包...
echo.

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
pyinstaller --onefile --clean --noconfirm --icon=assets/app.ico -w --version-file=version_info_zh.txt ^
  --add-data "Command_TABLE/command.txt;Command_TABLE" ^
  --add-data "FIXTURE/Fixture_Command.txt;FIXTURE" ^
  --add-data "user_guide.txt;." ^
  --add-data "setup.json;." ^
  --add-data "assets/app.ico;assets" ^
  --name "VALO360指令通" main.py

rem 創建必要的目錄
if not exist "dist\backup" mkdir dist\backup
if not exist "dist\logs" mkdir dist\logs
if not exist "dist\Command_TABLE" mkdir dist\Command_TABLE
if not exist "dist\FIXTURE" mkdir dist\FIXTURE

rem 複製必要的檔案
echo 複製必要檔案到輸出目錄...
copy Command_TABLE\command.txt dist\Command_TABLE\
copy FIXTURE\Fixture_Command.txt dist\FIXTURE\
copy setup.json dist\
copy user_guide.txt dist\

echo.
if %ERRORLEVEL% EQU 0 (
    echo 建置成功! 輸出檔案位於 dist/VALO360指令通.exe
) else (
    echo 建置失敗，錯誤碼: %ERRORLEVEL%
)

:end
echo.
pause 