@echo off
chcp 65001 > nul
echo.
echo ========================================
echo    PEGA指令通 V2.0.2 打包程序
echo ========================================
echo.

rem 檢查Python環境
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 未找到Python，請先安裝Python
    pause
    exit /b 1
)

rem 檢查PyInstaller
python -c "import PyInstaller" > nul 2>&1
if %errorlevel% neq 0 (
    echo [安裝] 正在安裝PyInstaller...
    pip install pyinstaller
)

rem 生成版本信息
echo [步驟1] 生成版本信息...
python version_info_zh.py
if %errorlevel% neq 0 (
    echo [錯誤] 版本信息生成失敗
    pause
    exit /b 1
)

rem 檢查必要文件
echo [步驟2] 檢查必要文件...
if not exist "main.py" (
    echo [錯誤] 找不到main.py
    pause
    exit /b 1
)

if not exist "setup.json" (
    echo [錯誤] 找不到setup.json
    pause
    exit /b 1
)

if not exist "tooltips.ini" (
    echo [錯誤] 找不到tooltips.ini
    pause
    exit /b 1
)

rem 創建assets目錄（如果不存在）
if not exist "assets" mkdir assets

rem 清理舊文件
echo [步驟3] 清理舊文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

rem 開始打包
echo [步驟4] 開始打包...
echo.

pyinstaller ^
    --onefile ^
    --clean ^
    --noconfirm ^
    --noconsole ^
    --name "PEGA指令通_V2.0.2" ^
    --version-file "version_info_zh.txt" ^
    --add-data "tooltips.ini;." ^
    --add-data "setup.json;." ^
    --add-data "command.txt;." ^
    --add-data "color_word.txt;." ^
    --add-data "tooltip_config.txt;." ^
    --add-data "user_guide.txt;." ^
    --add-data "PEGA指令通使用指南.html;." ^
    --add-data "readROVO.txt;." ^
    --add-data "sign_DOC.txt;." ^
    --add-data "Command_TABLE;Command_TABLE" ^
    --add-data "FIXTURE;FIXTURE" ^
    --add-data "core;core" ^
    --add-data "ui_parts;ui_parts" ^
    --add-data "assets;assets" ^
    --icon "assets/app.ico" ^
    main.py

rem 檢查結果
echo.
if exist "dist\PEGA指令通_V2.0.2.exe" (
    echo ========================================
    echo           打包成功！
    echo ========================================
    echo.
    echo 輸出文件: dist\PEGA指令通_V2.0.2.exe
    dir "dist\PEGA指令通_V2.0.2.exe"
    echo.
    echo [步驟5] 複製必要的執行時檔案到 dist ...
    if not exist "dist\assets" mkdir "dist\assets"
    if not exist "dist\Command_TABLE" mkdir "dist\Command_TABLE"
    if not exist "dist\FIXTURE" mkdir "dist\FIXTURE"
    if not exist "dist\core" mkdir "dist\core"
    if not exist "dist\ui_parts" mkdir "dist\ui_parts"
    
    rem 複製資料夾（包含子資料夾與檔案）
    xcopy /E /I /Y "assets" "dist\assets\" > nul
    xcopy /E /I /Y "Command_TABLE" "dist\Command_TABLE\" > nul
    xcopy /E /I /Y "FIXTURE" "dist\FIXTURE\" > nul
    xcopy /E /I /Y "core" "dist\core\" > nul
    xcopy /E /I /Y "ui_parts" "dist\ui_parts\" > nul
    
    rem 複製單一檔案
    copy /Y "setup.json" "dist\" > nul
    copy /Y "tooltips.ini" "dist\" > nul
    copy /Y "tooltip_config.txt" "dist\" > nul
    copy /Y "color_word.txt" "dist\" > nul
    copy /Y "command.txt" "dist\" > nul
    copy /Y "user_guide.txt" "dist\" > nul
    copy /Y "PEGA指令通使用指南.html" "dist\" > nul
    copy /Y "readROVO.txt" "dist\" > nul
    copy /Y "sign_DOC.txt" "dist\" > nul
    
    echo 複製完成。列出 dist 目錄：
    dir "dist"
    echo.
    echo 打包完成！您可以在dist目錄找到可執行文件。
) else (
    echo ========================================
    echo           打包失敗！
    echo ========================================
    echo 請檢查上方的錯誤信息
)

echo.
pause