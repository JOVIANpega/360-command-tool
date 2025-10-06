@echo off
chcp 65001 >nul
echo ========================================
echo VALO360 指令通 V1.9.5 完整打包腳本
echo ========================================
echo.

echo [1/6] 檢查環境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤：未找到Python，請先安裝Python 3.7+
    pause
    exit /b 1
)

echo ✅ Python環境檢查通過

echo.
echo [2/6] 檢查PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤：未找到PyInstaller，正在安裝...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ PyInstaller安裝失敗
        pause
        exit /b 1
    )
)

echo ✅ PyInstaller檢查通過

echo.
echo [3/6] 清理舊的打包檔案...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo ✅ 清理完成

echo.
echo [4/6] 檢查必要檔案...
if not exist "assets\icon.ico" (
    echo ❌ 錯誤：找不到圖示檔案 assets\icon.ico
    pause
    exit /b 1
)

if not exist "main.py" (
    echo ❌ 錯誤：找不到主程式 main.py
    pause
    exit /b 1
)

echo ✅ 必要檔案檢查通過

echo.
echo [5/6] 開始完整打包...
echo 包含所有檔案和資料夾...

pyinstaller --onefile ^
    --noconsole ^
    --icon=assets\icon.ico ^
    --name="VALO360指令通V1.9.5" ^
    --add-data "assets;assets" ^
    --add-data "Command_TABLE;Command_TABLE" ^
    --add-data "FIXTURE;FIXTURE" ^
    --add-data "logs;logs" ^
    --add-data "backup;backup" ^
    --add-data "ui_parts;ui_parts" ^
    --add-data "core;core" ^
    --add-data "*.txt;." ^
    --add-data "*.json;." ^
    --add-data "*.ini;." ^
    --add-data "*.md;." ^
    --add-data "*.html;." ^
    --add-data "*.bat;." ^
    --add-data "*.spec;." ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.scrolledtext ^
    --hidden-import tkinter.messagebox ^
    --hidden-import serial ^
    --hidden-import threading ^
    --hidden-import json ^
    --hidden-import logging ^
    --hidden-import traceback ^
    main.py

if errorlevel 1 (
    echo ❌ 打包失敗！
    echo 請檢查錯誤訊息
    pause
    exit /b 1
)

echo.
echo [6/6] 打包完成！檢查結果...
echo.

if exist "dist\VALO360指令通V1.9.5.exe" (
    echo ✅ 執行檔生成成功：dist\VALO360指令通V1.9.5.exe
    
    echo.
    echo 📋 檢查包含的檔案和資料夾：
    
    if exist "dist\assets" (
        echo ✅ assets\ (圖示和資源)
    ) else (
        echo ❌ assets\ 目錄缺失
    )
    
    if exist "dist\Command_TABLE" (
        echo ✅ Command_TABLE\ (指令表格)
    ) else (
        echo ❌ Command_TABLE\ 目錄缺失
    )
    
    if exist "dist\FIXTURE" (
        echo ✅ FIXTURE\ (治具相關)
    ) else (
        echo ❌ FIXTURE\ 目錄缺失
    )
    
    if exist "dist\logs" (
        echo ✅ logs\ (日誌目錄)
    ) else (
        echo ❌ logs\ 目錄缺失
    )
    
    if exist "dist\backup" (
        echo ✅ backup\ (備份目錄)
    ) else (
        echo ❌ backup\ 目錄缺失
    )
    
    if exist "dist\ui_parts" (
        echo ✅ ui_parts\ (UI元件)
    ) else (
        echo ❌ ui_parts\ 目錄缺失
    )
    
    if exist "dist\core" (
        echo ✅ core\ (核心模組)
    ) else (
        echo ❌ core\ 目錄缺失
    )
    
    echo.
    echo 📄 檢查配置檔案：
    
    if exist "dist\setup.json" (
        echo ✅ setup.json
    ) else (
        echo ❌ setup.json 缺失
    )
    
    if exist "dist\tooltips.ini" (
        echo ✅ tooltips.ini
    ) else (
        echo ❌ tooltips.ini 缺失
    )
    
    if exist "dist\*.txt" (
        echo ✅ *.txt 檔案
    ) else (
        echo ❌ *.txt 檔案缺失
    )
    
    echo.
    echo 🎉 打包完成！V1.9.5版本已準備就緒
    echo 📁 輸出目錄：dist\
    echo 📄 執行檔：VALO360指令通V1.9.5.exe
    
) else (
    echo ❌ 執行檔生成失敗！
)

echo.
pause
