import os
import sys
import subprocess

try:
    result = subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "pyserial", "psutil"], 
                          capture_output=True, text=True, check=True)
    print("Dependencies installed")
    
    result = subprocess.run([sys.executable, "-m", "PyInstaller", "VALO360指令通.spec"], 
                          capture_output=True, text=True, check=True)
    print("Build completed")
    
    if os.path.exists("dist/VALO360指令通.exe"):
        size = os.path.getsize("dist/VALO360指令通.exe") / 1024 / 1024
        print(f"EXE created: {size:.1f} MB")
    else:
        print("EXE not found")
        
except subprocess.CalledProcessError as e:
    print(f"Error: {e}")
    print(f"Output: {e.stdout}")
    print(f"Error: {e.stderr}")
except Exception as e:
    print(f"Exception: {e}")

input("Press Enter to exit")