#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import shutil

def main():
    print("=== VALO360 指令通 EXE 打包工具 ===")
    
    # 1. 安装依赖
    print("\n1. 安装依赖...")
    deps = ["pyinstaller", "pyserial", "psutil"]
    for dep in deps:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✓ {dep}")
        except:
            print(f"✗ {dep} 安装失败")
    
    # 2. 清理旧文件
    print("\n2. 清理旧文件...")
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"✓ 清理 {folder}")
    
    # 3. 使用spec文件构建
    print("\n3. 开始构建...")
    spec_file = "VALO360指令通.spec"
    
    if not os.path.exists(spec_file):
        print(f"✗ 找不到 {spec_file}")
        return False
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller", spec_file
        ], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            print("✓ 构建成功!")
            
            # 检查输出文件
            exe_path = "dist/VALO360指令通.exe"
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"✓ EXE 文件: {size_mb:.1f} MB")
                
                # 创建运行时目录
                print("\n4. 创建运行时文件...")
                create_runtime_structure()
                
                print("\n🎉 打包完成!")
                print(f"输出文件: {exe_path}")
                return True
            else:
                print("✗ EXE 文件未生成")
                return False
        else:
            print("✗ 构建失败")
            print("错误信息:", result.stderr[:500])
            return False
            
    except Exception as e:
        print(f"✗ 构建异常: {e}")
        return False

def create_runtime_structure():
    """创建运行时需要的目录结构"""
    # 创建必要目录
    dirs = ["backup", "logs", "Command_TABLE", "FIXTURE"]
    for dir_name in dirs:
        dir_path = os.path.join("dist", dir_name)
        os.makedirs(dir_path, exist_ok=True)
        print(f"✓ 目录: {dir_name}")
    
    # 复制重要文件
    files = [
        ("setup.json", "dist/setup.json"),
        ("user_guide.txt", "dist/user_guide.txt")
    ]
    
    for src, dst in files:
        if os.path.exists(src):
            try:
                shutil.copy2(src, dst)
                print(f"✓ 文件: {os.path.basename(src)}")
            except:
                pass

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ 打包失败，请检查错误信息")
    else:
        print("\n✅ 打包成功，可以测试运行")