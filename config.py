import json
import os
import sys
import logging
from datetime import datetime
from tkinter import messagebox

def resource_path(relative_path):
    """獲取資源的絕對路徑，支持開發環境和打包後的環境"""
    try:
        if getattr(sys, 'frozen', False):
            # 如果是打包後的執行檔，使用執行檔所在目錄
            base_path = os.path.dirname(sys.executable)
        else:
            # 如果是開發環境，使用當前目錄
            base_path = os.path.abspath(".")
        
        # 確保相對路徑不包含開頭的斜線
        if relative_path.startswith('/') or relative_path.startswith('\\'):
            relative_path = relative_path[1:]
            
        return os.path.join(base_path, relative_path)
    except Exception as e:
        print(f"[ERROR] 獲取資源路徑時發生錯誤: {e}")
        # 返回一個基本路徑作為備選
        return os.path.join(os.path.abspath("."), relative_path)

# 確保必要的目錄存在
def ensure_directories_exist():
    """確保必要的目錄存在"""
    try:
        # 確保備份目錄存在
        backup_dir = resource_path('backup')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            print(f"[INFO] 已創建備份目錄: {backup_dir}")
            
        # 確保日誌目錄存在
        log_dir = resource_path('logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            print(f"[INFO] 已創建日誌目錄: {log_dir}")
            
        return True
    except Exception as e:
        print(f"[ERROR] 創建目錄時發生錯誤: {e}")
        return False

# 初始化目錄
ensure_directories_exist()

# 定義檔案路徑
COMMAND_FILE = resource_path('command.txt')
SETUP_FILE = resource_path('setup.json')
GUIDE_FILE = resource_path('user_guide.txt')
ERROR_LOG_FILE = resource_path('error_log.txt')
RUN_LOG_FILE = resource_path('run_log.txt')

# 當前日期的日誌文件
today = datetime.now().strftime('%Y%m%d')
TODAY_LOG_FILE = resource_path(f'logs/log_{today}.txt')

# 記錄錯誤訊息到日誌檔
def log_error(message):
    """記錄錯誤訊息到日誌檔"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"[ERROR] 無法寫入錯誤日誌: {e}")

default_setup = {
    'DUT_Control': {
        'Serial_COM_Port': '',
        'Command_Timeout_Seconds': '30',
        'Command_End_String': 'root',
        'UI_Font_Size': '12',
        'Content_Font_Size': '12',
        'Window_Title': 'VALO360 指令通',
        'Available_End_Strings': ['root'],
        'Default_IP_Address': '192.168.11.143',
        'Window_Width': '800',
        'Window_Height': '600',
        'Last_Selected_Command_Section': '全部指令',
        'Pane_Sash_Position': '400',  # 預設分割位置
        'Auto_Execute': False         # 預設不自動執行
    },
    'Fixture_Control': {
        'Fixture_COM_Port': '',
        'Fixture_Font_Size': '12',
        'Test_Category_MB': True,
        'Current_Command': ''
    }
}

def load_commands():
    """載入指令檔案，包含更好的錯誤處理和日誌記錄"""
    commands = {}
    try:
        # 檢查檔案是否存在
        if not os.path.exists(COMMAND_FILE):
            error_msg = f'找不到指令檔 (command.txt)\n路徑: {COMMAND_FILE}'
            log_error(error_msg)
            messagebox.showerror('錯誤', error_msg)
            sys.exit(1)
            
        # 讀取檔案內容
        with open(COMMAND_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 檢查是否包含 JOVIAN
        if 'JOVIAN' not in content:
            error_msg = '請輸入合法的字串再開啟程式'
            log_error(error_msg)
            messagebox.showerror('錯誤', error_msg)
            sys.exit(1)
            
        # 檢查指令格式
        has_valid_commands = False
        for line in content.split('\n'):
            if '=' in line:
                k, v = line.strip().split('=', 1)
                if k.strip() and v.strip():  # 確保鍵值都不為空
                    commands[k.strip()] = v.strip()
                    has_valid_commands = True
                    
        if not has_valid_commands:
            error_msg = '指令檔中沒有有效的指令格式'
            log_error(error_msg)
            messagebox.showerror('錯誤', error_msg)
            sys.exit(1)
            
    except Exception as e:
        error_msg = f'讀取指令檔時發生錯誤: {e}\n路徑: {COMMAND_FILE}'
        log_error(error_msg)
        messagebox.showerror('錯誤', error_msg)
        sys.exit(1)
        
    return commands

def load_setup():
    """載入設定檔，包含更好的錯誤處理和備份功能"""
    if os.path.exists(SETUP_FILE):
        try:
            # 先讀取設定檔
            with open(SETUP_FILE, 'r', encoding='utf-8') as f:
                setup = json.load(f)
                
            # 在處理前先備份設定檔
            backup_setup(setup)
                
            # 確保所有必要的設定都存在
            for section in default_setup:
                if section not in setup:
                    setup[section] = default_setup[section].copy()
                else:
                    for key, value in default_setup[section].items():
                        if key not in setup[section]:
                            setup[section][key] = value
            
            # EndStrings 處理
            dut = setup.get('DUT_Control', {})
            if 'Available_End_Strings' in dut:
                if isinstance(dut['Available_End_Strings'], str):
                    try:
                        dut['Available_End_Strings'] = json.loads(dut['Available_End_Strings'])
                    except Exception:
                        dut['Available_End_Strings'] = ["root"]
            
            return setup
        except Exception as e:
            error_msg = f'無法讀取設定檔: {e}'
            log_error(error_msg)
            messagebox.showerror('錯誤', error_msg)
    
    # 如果無法讀取或設定檔不存在，使用預設設定
    return default_setup.copy()

def backup_setup(setup_data):
    """備份設定檔"""
    try:
        # 建立備份檔名，格式為 backup_日期_時間.json
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = resource_path(f'backup/setup_backup_{timestamp}.json')
        
        # 寫入備份檔
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(setup_data, f, ensure_ascii=False, indent=2)
            
        print(f"[INFO] 已備份設定檔至: {backup_file}")
        
        # 清理過舊的備份檔 (保留最近30個)
        cleanup_old_backups()
        
    except Exception as e:
        print(f"[ERROR] 無法備份設定檔: {e}")

def cleanup_old_backups():
    """清理過舊的備份檔，只保留最近30個"""
    try:
        backup_dir = resource_path('backup')
        if os.path.exists(backup_dir):
            backup_files = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) 
                           if f.startswith('setup_backup_') and f.endswith('.json')]
            
            # 按修改時間排序
            backup_files.sort(key=os.path.getmtime, reverse=True)
            
            # 刪除超過30個的舊檔案
            if len(backup_files) > 30:
                for old_file in backup_files[30:]:
                    try:
                        os.remove(old_file)
                        print(f"[INFO] 已刪除舊備份檔: {old_file}")
                    except Exception as e:
                        print(f"[ERROR] 無法刪除舊備份檔 {old_file}: {e}")
    except Exception as e:
        print(f"[ERROR] 清理舊備份檔時發生錯誤: {e}")

def save_setup(setup_data):
    """保存設定檔，包含更好的錯誤處理和日誌記錄"""
    try:
        # 先備份現有設定
        if os.path.exists(SETUP_FILE):
            try:
                with open(SETUP_FILE, 'r', encoding='utf-8') as f:
                    old_setup = json.load(f)
                backup_setup(old_setup)
            except Exception as e:
                print(f"[ERROR] 備份現有設定時發生錯誤: {e}")
        
        # 只保留分層結構，不讀取舊的扁平參數
        clean_setup = {}
        
        # 確保有基本的分層結構
        for section in ['DUT_Control', 'Fixture_Control']:
            clean_setup[section] = {}
        
        # 更新設定
        for section, data in setup_data.items():
            if section in ['DUT_Control', 'Fixture_Control']:
                # 保證 data 是 dict
                if isinstance(data, dict):
                    # EndStrings 處理
                    if section == 'DUT_Control' and 'Available_End_Strings' in data:
                        if isinstance(data['Available_End_Strings'], str):
                            try:
                                data['Available_End_Strings'] = json.loads(data['Available_End_Strings'])
                            except Exception:
                                data['Available_End_Strings'] = ["root"]
                    clean_setup[section].update(data)
                else:
                    clean_setup[section] = data
        
        # 保存設定
        with open(SETUP_FILE, 'w', encoding='utf-8') as f:
            json.dump(clean_setup, f, ensure_ascii=False, indent=2)
            
        print(f"[DEBUG] 已保存乾淨的設定結構: {list(clean_setup.keys())}")
        
    except Exception as e:
        error_msg = f'無法保存設定檔: {e}'
        log_error(error_msg)
        messagebox.showerror('錯誤', error_msg)

def list_com_ports():
    """列出可用的COM口，包含更好的錯誤處理"""
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        com_ports = [port.device for port in ports]
        print(f"[DEBUG] 找到 {len(com_ports)} 個COM口: {com_ports}")
        return com_ports
    except Exception as e:
        print(f"[ERROR] 獲取COM口列表時發生錯誤: {e}")
        return []