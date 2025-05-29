import json
import os
import sys
from tkinter import messagebox

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        # 如果是打包後的執行檔，使用執行檔所在目錄
        base_path = os.path.dirname(sys.executable)
    else:
        # 如果是開發環境，使用當前目錄
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

COMMAND_FILE = resource_path('command.txt')
SETUP_FILE = resource_path('setup.json')
GUIDE_FILE = resource_path('user_guide.txt')

default_setup = {
    'DUT': {
        'COM': '',
        'Timeout': '30',
        'EndString': 'root',
        'UIFontSize': '12',
        'ContentFontSize': '12',
        'Title': 'VALO360 指令通',
        'EndStrings': json.dumps(['root'], ensure_ascii=False),
        'Default_IP': '192.168.11.143',
        'WinWidth': '800',
        'WinHeight': '600',
        'LastSection': '全部指令'
    },
    'FIXTURE': {
        'COM': '',
        'FixtureFontSize': '12',
        'MB': True,
        'CMD': ''
    }
}

def load_commands():
    commands = {}
    try:
        # 檢查檔案是否存在
        if not os.path.exists(COMMAND_FILE):
            messagebox.showerror('錯誤', f'找不到指令檔 (command.txt)\n路徑: {COMMAND_FILE}')
            sys.exit(1)
            
        # 讀取檔案內容
        with open(COMMAND_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 檢查是否包含 JOVIAN
        if 'JOVIAN' not in content:
            messagebox.showerror('錯誤', '請輸入合法的字串再開啟程式')
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
            messagebox.showerror('錯誤', '指令檔中沒有有效的指令格式')
            sys.exit(1)
            
    except Exception as e:
        messagebox.showerror('錯誤', f'讀取指令檔時發生錯誤: {e}\n路徑: {COMMAND_FILE}')
        sys.exit(1)
        
    return commands

def load_setup():
    if os.path.exists(SETUP_FILE):
        try:
            with open(SETUP_FILE, 'r', encoding='utf-8') as f:
                setup = json.load(f)
                # 確保所有必要的設定都存在
                for section in default_setup:
                    if section not in setup:
                        setup[section] = default_setup[section].copy()
                    else:
                        for key, value in default_setup[section].items():
                            if key not in setup[section]:
                                setup[section][key] = value
                # EndStrings 處理
                dut = setup.get('DUT', {})
                if 'EndStrings' in dut:
                    if isinstance(dut['EndStrings'], str):
                        try:
                            dut['EndStrings'] = json.loads(dut['EndStrings'])
                        except Exception:
                            dut['EndStrings'] = ["root"]
                return setup
        except Exception as e:
            messagebox.showerror('錯誤', f'無法讀取設定檔: {e}')
    return default_setup.copy()

def save_setup(setup_data):
    try:
        # 讀取現有的設定
        current_setup = {}
        if os.path.exists(SETUP_FILE):
            with open(SETUP_FILE, 'r', encoding='utf-8') as f:
                current_setup = json.load(f)
        # 更新設定
        for section, data in setup_data.items():
            if section not in current_setup:
                current_setup[section] = {}
            # 保證 data 是 dict
            if isinstance(data, dict):
                # EndStrings 處理
                if section == 'DUT' and 'EndStrings' in data:
                    if isinstance(data['EndStrings'], str):
                        try:
                            data['EndStrings'] = json.loads(data['EndStrings'])
                        except Exception:
                            data['EndStrings'] = ["root"]
                current_setup[section].update(data)
            else:
                current_setup[section] = data
        # 保存設定
        with open(SETUP_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_setup, f, ensure_ascii=False, indent=2)
    except Exception as e:
        messagebox.showerror('錯誤', f'無法保存設定檔: {e}')

def list_com_ports():
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    except Exception:
        return []