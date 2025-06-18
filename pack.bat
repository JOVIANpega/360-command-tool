@echo off
echo VALO360 指令通 - 一鍵打包腳本
echo.

echo 第一步：安裝必要依賴...
pip install pyinstaller
pip install pyserial

echo.
echo 第二步：運行打包腳本...
call build.bat

echo.
echo 第三步：清理臨時文件...
call cleanup.bat

echo.
echo VALO360 指令通打包完成！可執行文件位於 dist 目錄中。
echo.

pause 