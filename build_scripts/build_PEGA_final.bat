@echo off
chcp 65001 > nul

rem 切換到專案根目錄
cd /d "%~dp0.."

rem 讀取版本號從 setup.json
echo [初始化] 讀取版本號...
for /f "delims=" %%i in ('python build_scripts\get_version.py') do set APP_VERSION=%%i
if "%APP_VERSION%"=="" (
    echo [警告] 無法讀取版本號，使用預設值 2.5.4
    set APP_VERSION=2.5.4
)

echo.
echo ========================================
echo    PEGA指令通 V%APP_VERSION% 打包程序
echo ========================================
echo.

rem 生成版本信息
echo [步驟1] 生成版本信息...
python build_scripts\version_info_zh.py
if %errorlevel% neq 0 (
    echo [錯誤] 版本信息生成失敗
    pause
    exit /b 1
)

rem 檢查必要文件
echo [步驟2] 檢查必要文件...
if not exist "MAIN.PY" echo [錯誤] 找不到MAIN.PY && pause && exit /b 1
if not exist "setup.json" echo [錯誤] 找不到setup.json && pause && exit /b 1
if not exist "docs\PEGA指令通使用指南.html" echo [錯誤] 找不到使用指南 && pause && exit /b 1

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
    --name "PEGA指令通_V%APP_VERSION%" ^
    --version-file "version_info_zh.txt" ^
    --add-data "tooltips.ini;." ^
    --add-data "setup.json;." ^
    --add-data "command.txt;." ^
    --add-data "color_word.txt;." ^
    --add-data "tooltip_config.txt;." ^
    --add-data "user_guide.txt;." ^
    --add-data "readROVO.txt;." ^
    --add-data "sign_DOC.txt;." ^
    --add-data "Command_TABLE;Command_TABLE" ^
    --add-data "FIXTURE;FIXTURE" ^
    --add-data "core;core" ^
    --add-data "ui_parts;ui_parts" ^
    --add-data "transport;transport" ^
    --add-data "assets;assets" ^
    --add-data "docs\PEGA指令通使用指南.html;." ^
    --add-data "docs\VALO360_guide_files;VALO360_guide_files" ^
    --icon "assets/icon.ico" ^
    MAIN.PY

rem 檢查結果
echo.
if exist "dist\PEGA指令通_V%APP_VERSION%.exe" (
    echo ========================================
    echo           打包成功！
    echo ========================================
    echo.
    
    echo [步驟5] 複製必要的執行時檔案到 dist ...
    xcopy /E /I /Y "assets" "dist\assets\" > nul
    xcopy /E /I /Y "Command_TABLE" "dist\Command_TABLE\" > nul
    xcopy /E /I /Y "FIXTURE" "dist\FIXTURE\" > nul
    xcopy /E /I /Y "core" "dist\core\" > nul
    xcopy /E /I /Y "ui_parts" "dist\ui_parts\" > nul
    xcopy /E /I /Y "transport" "dist\transport\" > nul
    xcopy /E /I /Y "docs\VALO360_guide_files" "dist\VALO360_guide_files\" > nul
    
    copy /Y "setup.json" "dist\" > nul
    copy /Y "tooltips.ini" "dist\" > nul
    copy /Y "tooltip_config.txt" "dist\" > nul
    copy /Y "color_word.txt" "dist\" > nul
    copy /Y "command.txt" "dist\" > nul
    copy /Y "user_guide.txt" "dist\" > nul
    copy /Y "docs\PEGA指令通使用指南.html" "dist\" > nul
    copy /Y "readROVO.txt" "dist\" > nul
    copy /Y "sign_DOC.txt" "dist\" > nul
    
    echo 打包完成！您可以在dist目錄找到可執行文件。
) else (
    echo 打包失敗！
)
pause