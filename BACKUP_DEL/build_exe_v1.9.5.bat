@echo off
chcp 65001 >nul
echo ========================================
echo VALO360 指令通 V1.9.5 打包腳本
echo ========================================
echo.

echo [1/5] 檢查環境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤：未找到Python，請先安裝Python 3.7+
    pause
    exit /b 1
)

echo ✅ Python環境檢查通過

echo.
echo [2/5] 檢查PyInstaller...
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
echo [3/5] 清理舊的打包檔案...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del "*.spec" 2>nul
echo ✅ 清理完成

echo.
echo [4/5] 開始打包...
echo 使用spec檔案：VALO360_V1.9.5.spec
pyinstaller --clean VALO360_V1.9.5.spec

if errorlevel 1 (
    echo ❌ 打包失敗！
    echo 請檢查錯誤訊息
    pause
    exit /b 1
)

echo.
echo [5/5] 打包完成！
echo.
echo 📁 輸出目錄：dist\
echo 📄 執行檔：VALO360指令通V1.9.5.exe
echo.
echo 📋 包含的檔案和資料夾：
echo   • assets\ (圖示和資源)
echo   • Command_TABLE\ (指令表格)
echo   • FIXTURE\ (治具相關)
echo   • logs\ (日誌目錄)
echo   • backup\ (備份目錄)
echo   • ui_parts\ (UI元件)
echo   • core\ (核心模組)
echo   • 所有配置檔案 (*.txt, *.json, *.ini, *.md)
echo.
echo 🎉 打包成功！V1.9.5版本已準備就緒
echo.
pause
