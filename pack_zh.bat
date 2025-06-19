@echo off
echo VALO360 指令通 - 打包腳本 (UTF-8 版本)
echo.

rem 設置版本號
set VERSION=V1.38

rem 確保版本資訊檔案存在
echo 更新版本資訊...
echo VSVersionInfo( > version_info_zh.txt
echo   ffi=FixedFileInfo( >> version_info_zh.txt
echo     filevers=(1, 3, 8, 0), >> version_info_zh.txt
echo     prodvers=(1, 3, 8, 0), >> version_info_zh.txt
echo     mask=0x3f, >> version_info_zh.txt
echo     flags=0x0, >> version_info_zh.txt
echo     OS=0x40004, >> version_info_zh.txt
echo     fileType=0x1, >> version_info_zh.txt
echo     subtype=0x0, >> version_info_zh.txt
echo     date=(0, 0) >> version_info_zh.txt
echo   ), >> version_info_zh.txt
echo   kids=[ >> version_info_zh.txt
echo     StringFileInfo( >> version_info_zh.txt
echo       [ >> version_info_zh.txt
echo         StringTable( >> version_info_zh.txt
echo           u'040904B0', >> version_info_zh.txt
echo           [StringStruct(u'CompanyName', u'VALO360'), >> version_info_zh.txt
echo            StringStruct(u'FileDescription', u'VALO360 指令通'), >> version_info_zh.txt
echo            StringStruct(u'FileVersion', u'%VERSION%'), >> version_info_zh.txt
echo            StringStruct(u'InternalName', u'VALO360指令通'), >> version_info_zh.txt
echo            StringStruct(u'LegalCopyright', u'Copyright (C) 2025 VALO360'), >> version_info_zh.txt
echo            StringStruct(u'OriginalFilename', u'VALO360指令通.exe'), >> version_info_zh.txt
echo            StringStruct(u'ProductName', u'VALO360 指令通'), >> version_info_zh.txt
echo            StringStruct(u'ProductVersion', u'%VERSION%')] >> version_info_zh.txt
echo         ) >> version_info_zh.txt
echo       ]), >> version_info_zh.txt
echo     VarFileInfo([VarStruct(u'Translation', [1033, 1200])]) >> version_info_zh.txt
echo   ] >> version_info_zh.txt
echo ) >> version_info_zh.txt

echo 開始打包程式...
pyinstaller --onefile --clean --noconfirm --icon=app.ico -w --version-file=version_info_zh.txt --add-data "command.txt;." --add-data "user_guide.txt;." --add-data "setup.json;." --add-data "app.ico;." --name "VALO360指令通" main_utf8.py

echo.
if %ERRORLEVEL% EQU 0 (
    echo 打包成功! 輸出檔案位於 dist/VALO360指令通.exe
) else (
    echo 打包失敗，錯誤碼: %ERRORLEVEL%
)

echo.
pause 