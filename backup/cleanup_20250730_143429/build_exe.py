import os
import subprocess
import sys

subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "pyserial", "psutil"])
subprocess.run([sys.executable, "-m", "PyInstaller", "VALO360指令通.spec"])

if os.path.exists("dist/VALO360指令通.exe"):
    print("Build successful")
else:
    print("Build failed")