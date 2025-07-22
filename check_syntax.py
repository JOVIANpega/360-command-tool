#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import sys
import os

def check_python_file(filepath):
    """檢查 Python 檔案語法"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 嘗試解析語法
        ast.parse(content)
        print(f"✓ {filepath} - 語法正確")
        return True
    except SyntaxError as e:
        print(f"✗ {filepath} - 語法錯誤: {e}")
        return False
    except Exception as e:
        print(f"✗ {filepath} - 其他錯誤: {e}")
        return False

def check_imports():
    """檢查主要導入"""
    imports_to_check = [
        'tkinter',
        'serial', 
        'json',
        'threading',
        'datetime',
        'os',
        'sys'
    ]
    
    for imp in imports_to_check:
        try:
            __import__(imp)
            print(f"✓ {imp} - 可導入")
        except ImportError as e:
            print(f"✗ {imp} - 導入失敗: {e}")

def main():
    print("=== 語法和導入檢查 ===\n")
    
    # 檢查主要 Python 檔案
    files_to_check = [
        'main.py',
        'config_core.py', 
        'config_utils.py',
        'serial_worker.py'
    ]
    
    print("檢查語法:")
    all_good = True
    for file in files_to_check:
        if os.path.exists(file):
            if not check_python_file(file):
                all_good = False
        else:
            print(f"✗ {file} - 檔案不存在")
            all_good = False
    
    print("\n檢查導入:")
    check_imports()
    
    print(f"\n總結: {'所有檢查通過' if all_good else '發現問題'}")
    
    # 如果所有檢查通過，嘗試執行 PyInstaller
    if all_good:
        print("\n嘗試執行 PyInstaller...")
        try:
            import subprocess
            cmd = [
                sys.executable, "-m", "PyInstaller", 
                "--version"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ PyInstaller 版本: {result.stdout.strip()}")
                
                # 嘗試實際建置
                print("\n開始建置...")
                build_cmd = [
                    sys.executable, "-m", "PyInstaller",
                    "VALO360指令通.spec"
                ]
                
                build_result = subprocess.run(build_cmd, capture_output=True, text=True)
                if build_result.returncode == 0:
                    print("✓ 建置成功!")
                    if os.path.exists("dist/VALO360指令通.exe"):
                        size = os.path.getsize("dist/VALO360指令通.exe") / (1024*1024)
                        print(f"✓ EXE 檔案已生成，大小: {size:.1f} MB")
                else:
                    print("✗ 建置失敗:")
                    print("STDOUT:", build_result.stdout)
                    print("STDERR:", build_result.stderr)
            else:
                print(f"✗ PyInstaller 錯誤: {result.stderr}")
        except Exception as e:
            print(f"✗ PyInstaller 執行錯誤: {e}")

if __name__ == "__main__":
    main()
    input("\n按 Enter 鍵退出...")