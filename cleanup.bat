@echo off
echo Starting cleanup of unnecessary files and directories...

:: Delete Python cache files
echo Deleting Python cache files...
rd /s /q __pycache__ 2>nul
rd /s /q ui_parts\__pycache__ 2>nul

:: Delete PyInstaller build files
echo Deleting PyInstaller build files...
rd /s /q build 2>nul

:: Delete backup and temporary files
echo Deleting backup and temporary files...
del test_command.txt 2>nul
del build_commands.txt 2>nul
del build_code.txt 2>nul
del build_command.txt 2>nul
del dist\main.exe 2>nul
del main_backup.py 2>nul
del "build code.txt" 2>nul

:: Delete duplicate files
echo Deleting duplicate files...
del VALO360指令通.spec 2>nul
del main.spec 2>nul

:: Keep readme.md, delete readme.txt
echo Organizing documentation files...
del readme.txt 2>nul

:: Delete unused code files
echo Deleting unused code files...
del ui_parts\ui_components_new.py 2>nul
del ui_parts\handlers.py 2>nul

echo Cleanup completed!
pause 