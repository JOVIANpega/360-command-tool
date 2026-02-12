# -*- coding: utf-8 -*-
"""
配置管理核心模組
提供設定檔案、指令檔案載入/保存功能和 COM 口管理
"""

import os
import sys
import json
from typing import Dict, List, Any, Optional
from tkinter import messagebox

# 確保核心模組已正確導入
from core.resource_manager import get_resource_manager
from core.config_manager import get_config_manager
from core.error_handler import get_error_handler
from core.performance_monitor import safe_execute
from core.error_handler import log_info, log_warning, log_error, log_debug

# 獲取核心模組實例
resource_manager = get_resource_manager()
config_manager = get_config_manager()
error_handler = get_error_handler()

# 定義重要檔案路徑
SETUP_FILE = resource_manager.get_resource_path('setup.json')
GUIDE_FILE = resource_manager.get_resource_path('user_guide.txt')
COMMAND_FILE = resource_manager.get_resource_path('command.txt')

# 取得今天的日期作為日誌檔名
from datetime import datetime
today = datetime.now().strftime('%Y%m%d')

# 日誌檔案路徑
TODAY_LOG_FILE = resource_manager.get_resource_path(f'logs/log_{today}.txt')



# 確保必要的目錄存在
resource_manager.ensure_directory('backup')
resource_manager.ensure_directory('logs')


# 預設配置已移至 ConfigManager 中，這裡保留向後相容性
default_setup = config_manager.default_config





@safe_execute(error_handler, show_user_error=True)
def load_commands() -> Dict[str, str]:
    """載入指令檔案，使用新的錯誤處理和快取機制"""
    commands = {}

    try:
        # 檢查檔案是否存在
        if not os.path.exists(COMMAND_FILE):
            error_msg = f'找不到指令檔 (command.txt)\n路徑: {COMMAND_FILE}'
            log_error(error_msg, show_user=True)
            sys.exit(1)

        # 使用資源管理器載入內容（支援快取）
        content = resource_manager.load_file_content(COMMAND_FILE)
        if content is None:
            error_msg = f'無法讀取指令檔: {COMMAND_FILE}'
            log_error(error_msg, show_user=True)
            sys.exit(1)



        # 解析指令格式
        has_valid_commands = False
        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('#'):
                continue

            if '=' in line:
                try:
                    k, v = line.split('=', 1)
                    k, v = k.strip(), v.strip()
                    if k and v:  # 確保鍵值都不為空
                        commands[k] = v
                        has_valid_commands = True
                except ValueError:
                    log_warning(f"指令檔第 {line_num} 行格式錯誤: {line}")
                    continue

        if not has_valid_commands:
            error_msg = '指令檔中沒有有效的指令格式'
            log_error(error_msg, show_user=True)
            sys.exit(1)

        log_info(f"成功載入 {len(commands)} 個指令")
        return commands

    except Exception as e:
        error_msg = f'讀取指令檔時發生錯誤: {e}\n路徑: {COMMAND_FILE}'
        log_error(error_msg, e, show_user=True)
        sys.exit(1)



def load_settings(path="setup.json") -> Dict[str, Any]:
    """新的設定載入函數，符合新需求規格"""
    return load_setup()

def save_settings(cfg: dict, path="setup.json") -> None:
    """新的設定保存函數，符合新需求規格"""
    save_setup(cfg, manual_save=True)

def load_setup() -> Dict[str, Any]:
    """載入設定檔 - 使用新的配置管理器"""
    return config_manager.load_config()



# ensure_required_fields 功能已整合到 ConfigManager 中

# 備份功能已整合到 ConfigManager 中
def backup_setup(setup_data):
    """備份設定檔 - 向後相容性包裝"""
    config_manager._backup_config(setup_data)

def cleanup_old_backups():
    """清理舊備份 - 向後相容性包裝"""
    config_manager._cleanup_old_backups()



def save_setup(setup_data: Dict[str, Any], manual_save=False) -> bool:
    """保存設定檔 - 使用新的配置管理器"""
    # 如果不是手動保存，則跳過（暫時禁用自動保存）
    if not manual_save:
        # print("[DEBUG] 自動保存已禁用，請使用手動保存")
        return False
    return config_manager.save_config(setup_data)



@safe_execute(error_handler)
def list_com_ports() -> List[str]:
    """列出可用的COM口，只對特定類型顯示描述"""
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        com_ports = []

        for port in ports:
            # 基本 COM 口名稱
            port_name = port.device

            # 獲取描述信息
            description = port.description.upper() if port.description else ""

            # 只對特定類型的 COM 口顯示描述
            display_name = port_name  # 預設只顯示 COM 口名稱

            # 檢查是否包含特定的描述關鍵字
            if "USB DM PORT" in description or "DM PORT" in description:
                display_name = f"{port_name} - DM PORT"
            elif "USB AT PORT" in description or "AT PORT" in description:
                display_name = f"{port_name} - AT PORT"
            elif "USB NMEA PORT" in description or "NMEA PORT" in description:
                display_name = f"{port_name} - NMEA PORT"
            elif "DT PORT" in description:
                display_name = f"{port_name} - DT PORT"
            # 其他類型的 COM 口只顯示名稱，不顯示描述

            com_ports.append(display_name)

        log_debug(f"找到 {len(com_ports)} 個COM口: {com_ports}")
        return com_ports
    except Exception as e:
        log_error("獲取COM口列表時發生錯誤", e)
        return []


def extract_com_port_name(display_name: str) -> str:
    """從顯示名稱中提取實際的 COM 口名稱"""
    if " - " in display_name:
        return display_name.split(" - ")[0]
    return display_name



def load_highlight_keywords():

    """載入關鍵字高亮設定"""

    highlight_keywords = {}

    

    try:

        print(f"[DEBUG] 開始載入關鍵字高亮設定...")

        with open(COMMAND_FILE, 'r', encoding='utf-8') as f:

            content = f.read()

            

        # 尋找關鍵字高亮區段

        print(f"[DEBUG] 搜尋關鍵字高亮區段...")

        keyword_section = re.search(r'\[關鍵字高亮\](.*?)(?=\[|\Z)', content, re.DOTALL)

        if not keyword_section:

            keyword_section = re.search(r'==關鍵字高亮==(.*?)(?===|\Z)', content, re.DOTALL)

            

        if keyword_section:

            keyword_content = keyword_section.group(1).strip()

            print(f"[DEBUG] 找到關鍵字高亮區段: {keyword_content}")

            for line in keyword_content.split('\n'):

                line = line.strip()

                if line and '=' in line:

                    parts = line.split('=', 1)

                    if len(parts) == 2:

                        keyword, color = parts

                        keyword = keyword.strip()

                        color = color.strip()

                        

                        # 檢查顏色名稱是否有效

                        valid_colors = ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'black', 'white', 'gray', 'pink', 'brown', 'cyan', 'magenta']

                        

                        # 如果顏色名稱不在有效顏色列表中，使用預設顏色

                        if color.lower() not in valid_colors and not color.startswith('#'):

                            print(f"[WARNING] 無效的顏色名稱: {color}，使用預設顏色 'blue'")

                            color = 'blue'

                        

                        if keyword and color:

                            highlight_keywords[keyword] = color

                            print(f"[INFO] 載入關鍵字高亮: {keyword} -> {color}")

        else:

            print(f"[WARNING] 找不到關鍵字高亮區段")

                        

        print(f"[INFO] 總共載入了 {len(highlight_keywords)} 個關鍵字高亮設定")

        return highlight_keywords

    except Exception as e:

        print(f"[ERROR] 載入關鍵字高亮設定時發生錯誤: {e}")

        import traceback

        traceback.print_exc()

        return {} 



def load_color_word():
    """
    從 color_word.txt 讀取關鍵字與顏色對應，回傳 dict。
    檔案格式：keyword=color，每行一組。
    支援顏色名稱與 #HEX，遇到錯誤自動略過。
    """
    color_word_file = resource_manager.get_resource_path('color_word.txt')
    color_dict = {}
    valid_colors = [
        'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'black', 'white', 'gray', 'pink', 'brown', 'cyan', 'magenta'
    ]
    try:
        if not os.path.exists(color_word_file):
            print(f"[WARNING] 找不到 color_word.txt：{color_word_file}")
            return color_dict
        with open(color_word_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    keyword, color = line.split('=', 1)
                    keyword = keyword.strip()
                    color = color.strip()
                    if not keyword or not color:
                        continue
                    # 檢查顏色是否合法
                    if color.lower() not in valid_colors and not color.startswith('#'):
                        print(f"[WARNING] color_word.txt 無效顏色：{color}，自動略過")
                        continue
                    color_dict[keyword] = color
        print(f"[INFO] color_word.txt 載入 {len(color_dict)} 組關鍵字高亮")
    except Exception as e:
        print(f"[ERROR] 讀取 color_word.txt 發生錯誤: {e}")
    return color_dict

def reload_color_word():
    """
    重新載入 color_word.txt，用於即時更新關鍵字高亮設定
    """
    print("[INFO] 重新載入 color_word.txt...")
    return load_color_word()

def open_color_word_editor():
    """
    開啟 color_word.txt 進行編輯
    """
    color_word_file = resource_manager.get_resource_path('color_word.txt')
    try:
        if platform.system() == 'Windows':
            os.startfile(color_word_file)
        elif platform.system() == 'Darwin':  # macOS
            os.system(f'open "{color_word_file}"')
        else:  # Linux
            os.system(f'xdg-open "{color_word_file}"')
        print(f"[INFO] 已開啟關鍵字設定檔：{color_word_file}")
        return True
    except Exception as e:
        print(f"[ERROR] 無法開啟關鍵字設定檔：{e}")
        return False

def ensure_default_settings():
    """確保設定檔包含所需的預設值"""
    settings = load_settings()
    
    # 確保 DUT_Control 區段
    if "DUT_Control" not in settings:
        settings["DUT_Control"] = {}
    
    dut = settings["DUT_Control"]
    
    # 確保預設值
    if "Default_IP_Address" not in dut:
        dut["Default_IP_Address"] = "192.168.11.143"
    if "Command_End_String" not in dut:
        dut["Command_End_String"] = "root"
    if "Pane_Sash_Position" not in dut:
        dut["Pane_Sash_Position"] = "420"
    if "Available_End_Strings" not in dut:
        dut["Available_End_Strings"] = ["root", "admin", "$"]
    
    # 確保 UI_Settings 區段（暫時保留以供兼容）
    if "UI_Settings" not in settings:
        settings["UI_Settings"] = {}
    
    ui = settings["UI_Settings"]
    if "left_pane_width" not in ui:
        ui["left_pane_width"] = 420
    
    save_settings(settings)
    print("[INFO] 預設設定已確保完整")
    return settings 