@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

REM ========================================================
REM   PEGA 指令通 - 啟動器
REM   此腳本會呼叫 Python 版的打包系統 (build_final.py)
REM   確保路徑正確、資源完整、且解決 SSH 崩潰問題。
REM ========================================================

echo.
echo [INFO] 正在啟動 Python 打包系統...
echo.

REM 檢查 Python 是否安裝
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 找不到 Python！請確認已安裝 Python 並加入環境變數。
    pause
    exit /b
)

REM 呼叫 build_final.py (位於同一目錄)
REM 使用 %~dp0 確保路徑正群
python "%~dp0build_final.py"

echo.
if %errorlevel% neq 0 (
    echo [ERROR] 打包過程發生錯誤。
) else (
    echo [SUCCESS] 打包腳本執行完畢。
)
echo.
pause
