#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys
import os

def install_dependencies():
    """安裝必要的依賴"""
    dependencies = [
        "pyinstaller",
        "pyserial", 
        "psutil"
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✓ {dep} installed successfully")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {dep}")
            return False
    return True

def test_imports():
    """測試重要的導入"""
    imports = [
        ("tkinter", "tkinter"),
        ("serial", "pyserial"),
        ("json", "json (built-in)"),
        ("threading", "threading (built-in)")
    ]
    
    print("\nTesting imports...")
    for module, name in imports:
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError as e:
            print(f"✗ {name}: {e}")
            return False
    return True

def build_exe():
    """建置 EXE"""
    print("\nStarting build process...")
    
    # 清理舊檔案
    import shutil
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"Cleaned {folder}")
    
    # 建置命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        "--name", "VALO360指令通",
        "--icon", "assets/app.ico",
        "--add-data", "Command_TABLE;Command_TABLE",
        "--add-data", "FIXTURE;FIXTURE", 
        "--add-data", "ui_parts;ui_parts",
        "--add-data", "assets;assets",
        "--add-data", "user_guide.txt;.",
        "--add-data", "setup.json;.",
        "--add-data", "command.txt;.",
        "--add-data", "color_word.txt;.",
        "--add-data", "config_core.py;.",
        "--add-data", "config_utils.py;.",
        "--add-data", "serial_worker.py;.",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "serial",
        "--hidden-import", "serial.tools.list_ports",
        "--hidden-import", "config_core",
        "--hidden-import", "config_utils", 
        "--hidden-import", "serial_worker",
        "main.py"
    ]
    
    try:
        print("Running PyInstaller...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Build successful!")
            
            # 檢查輸出檔案
            exe_path = "dist/VALO360指令通.exe"
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"✓ EXE created: {size_mb:.1f} MB")
                
                # 創建必要目錄並複製檔案
                create_runtime_files()
                return True
            else:
                print("✗ EXE file not found")
                return False
        else:
            print("✗ Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Build error: {e}")
        return False

def create_runtime_files():
    """創建運行時需要的檔案和目錄"""
    print("\nCreating runtime files...")
    
    # 創建目錄
    dirs = ["backup", "logs", "Command_TABLE", "FIXTURE"]
    for dir_name in dirs:
        dir_path = os.path.join("dist", dir_name)
        os.makedirs(dir_path, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")
    
    # 複製檔案
    import shutil
    files_to_copy = [
        ("command.txt", "dist/command.txt"),
        ("setup.json", "dist/setup.json"),
        ("user_guide.txt", "dist/user_guide.txt"),
        ("color_word.txt", "dist/color_word.txt")
    ]
    
    for src, dst in files_to_copy:
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"✓ Copied: {src}")
    
    # 複製目錄內容
    if os.path.exists("Command_TABLE"):
        for file in os.listdir("Command_TABLE"):
            if file.endswith(".txt"):
                src = os.path.join("Command_TABLE", file)
                dst = os.path.join("dist", "Command_TABLE", file)
                shutil.copy2(src, dst)
                print(f"✓ Copied: {src}")

def main():
    print("=== VALO360 指令通 建置工具 ===\n")
    
    # 1. 安裝依賴
    if not install_dependencies():
        print("❌ 依賴安裝失敗")
        return False
    
    # 2. 測試導入
    if not test_imports():
        print("❌ 導入測試失敗")
        return False
    
    # 3. 建置 EXE
    if not build_exe():
        print("❌ 建置失敗")
        return False
    
    print("\n🎉 建置完成!")
    print("執行檔位於: dist/VALO360指令通.exe")
    return True

if __name__ == "__main__":
    success = main()
    print(f"\n建置{'成功' if success else '失敗'}")
    input("按 Enter 鍵退出...")