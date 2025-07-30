@echo off
chcp 65001 > nul
echo VALO360 指令通 - EXE 打包工具
echo.

echo 1. 安装依赖...
pip install pyinstaller pyserial psutil
if %errorlevel% neq 0 (
    echo 依赖安装失败
    goto end
)

echo.
echo 2. 清理旧文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo 3. 开始构建...
pyinstaller VALO360指令通.spec
if %errorlevel% neq 0 (
    echo 构建失败
    goto end
)

echo.
echo 4. 创建运行时目录...
if not exist "dist\backup" mkdir dist\backup
if not exist "dist\logs" mkdir dist\logs
if not exist "dist\Command_TABLE" mkdir dist\Command_TABLE
if not exist "dist\FIXTURE" mkdir dist\FIXTURE

echo.
echo 5. 复制必要文件...
if exist "setup.json" copy setup.json dist\
if exist "user_guide.txt" copy user_guide.txt dist\
if exist "Command_TABLE\command.txt" copy Command_TABLE\command.txt dist\Command_TABLE\
if exist "FIXTURE\Fixture_Command.txt" copy FIXTURE\Fixture_Command.txt dist\FIXTURE\

echo.
if exist "dist\VALO360指令通.exe" (
    echo 🎉 打包成功!
    echo 输出文件: dist\VALO360指令通.exe
    dir dist\VALO360指令通.exe
) else (
    echo ❌ 打包失败，EXE文件未生成
)

:end
echo.
pause