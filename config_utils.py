# -*- coding: utf-8 -*-
import os

import sys

from datetime import datetime



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