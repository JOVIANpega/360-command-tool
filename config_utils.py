# -*- coding: utf-8 -*-
import os

import sys

from datetime import datetime

import json

# 全局變數，存儲通知訊息
NOTIFY_TEXTS = {}
APP_VERSION = ""

def load_notification_messages():
    """從 setup.json 中讀取通知訊息"""
    global NOTIFY_TEXTS, APP_VERSION
    
    try:
        # 確定 setup.json 的路徑
        if getattr(sys, 'frozen', False):
            # 如果是打包後的 EXE
            base_dir = os.path.dirname(sys.executable)
        else:
            # 如果是開發環境
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        setup_path = os.path.join(base_dir, "setup.json")
        
        # 檢查文件是否存在
        if not os.path.exists(setup_path):
            print(f"[ERROR] 找不到設定檔：{setup_path}")
            return
        
        # 讀取 setup.json
        with open(setup_path, 'r', encoding='utf-8') as file:
            setup_data = json.load(file)
        
        # 讀取版本號
        APP_VERSION = setup_data.get("version", "1.0.0")
        
        # 讀取通知訊息
        messages = setup_data.get("notification_messages", {})
        if messages:
            NOTIFY_TEXTS.update(messages)
            print(f"[INFO] 已載入 {len(messages)} 個通知訊息")
        else:
            print("[WARNING] 設定檔中沒有通知訊息")
            
    except Exception as e:
        print(f"[ERROR] 載入通知訊息時發生錯誤：{e}")
        import traceback
        traceback.print_exc()

def get_notification_text(key, *args):
    """獲取指定鍵的通知訊息，並進行格式化"""
    global NOTIFY_TEXTS
    
    # 如果通知訊息字典為空，先載入
    if not NOTIFY_TEXTS:
        load_notification_messages()
    
    # 獲取訊息，如果不存在則使用鍵名作為預設值
    message = NOTIFY_TEXTS.get(key, key)
    
    # 如果有參數，進行格式化
    if args:
        try:
            message = message.format(*args)
        except Exception as e:
            print(f"[ERROR] 格式化通知訊息時發生錯誤：{e}, key={key}, args={args}")
    
    return message

def get_app_version():
    """獲取應用程式版本號"""
    global APP_VERSION
    
    # 如果版本號為空，先載入
    if not APP_VERSION:
        load_notification_messages()
    
    return APP_VERSION

# 在模塊導入時自動載入通知訊息
load_notification_messages()


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
            
        # 優先查找 Command_TABLE 目錄中的文件
        if relative_path == 'command.txt':
            # 嘗試多個可能的路徑
            possible_paths = [
                os.path.join(base_path, 'Command_TABLE', 'command.txt'),  # 主目錄下的Command_TABLE
                os.path.join(base_path, 'command.txt'),                   # 主目錄
                os.path.join(os.path.dirname(base_path), 'Command_TABLE', 'command.txt')  # 上一級目錄的Command_TABLE
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    print(f"[INFO] 找到指令檔: {path}")
                    return path
                    
            print(f"[WARNING] 無法找到指令檔，將使用預設路徑: {os.path.join(base_path, relative_path)}")
            
        # 處理 Fixture_Command.txt 文件
        if relative_path == 'Fixture_Command.txt' or relative_path == 'FIXTURE/Fixture_Command.txt':
            # 嘗試多個可能的路徑
            possible_paths = [
                os.path.join(base_path, 'FIXTURE', 'Fixture_Command.txt'),  # 主目錄下的FIXTURE
                os.path.join(base_path, 'Fixture_Command.txt'),             # 主目錄
                os.path.join(os.path.dirname(base_path), 'FIXTURE', 'Fixture_Command.txt')  # 上一級目錄的FIXTURE
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    print(f"[INFO] 找到夾具指令檔: {path}")
                    return path
                    
            print(f"[WARNING] 無法找到夾具指令檔，將使用預設路徑: {os.path.join(base_path, 'FIXTURE', 'Fixture_Command.txt')}")
            return os.path.join(base_path, 'FIXTURE', 'Fixture_Command.txt')
            
        # 處理其他特殊文件
        if relative_path == 'setup.json' and not os.path.exists(os.path.join(base_path, relative_path)):
            print(f"[WARNING] 找不到設定檔，將創建默認設定檔")
            try:
                from config_core import default_setup
                import json
                with open(os.path.join(base_path, relative_path), 'w', encoding='utf-8') as f:
                    json.dump(default_setup, f, ensure_ascii=False, indent=2)
                print(f"[INFO] 已創建默認設定檔: {os.path.join(base_path, relative_path)}")
            except Exception as e:
                print(f"[ERROR] 創建默認設定檔失敗: {e}")
            
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



# 記錄錯誤訊息到日誌檔

def log_error(message):

    """記錄錯誤訊息到日誌檔"""

    try:

        # 定義錯誤日誌檔案路徑

        error_log_file = resource_path('error_log.txt')

        

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(error_log_file, 'a', encoding='utf-8') as f:

            f.write(f"[{timestamp}] {message}\n")

    except Exception as e:

        print(f"[ERROR] 無法寫入錯誤日誌: {e}") 