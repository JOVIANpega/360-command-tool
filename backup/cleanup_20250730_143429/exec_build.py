import os
import sys

# 直接執行系統命令
def run_build():
    print("Starting build process...")
    
    # 使用 os.system 來避免編碼問題
    commands = [
        "pip install pyinstaller pyserial psutil",
        "pyinstaller --onefile --windowed --clean --noconfirm --name VALO360指令通 --icon assets/app.ico --add-data Command_TABLE;Command_TABLE --add-data FIXTURE;FIXTURE --add-data ui_parts;ui_parts --add-data assets;assets --add-data user_guide.txt;. --add-data setup.json;. --add-data command.txt;. --add-data color_word.txt;. main.py"
    ]
    
    for cmd in commands:
        print(f"Executing: {cmd}")
        result = os.system(cmd)
        if result != 0:
            print(f"Command failed with code: {result}")
            return False
        print("Command completed successfully")
    
    # 檢查結果
    if os.path.exists("dist/VALO360指令通.exe"):
        size = os.path.getsize("dist/VALO360指令通.exe") / (1024*1024)
        print(f"Build successful! EXE size: {size:.1f} MB")
        return True
    else:
        print("Build failed - EXE not found")
        return False

if __name__ == "__main__":
    success = run_build()
    print("Build", "successful" if success else "failed")