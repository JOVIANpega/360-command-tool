@echo off
echo VALO360 指令通 - 版本資訊修正腳本
echo.

rem 執行修正腳本
python fix_version.py

rem 檢查打包結果
if exist "dist\VALO360指令通.exe" (
  echo.
  echo 打包成功，正在啟動程式...
  start "" "dist\VALO360指令通.exe"
) else (
  echo.
  echo 打包失敗，請檢查錯誤訊息。
)

echo.
echo 完成
pause 