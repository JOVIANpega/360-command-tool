# -*- coding: utf-8 -*-
"""
配置核心模組 - 重構版本
使用新的核心模組提供更好的錯誤處理和性能
"""
import json
import os
import sys
import re
import platform
import time
from datetime import datetime
from tkinter import messagebox
from typing import Dict, Any, List, Optional

# 導入新的核心模組
from core import (
    get_error_handler, get_config_manager, get_resource_manager,
    safe_execute, log_debug, log_info, log_warning, log_error
)

# 初始化核心組件
error_handler = get_error_handler()
config_manager = get_config_manager()
resource_manager = get_resource_manager()

# 確保必要的目錄存在
resource_manager.ensure_directory('backup')
resource_manager.ensure_directory('logs')

# 定義檔案路徑 - 使用新的資源管理器
COMMAND_FILE = resource_manager.get_resource_path('command.txt')
SETUP_FILE = resource_manager.get_resource_path('setup.json')
GUIDE_FILE = resource_manager.get_resource_path('user_guide.txt')
ERROR_LOG_FILE = resource_manager.get_resource_path('error_log.txt')
RUN_LOG_FILE = resource_manager.get_resource_path('run_log.txt')

# 當前日期的日誌文件
today = datetime.now().strftime('%Y%m%d')
TODAY_LOG_FILE = resource_manager.get_resource_path(f'logs/log_{today}.txt')



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



def save_setup(setup_data: Dict[str, Any]) -> bool:
    """保存設定檔 - 使用新的配置管理器"""
    return config_manager.save_config(setup_data)



@safe_execute(error_handler)
def list_com_ports() -> List[str]:
    """列出可用的COM口，包含更好的錯誤處理"""
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        com_ports = [port.device for port in ports]
        log_debug(f"找到 {len(com_ports)} 個COM口: {com_ports}")
        return com_ports
    except Exception as e:
        log_error("獲取COM口列表時發生錯誤", e)
        return []



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
    color_word_file = resource_path('color_word.txt')
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
    color_word_file = resource_path('color_word.txt')
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