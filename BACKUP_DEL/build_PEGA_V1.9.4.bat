@echo off
chcp 65001 > nul
echo PEGA指令工具V1.9.4 - 打包脚本
echo.

rem 檢查Python環境
python --version > nul 2>&1
if %errorlevel% neq 0 (
  echo 錯誤: 未安裝Python或Python不在系統路徑中
  goto end
)

rem 檢查PyInstaller
python -c "import PyInstaller" > nul 2>&1
if %errorlevel% neq 0 (
  echo 正在安裝 PyInstaller...
  pip install pyinstaller
  if %errorlevel% neq 0 (
    echo 錯誤: 無法安裝 PyInstaller
    goto end
  )
)

rem 檢查必要的套件
echo 檢查必要套件...
python -c "import serial" > nul 2>&1
if %errorlevel% neq 0 (
  echo 正在安裝 PySerial...
  pip install pyserial
)

python -c "import psutil" > nul 2>&1
if %errorlevel% neq 0 (
  echo 正在安裝 psutil...
  pip install psutil
)

echo 所有依賴已準備就緒，開始打包...
echo.

rem 生成版本資訊檔案
echo 生成版本資訊檔案...
python version_info_zh.py

rem 清理舊的編譯檔案
echo 清理舊的編譯檔案...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

rem 檢查必要檔案
if not exist "assets\app.ico" (
  echo 警告: 找不到圖示檔案 assets\app.ico
  echo 請確認圖示檔案存在
)

if not exist "tooltips.ini" (
  echo 警告: 找不到 tooltips.ini 配置檔案
)

if not exist "setup.json" (
  echo 警告: 找不到 setup.json 配置檔案
)

rem 開始打包
echo 開始打包程式...
pyinstaller PEGA指令工具V1.9.4.spec --clean --noconfirm

rem 檢查打包結果
if exist "dist\PEGA指令工具V1.9.4.exe" (
  echo.
  echo ✓ 建置成功! 
  echo ✓ 輸出檔案: dist\PEGA指令工具V1.9.4.exe
  echo.
  
  rem 顯示檔案資訊
  echo 檔案資訊:
  dir "dist\PEGA指令工具V1.9.4.exe"
  
  rem 創建必要的目錄結構
  if not exist "dist\backup" mkdir "dist\backup"
  if not exist "dist\logs" mkdir "dist\logs"
  
  echo.
  echo 打包完成! 可執行檔案位於: dist\PEGA指令工具V1.9.4.exe
) else (
  echo.
  echo ✗ 建置失敗，請檢查錯誤訊息
)

:end
echo.
pause