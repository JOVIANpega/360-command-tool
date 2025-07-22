#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import shutil

def install_package(package):
    """安裝 Python 套件"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except:
        return False

def check_and_install_dependencies():
    """檢查並安裝依賴"""
    dependencies = ["pyinstaller", "pyserial"]
    
    for dep in dependencies:
        try:
            __import__(dep.replace("-", "_"))
            print(f"✓ {dep} already installed")
        except ImportError:
            print(f"Installing {dep}...")
            if install_package(dep):
                print(f"✓ {dep} installed successfully")
            else:
                print(f"✗ Failed to install {dep}")
                return False
    return True

def clean_build_files():
    """清理舊的建置檔案"""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_to_clean = ["main.spec", "VALO360指令通.spec"]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ Cleaned {dir_name}")
    
    for file_name in files_to_clean:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"✓ Removed {file_name}")

def build_exe():
    """建置 EXE 檔案"""
    print("=== VALO360 指令通 EXE 建置工具 ===\n")
    
    # 檢查依賴
    if not check_and_install_dependencies():
        print("❌ 依賴安裝失敗")
        return False
    
    # 清理舊檔案
    clean_build_files()
    
    # 建置命令
    build_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed", 
        "--clean",
        "--noconfirm",
        "--name", "VALO360指令通",
        "--distpath", "dist",
        "--workpath", "build",
    ]
    
    # 添加圖示
    if os.path.exists("assets/app.ico"):
        build_cmd.extend(["--icon", "assets/app.ico"])
    
    # 添加數據檔案
    data_files = [
        ("Command_TABLE", "Command_TABLE"),
        ("FIXTURE", "FIXTURE"),
        ("ui_parts", "ui_parts"),
        ("assets", "assets"),
        ("user_guide.txt", "."),
        ("setup.json", "."),
        ("command.txt", "."),
        ("color_word.txt", "."),
    ]
    
    for src, dst in data_files:
        if os.path.exists(src):
            build_cmd.extend(["--add-data", f"{src};{dst}"])
            print(f"✓ Adding data: {src} -> {dst}")
    
    # 添加隱藏導入
    hidden_imports = [
        "tkinter",
        "tkinter.ttk", 
        "serial",
        "serial.tools.list_ports",
        "json",
        "threading",
        "datetime",
        "config_core",
        "config_utils",
        "serial_worker",
    ]
    
    for imp in hidden_imports:
        build_cmd.extend(["--hidden-import", imp])
    
    # 主程式檔案
    build_cmd.append("main.py")
    
    print("\n開始建置...")
    print("執行命令:", " ".join(build_cmd))
    
    try:
        # 執行建置
        result = subprocess.run(build_cmd, check=True, capture_output=True, text=True)
        print("✓ PyInstaller 建置成功")
        
        # 創建必要目錄
        dist_dirs = ["backup", "logs", "Command_TABLE", "FIXTURE"]
        for dir_name in dist_dirs:
            dist_path = os.path.join("dist", dir_name)
            os.makedirs(dist_path, exist_ok=True)
            print(f"✓ 創建目錄: {dist_path}")
        
        # 複製額外檔案
        extra_files = [
            "command.txt",
            "setup.json", 
            "user_guide.txt",
            "color_word.txt"
        ]
        
        for file_name in extra_files:
            if os.path.exists(file_name):
                shutil.copy2(file_name, "dist/")
                print(f"✓ 複製檔案: {file_name}")
        
        # 複製目錄內容
        if os.path.exists("Command_TABLE"):
            for file in os.listdir("Command_TABLE"):
                if file.endswith(".txt"):
                    src = os.path.join("Command_TABLE", file)
                    dst = os.path.join("dist", "Command_TABLE", file)
                    shutil.copy2(src, dst)
                    print(f"✓ 複製: {src}")
        
        if os.path.exists("FIXTURE"):
            for file in os.listdir("FIXTURE"):
                if file.endswith((".txt", ".py")):
                    src = os.path.join("FIXTURE", file)
                    dst = os.path.join("dist", "FIXTURE", file)
                    shutil.copy2(src, dst)
                    print(f"✓ 複製: {src}")
        
        print(f"\n🎉 建置完成!")
        print(f"執行檔位於: dist/VALO360指令通.exe")
        
        # 檢查檔案大小
        exe_path = "dist/VALO360指令通.exe"
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"檔案大小: {size_mb:.1f} MB")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 建置失敗!")
        print(f"錯誤碼: {e.returncode}")
        if e.stdout:
            print(f"輸出: {e.stdout}")
        if e.stderr:
            print(f"錯誤: {e.stderr}")
        return False
    
    except Exception as e:
        print(f"❌ 未預期的錯誤: {e}")
        return False

if __name__ == "__main__":
    success = build_exe()
    print(f"\n建置{'成功' if success else '失敗'}")
    input("按 Enter 鍵退出...")