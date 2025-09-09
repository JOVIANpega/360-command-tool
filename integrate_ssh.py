#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSH功能自動整合腳本
一鍵完成所有SSH功能的整合

此腳本會自動：
1. 備份所有要修改的檔案
2. 在所有傳輸方式下拉選單加入SSH選項
3. 整合SSH處理邏輯到事件處理器
4. 在設定頁面加入SSH設定區塊
5. 在setup.json加入SSH配置

使用方法：
python integrate_ssh.py
"""

import os
import re
import json
import shutil
from datetime import datetime

def backup_file(file_path):
    """備份檔案"""
    if not os.path.exists(file_path):
        print(f"⚠️  檔案不存在: {file_path}")
        return False
    
    backup_path = file_path + f'.backup_before_ssh_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    try:
        shutil.copy2(file_path, backup_path)
        print(f"✅ 已備份: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ 備份失敗 {file_path}: {e}")
        return False

def update_transport_modes():
    """更新所有傳輸方式選項，加入SSH"""
    files_to_update = [
        'ui_parts/ui_components.py',
        'ui_parts/ui_manual_command.py'
    ]
    
    success_count = 0
    for file_path in files_to_update:
        if not os.path.exists(file_path):
            print(f"⚠️  檔案不存在: {file_path}")
            continue
            
        if not backup_file(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 更新傳輸方式選項
            patterns = [
                (r"values=\['Console', 'ADB'\]", "values=['Console', 'ADB', 'SSH']"),
                (r'values=\["Console", "ADB"\]', 'values=["Console", "ADB", "SSH"]'),
            ]
            
            modified = False
            for pattern, replacement in patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    modified = True
                    print(f"✅ 已更新傳輸方式選項: {file_path}")
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                success_count += 1
            else:
                print(f"⚠️  未找到需要更新的傳輸方式選項: {file_path}")
                
        except Exception as e:
            print(f"❌ 更新失敗 {file_path}: {e}")
    
    return success_count

def integrate_ssh_handler():
    """整合SSH到事件處理器"""
    file_path = 'ui_parts/ui_handlers.py'
    if not os.path.exists(file_path):
        print(f"❌ 檔案不存在: {file_path}")
        return False
    
    if not backup_file(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # SSH處理器程式碼
        ssh_handler_code = '''        elif transport_mode == "SSH":
            # 導入 SSH 工作器
            from ssh_worker import SSHWorker
            
            # 獲取 SSH 設定
            ssh_settings = self.setup.get("SSH_Settings", {})
            host = ssh_settings.get("Host", "192.168.11.143")
            port = int(ssh_settings.get("Port", 22))
            default_account = ssh_settings.get("Default_Account", "root/oelinux123")
            
            # 解析帳號密碼
            if "/" in default_account:
                username, password = default_account.split("/", 1)
            else:
                username = default_account
                password = ""

            # 創建並啟動 SSH 線程
            self.parent.thread = SSHWorker(
                cmd_list, end_string, timeout,
                host, port, username, password,
                on_data=lambda text, tag: self.on_data(text, tag),
                on_status=lambda connected: self.parent.root.after(0, lambda: self.update_status_light(connected)),
                on_progress=lambda p: self.parent.root.after(0, lambda: self.parent.components.update_progress(p)),
                on_finish=lambda: self.parent.root.after(0, self.on_command_finish),
                stop_event=self.parent.stop_event
            )'''
        
        # 找到ADB處理的位置，在後面插入SSH處理
        # 先找到ADB處理的結束位置
        adb_pattern = r'(\s+if transport_mode == "ADB":.*?stop_event=self\.parent\.stop_event\s+\))'
        
        def replacement(match):
            adb_code = match.group(1)
            return adb_code + '\n' + ssh_handler_code
        
        if re.search(adb_pattern, content, re.DOTALL):
            content = re.sub(adb_pattern, replacement, content, flags=re.DOTALL)
            print(f"✅ 已整合SSH到事件處理器: {file_path}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        else:
            print(f"⚠️  未找到ADB處理邏輯，無法插入SSH處理: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ 整合SSH處理器失敗 {file_path}: {e}")
        return False

def add_ssh_settings_to_ui():
    """在設定頁面加入SSH設定區塊"""
    file_path = 'ui_parts/ui_settings_tab.py'
    if not os.path.exists(file_path):
        print(f"❌ 檔案不存在: {file_path}")
        return False
    
    if not backup_file(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # SSH設定區塊程式碼
        ssh_settings_code = '''
        # SSH 設定
        ssh_frame = ttk.LabelFrame(left_container, text="SSH 設定", padding=(10, 4))
        ssh_frame.pack(fill='x', pady=(0, 8))
        ssh_frame.columnconfigure(1, weight=1)
        
        ssh_settings = self.setup_data.get("SSH_Settings", {})
        
        # 主機地址
        ttk.Label(ssh_frame, text="主機地址:").grid(row=0, column=0, sticky="w", pady=4)
        self.vars["SSH_Host"] = tk.StringVar(value=ssh_settings.get("Host", "192.168.11.143"))
        ttk.Entry(ssh_frame, textvariable=self.vars["SSH_Host"], width=20).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=4)
        
        # 埠號
        ttk.Label(ssh_frame, text="埠號:").grid(row=1, column=0, sticky="w", pady=4)
        self.vars["SSH_Port"] = tk.StringVar(value=str(ssh_settings.get("Port", 22)))
        ttk.Entry(ssh_frame, textvariable=self.vars["SSH_Port"], width=20).grid(row=1, column=1, sticky="w", padx=(10, 0), pady=4)
        
        # 預設帳號
        ttk.Label(ssh_frame, text="預設帳號:").grid(row=2, column=0, sticky="w", pady=4)
        self.vars["SSH_Default_Account"] = tk.StringVar(value=ssh_settings.get("Default_Account", "root/oelinux123"))
        ttk.Entry(ssh_frame, textvariable=self.vars["SSH_Default_Account"], width=20).grid(row=2, column=1, sticky="w", padx=(10, 0), pady=4)
        
        # 連線超時
        ttk.Label(ssh_frame, text="連線超時:").grid(row=3, column=0, sticky="w", pady=4)
        self.vars["SSH_Connection_Timeout"] = tk.StringVar(value=str(ssh_settings.get("Connection_Timeout", 30)))
        ttk.Entry(ssh_frame, textvariable=self.vars["SSH_Connection_Timeout"], width=20).grid(row=3, column=1, sticky="w", padx=(10, 0), pady=4)
'''
        
        # 尋找合適的插入位置 - 在DUT控制設定後面
        insertion_patterns = [
            r'(\s+# DUT 控制設定.*?dut_frame\.pack.*?expand=True.*?\n)',
            r'(\s+dut_frame\.pack.*?expand=True.*?\n)',
            r'(\s+left_container\.pack.*?side="left".*?fill="both".*?expand=True.*?\n)'
        ]
        
        inserted = False
        for pattern in insertion_patterns:
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, r'\1' + ssh_settings_code, content, flags=re.DOTALL)
                print(f"✅ 已在設定頁面加入SSH設定區塊")
                inserted = True
                break
        
        if not inserted:
            print(f"⚠️  未找到合適位置插入SSH設定，請手動加入")
            return False
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
            
    except Exception as e:
        print(f"❌ 加入SSH設定失敗 {file_path}: {e}")
        return False

def update_setup_json():
    """在setup.json加入SSH設定"""
    file_path = 'setup.json'
    if not os.path.exists(file_path):
        print(f"❌ 檔案不存在: {file_path}")
        return False
    
    if not backup_file(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # SSH設定區塊
        ssh_settings = '''  "SSH_Settings": {
    "Host": "192.168.11.143",
    "Port": 22,
    "Default_Account": "root/oelinux123",
    "Account_History": [
      "root/oelinux123",
      "root/"
    ],
    "IP_History": [
      "192.168.11.143",
      "192.168.225.1"
    ],
    "Connection_Timeout": 30,
    "Command_Timeout": 30
  },'''
        
        # 在Command_Transport_Mode前加入SSH_Settings
        pattern = r'(\s*"Command_Transport_Mode":)'
        if re.search(pattern, content):
            content = re.sub(pattern, f'{ssh_settings}\n\\1', content)
            print(f"✅ 已在setup.json加入SSH設定")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        else:
            print(f"⚠️  未找到Command_Transport_Mode，無法插入SSH設定")
            return False
            
    except Exception as e:
        print(f"❌ 更新setup.json失敗: {e}")
        return False

def check_ssh_worker():
    """檢查SSH工作器是否存在"""
    ssh_worker_path = 'ssh_worker.py'
    if os.path.exists(ssh_worker_path):
        print(f"✅ SSH工作器已存在: {ssh_worker_path}")
        return True
    else:
        print(f"⚠️  SSH工作器不存在: {ssh_worker_path}")
        print("   請確保ssh_worker.py檔案存在於專案根目錄")
        return False

def main():
    """主函數"""
    print("🚀 開始自動整合SSH功能...")
    print("=" * 60)
    
    success_count = 0
    total_steps = 5
    
    try:
        # 1. 檢查SSH工作器
        print("📝 步驟 1/5: 檢查SSH工作器")
        if check_ssh_worker():
            success_count += 1
        print()
        
        # 2. 更新傳輸方式選項
        print("📝 步驟 2/5: 更新傳輸方式選項")
        updated_files = update_transport_modes()
        if updated_files > 0:
            success_count += 1
        print()
        
        # 3. 整合SSH到事件處理器  
        print("📝 步驟 3/5: 整合SSH到事件處理器")
        if integrate_ssh_handler():
            success_count += 1
        print()
        
        # 4. 在設定頁面加入SSH設定
        print("📝 步驟 4/5: 在設定頁面加入SSH設定")
        if add_ssh_settings_to_ui():
            success_count += 1
        print()
        
        # 5. 更新setup.json
        print("📝 步驟 5/5: 更新setup.json")
        if update_setup_json():
            success_count += 1
        print()
        
        print("=" * 60)
        if success_count == total_steps:
            print("🎉 SSH功能整合完成！")
            print(f"✅ 成功完成 {success_count}/{total_steps} 個步驟")
            print("\n📋 下一步：")
            print("   1. 安裝依賴: pip install paramiko>=2.7.0")
            print("   2. 測試程式啟動: python main.py")
            print("   3. 在設定頁面配置SSH連線資訊")
            print("   4. 選擇傳輸方式為SSH並測試連線")
            print("\n💡 提示：")
            print("   - 所有原始檔案都已備份（.backup_before_ssh_*）")
            print("   - 如有問題可從備份檔案還原")
            return 0
        else:
            print(f"⚠️  部分步驟未完成: {success_count}/{total_steps}")
            print("請檢查上述錯誤訊息並手動修復")
            return 1
        
    except Exception as e:
        print(f"\n❌ 整合過程中發生錯誤: {e}")
        print("請檢查錯誤訊息並手動修復")
        return 1

if __name__ == "__main__":
    exit(main())
