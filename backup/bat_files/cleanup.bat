@echo off
echo VALO360 指令通 - 清理腳本
echo.

echo 正在清理打包產生的臨時文件...

rem 刪除 PyInstaller 產生的臨時文件
if exist "build" (
    rmdir /s /q build
    echo 已刪除 build 目錄
)

if exist "__pycache__" (
    rmdir /s /q __pycache__
    echo 已刪除 __pycache__ 目錄
)

if exist "*.spec" (
    del *.spec
    echo 已刪除 .spec 文件
)

rem 刪除其他模組的 __pycache__
if exist "ui_parts\__pycache__" (
    rmdir /s /q ui_parts\__pycache__
    echo 已刪除 ui_parts\__pycache__ 目錄
)

if exist "FIXTURE\__pycache__" (
    rmdir /s /q FIXTURE\__pycache__
    echo 已刪除 FIXTURE\__pycache__ 目錄
)

echo.
echo 清理完成!
echo.

pause 