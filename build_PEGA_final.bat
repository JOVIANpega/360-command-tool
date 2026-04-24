@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

REM ========================================================
REM   PEGA 指令通 - 啟動器 (根目錄版)
REM   此腳本會呼叫 build_scripts 內的打包系統 (build_final.py)
REM ========================================================

echo.
echo [INFO] 正在啟動 PEGA 打包系統...
echo.

REM 檢查 Python 是否安裝
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 找不到 Python！請確認已安裝 Python 並加入環境變數。
    pause
    exit /b
)

REM 呼叫 build_scripts/build_final.py
REM 使用 %~dp0 指向當前目錄 (根目錄) 的子目錄
python "%~dp0build_scripts\build_final.py"

echo.
if %errorlevel% neq 0 (
    echo [ERROR] 打包過程發生錯誤。
) else (
    echo [SUCCESS] 打包完成！請至 dist 目錄查看結果。
)
echo.
pause
