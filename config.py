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
        'Pane_Sash_Position': '400'  # 預設分割位置
    },
    'Fixture_Control': {
        'Fixture_COM_Port': '',
        'Fixture_Font_Size': '12',
        'Test_Category_MB': True,
        'Current_Command': ''
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
                dut = setup.get('DUT_Control', {})
                if 'Available_End_Strings' in dut:
                    if isinstance(dut['Available_End_Strings'], str):
                        try:
                            dut['Available_End_Strings'] = json.loads(dut['Available_End_Strings'])
                        except Exception:
                            dut['Available_End_Strings'] = ["root"]
                return setup
        except Exception as e:
            messagebox.showerror('錯誤', f'無法讀取設定檔: {e}')
    return default_setup.copy()

def save_setup(setup_data):
    try:
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
        messagebox.showerror('錯誤', f'無法保存設定檔: {e}')

def list_com_ports():
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    except Exception:
        return []