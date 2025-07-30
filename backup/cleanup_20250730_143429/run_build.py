import subprocess
import sys
import os

# 設置環境變數以避免編碼問題
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    # 執行批次檔
    result = subprocess.run(['build_fix.bat'], shell=True, capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
except Exception as e:
    print(f"Error: {e}")
    
    # 如果批次檔失敗，直接執行 PyInstaller
    try:
        print("Trying direct PyInstaller...")
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile", "--windowed", "--clean", "--noconfirm",
            "--name", "VALO360指令通",
            "--icon", "assets/app.ico",
            "--add-data", "Command_TABLE;Command_TABLE",
            "--add-data", "FIXTURE;FIXTURE",
            "--add-data", "user_guide.txt;.",
            "--add-data", "setup.json;.",
            "--add-data", "assets;assets",
            "--add-data", "ui_parts;ui_parts",
            "--add-data", "command.txt;.",
            "--add-data", "color_word.txt;.",
            "main.py"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("PyInstaller STDOUT:", result.stdout)
        if result.stderr:
            print("PyInstaller STDERR:", result.stderr)
        print("PyInstaller Return code:", result.returncode)
        
    except Exception as e2:
        print(f"PyInstaller also failed: {e2}")