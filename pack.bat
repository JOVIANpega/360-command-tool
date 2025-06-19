@echo off
echo VALO360 指令通 - 打包執行腳本
echo.

rem 執行打包腳本
call build.bat

rem 檢查打包結果
if exist "dist\VALO360CommandTool.exe" (
  echo.
  echo 打包成功，正在啟動程式...
  start "" "dist\VALO360CommandTool.exe"
) else (
  echo.
  echo 打包失敗，請檢查錯誤訊息。
)

echo.
echo 完成
pause 