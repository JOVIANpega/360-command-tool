import os
import subprocess
import sys

# 最簡化的建置腳本
def build():
    print("Minimal build script starting...")
    
    # 清理
    if os.path.exists("dist"):
        import shutil
        shutil.rmtree("dist")
    if os.path.exists("build"):
        import shutil
        shutil.rmtree("build")
    
    # 基本建置命令
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "VALO360指令通",
        "main.py"
    ]
    
    try:
        result = subprocess.run(cmd, shell=True)
        if result.returncode == 0:
            print("Build successful!")
        else:
            print(f"Build failed with code: {result.returncode}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    build()