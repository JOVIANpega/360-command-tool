@echo off
echo VALO360 指令通 - 打包測試腳本
echo.

rem 檢查是否存在打包後的執行檔
if not exist "dist\main.exe" (
  echo 錯誤: 找不到打包後的執行檔 dist\main.exe
  echo 請先執行 build.bat 打包應用程序
  goto end
)

echo 找到打包後的執行檔 dist\main.exe
echo.

echo 檢查必要的檔案和目錄...
if not exist "dist\command.txt" (
  echo 警告: 找不到 dist\command.txt 檔案
) else (
  echo 找到 dist\command.txt 檔案
)

if not exist "dist\setup.json" (
  echo 警告: 找不到 dist\setup.json 檔案
) else (
  echo 找到 dist\setup.json 檔案
)

if not exist "dist\user_guide.txt" (
  echo 警告: 找不到 dist\user_guide.txt 檔案
) else (
  echo 找到 dist\user_guide.txt 檔案
)

if not exist "dist\app.ico" (
  echo 警告: 找不到 dist\app.ico 檔案
) else (
  echo 找到 dist\app.ico 檔案
)

if not exist "dist\FIXTURE" (
  echo 警告: 找不到 dist\FIXTURE 目錄
) else (
  echo 找到 dist\FIXTURE 目錄
)

if not exist "dist\ui_parts" (
  echo 警告: 找不到 dist\ui_parts 目錄
) else (
  echo 找到 dist\ui_parts 目錄
)

echo.
echo 所有檢查完成，準備啟動應用程序...
echo.

echo 啟動應用程序...
start "" "dist\main.exe"

echo.
echo 應用程序已啟動，請檢查下拉列表是否正常顯示
echo.

:end
pause 