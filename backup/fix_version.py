# -*- coding: utf-8 -*-

"""
修正 EXE 版本資訊
"""

import os
import sys
import time
import shutil
import re
from datetime import datetime

# 設定顏色代碼
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def print_info(msg):
    """打印綠色信息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{GREEN}[{timestamp}] {msg}{RESET}")

def print_error(msg):
    """打印紅色錯誤信息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{RED}[{timestamp}] 錯誤: {msg}{RESET}")

def create_version_resource():
    """創建版本資源檔案"""
    print_info("創建版本資源檔案...")
    
    # 版本信息
    version_info = """# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=(1, 4, 2, 0),
    prodvers=(1, 4, 2, 0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'VALO360'),
        StringStruct(u'FileDescription', u'VALO360指令通'),
        StringStruct(u'FileVersion', u'1.4.2.0'),
        StringStruct(u'InternalName', u'VALO360指令通'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2023-2025'),
        StringStruct(u'OriginalFilename', u'VALO360指令通.exe'),
        StringStruct(u'ProductName', u'VALO360 指令通'),
        StringStruct(u'ProductVersion', u'1.4.2.0'),
        StringStruct(u'Comments', u'V1.4.2 改進GUI同步和設定更新功能')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1028, 1200])])
  ]
)
"""
    with open('version_info_fixed.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    print_info("已生成修正版本資訊檔案: version_info_fixed.txt")
    return 'version_info_fixed.txt'


def run_pyinstaller(version_file):
    """執行 PyInstaller 打包"""
    try:
        print_info("開始執行 PyInstaller 打包...")
        cmd = f'pyinstaller --onefile --noconsole --icon=app.ico --version-file={version_file} --name="VALO360指令通" --add-data "command.txt;." --add-data "setup.json;." --add-data "user_guide.txt;." --add-data "app.ico;." main.py'
        os.system(cmd)
        print_info("PyInstaller 打包完成")
        return True
    except Exception as e:
        print_error(f"PyInstaller 打包失敗: {e}")
        return False


def main():
    """主函數"""
    print_info("開始修正 EXE 版本資訊...")
    
    # 確保 main.py 中的版本號正確
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新版本號
        import re
        new_content = re.sub(r'VERSION = "V1\.[0-9]+"', 'VERSION = "V1.4.2"', content)
        
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print_info("已更新 main.py 中的版本號為 V1.4.2")
    except Exception as e:
        print_error(f"更新版本號失敗: {e}")
    
    # 創建版本資源檔案
    version_file = create_version_resource()
    
    # 執行 PyInstaller 打包
    if run_pyinstaller(version_file):
        print_info("版本資訊修正完成，程式已成功打包")
    else:
        print_error("版本資訊修正失敗")


if __name__ == "__main__":
    main() 