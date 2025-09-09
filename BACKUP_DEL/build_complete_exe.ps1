# PEGA指令通 V1.9.5 完整打包腳本 (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PEGA指令通 V1.9.5 完整打包腳本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 清理舊的打包檔案
Write-Host "清理舊的打包檔案..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "*.spec") { Remove-Item "*.spec" -Force }

Write-Host ""
Write-Host "開始打包 EXE..." -ForegroundColor Green
Write-Host ""

# 執行打包指令
pyinstaller --onefile `
    --noconsole `
    --icon=assets/icon.ico `
    --add-data "assets/icon.ico;assets" `
    --add-data "tooltips.ini;." `
    --add-data "Command_TABLE;Command_TABLE" `
    --add-data "setup.json;." `
    --add-data "user_guide.txt;." `
    --add-data "color_word.txt;." `
    --add-data "command.txt;." `
    --add-data "readROVO.txt;." `
    --add-data "config_utils.py;." `
    --add-data "serial_worker.py;." `
    --add-data "adb_worker.py;." `
    --add-data "core;core" `
    --add-data "ui_parts;ui_parts" `
    --hidden-import tkinter `
    --hidden-import tkinter.ttk `
    --hidden-import tkinter.messagebox `
    --hidden-import tkinter.filedialog `
    --hidden-import serial `
    --hidden-import threading `
    --hidden-import json `
    --hidden-import os `
    --hidden-import sys `
    --hidden-import re `
    --hidden-import datetime `
    --hidden-import logging `
    --name "PEGA指令通_V1.9.5" `
    main.py

Write-Host ""
Write-Host "打包完成！" -ForegroundColor Green
Write-Host ""

# 檢查打包結果
Write-Host "檢查打包結果..." -ForegroundColor Yellow
if (Test-Path "dist\PEGA指令通_V1.9.5.exe") {
    Write-Host "✅ 打包成功！" -ForegroundColor Green
    Write-Host "📁 EXE 檔案位置: dist\PEGA指令通_V1.9.5.exe" -ForegroundColor Cyan
    
    $fileInfo = Get-Item "dist\PEGA指令通_V1.9.5.exe"
    $sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
    Write-Host "📊 檔案大小: $sizeMB MB" -ForegroundColor Cyan
} else {
    Write-Host "❌ 打包失敗！" -ForegroundColor Red
}

Write-Host ""
Write-Host "按任意鍵結束..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 