@echo off
chcp 65001 >nul
echo ========================================
echo PEGA指令通 V1.9.5 完整打包腳本
echo ========================================
echo.

echo 清理舊的打包檔案...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del "*.spec"

echo.
echo 開始打包 EXE...
echo.

pyinstaller --onefile ^
    --noconsole ^
    --icon=assets/icon.ico ^
    --add-data "assets/icon.ico;assets" ^
    --add-data "tooltips.ini;." ^
    --add-data "Command_TABLE;Command_TABLE" ^
    --add-data "setup.json;." ^
    --add-data "user_guide.txt;." ^
    --add-data "color_word.txt;." ^
    --add-data "command.txt;." ^
    --add-data "readROVO.txt;." ^
    --add-data "config_utils.py;." ^
    --add-data "serial_worker.py;." ^
    --add-data "adb_worker.py;." ^
    --add-data "core;core" ^
    --add-data "ui_parts;ui_parts" ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.messagebox ^
    --hidden-import tkinter.filedialog ^
    --hidden-import serial ^
    --hidden-import threading ^
    --hidden-import json ^
    --hidden-import os ^
    --hidden-import sys ^
    --hidden-import re ^
    --hidden-import datetime ^
    --hidden-import logging ^
    --name "PEGA指令通_V1.9.5" ^
    main.py

echo.
echo 打包完成！
echo.
echo 檢查打包結果...
if exist "dist\PEGA指令通_V1.9.5.exe" (
    echo ✅ 打包成功！
    echo 📁 EXE 檔案位置: dist\PEGA指令通_V1.9.5.exe
    echo 📊 檔案大小:
    dir "dist\PEGA指令通_V1.9.5.exe" | findstr "PEGA指令通_V1.9.5.exe"
) else (
    echo ❌ 打包失敗！
)

echo.
echo 按任意鍵結束...
pause >nul 