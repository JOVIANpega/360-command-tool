@echo off
chcp 65001 > nul
echo.
echo ========================================
echo    PEGA指令工具V1.9.4 打包程序
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
    --name "PEGA指令工具V1.9.4" ^
    --version-file "version_info_zh.txt" ^
    --add-data "tooltips.ini;." ^
    --add-data "setup.json;." ^
    --add-data "command.txt;." ^
    --add-data "color_word.txt;." ^
    --add-data "tooltip_config.txt;." ^
    --add-data "user_guide.txt;." ^
    --add-data "Command_TABLE;Command_TABLE" ^
    --add-data "FIXTURE;FIXTURE" ^
    --add-data "core;core" ^
    --add-data "ui_parts;ui_parts" ^
    --add-data "assets;assets" ^
    --icon "assets/app.ico" ^
    main.py

rem 檢查結果
echo.
if exist "dist\PEGA指令工具V1.9.4.exe" (
    echo ========================================
    echo           打包成功！
    echo ========================================
    echo.
    echo 輸出文件: dist\PEGA指令工具V1.9.4.exe
    dir "dist\PEGA指令工具V1.9.4.exe"
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