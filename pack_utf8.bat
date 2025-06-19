@echo off
chcp 65001 > nul
echo VALO360 指令通 - UTF-8 打包腳本
echo.

rem 設置版本號
set VERSION=V1.38

rem 生成版本資訊檔案
echo 生成版本資訊檔案...
python version_info_zh.py

rem 確保 main_utf8.py 是 UTF-8 編碼
echo 確保 main_utf8.py 是 UTF-8 編碼...
powershell -Command "[System.IO.File]::ReadAllText('main_utf8.py') | Out-File -Encoding utf8 'main_utf8_fixed.py'"

rem 清理舊的編譯檔案 (使用安全的方式)
echo 清理舊的編譯檔案...
if exist "build" (
    rmdir /s /q "build" 2>nul
    if exist "build" echo 警告: 無法刪除 build 目錄
)

if exist "dist\VALO360指令通.exe" (
    echo 嘗試刪除舊的 EXE 檔案...
    del /f /q "dist\VALO360指令通.exe" 2>nul
    if exist "dist\VALO360指令通.exe" echo 警告: 無法刪除舊的 EXE 檔案，可能正在使用中
)

if exist "*.spec" (
    del /f /q "*.spec" 2>nul
)

rem 使用新的輸出目錄
set OUTPUT_DIR=dist_new
if exist "%OUTPUT_DIR%" rmdir /s /q "%OUTPUT_DIR%" 2>nul
mkdir "%OUTPUT_DIR%"

rem 開始打包
echo 開始打包程式...
pyinstaller --onefile --noconsole --icon=app.ico --version-file=version_info_zh.txt --add-data "command.txt;." --add-data "user_guide.txt;." --add-data "setup.json;." --add-data "app.ico;." --distpath "%OUTPUT_DIR%" main_utf8_fixed.py --name "VALO360指令通"

rem 檢查打包結果
if %ERRORLEVEL% NEQ 0 (
    echo 打包失敗，錯誤碼: %ERRORLEVEL%
    goto end
)

rem 創建必要的目錄
echo 創建必要的目錄...
mkdir "%OUTPUT_DIR%\backup" 2>nul
mkdir "%OUTPUT_DIR%\logs" 2>nul

echo.
echo 打包成功! 輸出檔案位於 %OUTPUT_DIR%\VALO360指令通.exe
echo.

:end
pause 