# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import shutil

def build_exe():
    """簡化的打包腳本"""
    print("=== VALO360 指令通 打包腳本 ===")
    
    # 檢查依賴
    try:
        import PyInstaller
        print("✓ PyInstaller 已安裝")
    except ImportError:
        print("× PyInstaller 未安裝，正在安裝...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller 安裝完成")
    
    try:
        import serial
        print("✓ PySerial 已安裝")
    except ImportError:
        print("× PySerial 未安裝，正在安裝...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyserial"])
        print("✓ PySerial 安裝完成")
    
    # 清理舊檔案
    print("\n清理舊檔案...")
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"✓ 已清理 {folder}")
    
    # 刪除舊的 spec 檔案
    for spec_file in ["main.spec", "VALO360指令通.spec"]:
        if os.path.exists(spec_file):
            os.remove(spec_file)
            print(f"✓ 已刪除 {spec_file}")
    
    # 構建 PyInstaller 命令
    cmd = [
        "pyinstaller",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--windowed",  # 不顯示控制台
        "--name", "VALO360指令通",
        "--icon", "assets/app.ico",
        
        # 添加數據檔案
        "--add-data", "Command_TABLE;Command_TABLE",
        "--add-data", "FIXTURE;FIXTURE", 
        "--add-data", "user_guide.txt;.",
        "--add-data", "setup.json;.",
        "--add-data", "assets;assets",
        "--add-data", "ui_parts;ui_parts",
        "--add-data", "command.txt;.",
        "--add-data", "color_word.txt;.",
        
        # 隱藏導入
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "serial",
        "--hidden-import", "serial.tools.list_ports",
        "--hidden-import", "json",
        "--hidden-import", "threading",
        "--hidden-import", "datetime",
        "--hidden-import", "os",
        "--hidden-import", "sys",
        
        "main.py"
    ]
    
    print("\n開始打包...")
    print("執行命令:", " ".join(cmd))
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        print("✓ 打包成功!")
        
        # 創建必要目錄
        dist_dir = "dist"
        for folder in ["backup", "logs", "Command_TABLE", "FIXTURE"]:
            folder_path = os.path.join(dist_dir, folder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                print(f"✓ 創建目錄: {folder_path}")
        
        # 複製必要檔案
        files_to_copy = [
            ("command.txt", "dist/command.txt"),
            ("setup.json", "dist/setup.json"),
            ("user_guide.txt", "dist/user_guide.txt"),
            ("color_word.txt", "dist/color_word.txt"),
        ]
        
        for src, dst in files_to_copy:
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"✓ 複製: {src} -> {dst}")
        
        # 複製 Command_TABLE 目錄內容
        if os.path.exists("Command_TABLE"):
            for file in os.listdir("Command_TABLE"):
                if file.endswith(".txt"):
                    src = os.path.join("Command_TABLE", file)
                    dst = os.path.join("dist", "Command_TABLE", file)
                    shutil.copy2(src, dst)
                    print(f"✓ 複製: {src} -> {dst}")
        
        # 複製 FIXTURE 目錄內容
        if os.path.exists("FIXTURE"):
            for file in os.listdir("FIXTURE"):
                if file.endswith(".txt") or file.endswith(".py"):
                    src = os.path.join("FIXTURE", file)
                    dst = os.path.join("dist", "FIXTURE", file)
                    shutil.copy2(src, dst)
                    print(f"✓ 複製: {src} -> {dst}")
        
        print(f"\n🎉 打包完成! 執行檔位於: dist/VALO360指令通.exe")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失敗!")
        print(f"錯誤碼: {e.returncode}")
        print(f"錯誤輸出: {e.stderr}")
        return False
    
    return True

if __name__ == "__main__":
    success = build_exe()
    if success:
        print("\n按任意鍵退出...")
        input()
    else:
        print("\n打包失敗，請檢查錯誤訊息")
        input()