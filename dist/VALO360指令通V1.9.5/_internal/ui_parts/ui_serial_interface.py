# -*- coding: utf-8 -*-
"""
序列通訊介面模組
負責處理序列通訊相關的UI和邏輯
從 ui_main.py 中的 SerialUI 類別拆分而來
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
from datetime import datetime
import subprocess
import webbrowser
import logging

import config_core
import config_utils
from config_utils import get_notification_text, get_app_version

# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 導入配置模組
try:
    from config_core import load_setup, save_setup, list_com_ports, GUIDE_FILE, COMMAND_FILE, load_commands
except ImportError as e:
    print(f"導入 config_core 模組失敗: {e}")
    print(f"當前路徑: {sys.path}")
    sys.exit(1)

try:
    from serial_worker import SerialWorker
    from ui_parts.ui_components import UIComponents
    from ui_parts.ui_handlers import UIHandlers
except ImportError as e:
    print(f"導入模組失敗: {e}")
    sys.exit(1)


class SerialUI:
    """主應用程式的序列通訊 UI 框架"""
    
    def __init__(self, parent, root, highlight_keywords=None):
        """
        初始化 SerialUI
        
        Args:
            parent: 父級 tk 元件
            root: 主視窗
            highlight_keywords: 高亮關鍵字字典
        """
        self.parent = parent
        self.root = root
        self.highlight_keywords = highlight_keywords or {}
        
        # 載入設定
        self.setup = load_setup()
        
        # 初始化停止事件
        self.stop_event = threading.Event()
        
        # 初始化樣式
        self.init_styles()

        # 初始化事件處理器
        self.init_handlers()

        # 初始化 UI 元件
        self.init_components()

        # 啟動 UI
        self.activate()
        
        print("[DEBUG] SerialUI 初始化完成")
    
    def init_styles(self):
        """初始化樣式"""
        try:
            self.style = ttk.Style()
            
            # 設定基本樣式
            self.style.configure('TFrame', background='#f0f0f0')
            self.style.configure('TLabel', background='#f0f0f0')
            self.style.configure('TButton', padding=6)
            
            # 設定特殊樣式
            self.style.configure('Status.TLabel', 
                               foreground='green', 
                               background='#f0f0f0',
                               font=('Arial', 10, 'bold'))
            
            print("[DEBUG] SerialUI 樣式初始化完成")
        except Exception as e:
            print(f"[ERROR] 初始化 SerialUI 樣式時發生錯誤: {e}")
    
    def init_components(self):
        """初始化 UI 元件"""
        try:
            # 創建 UI 元件
            self.components = UIComponents(self, self.handlers, self.root)

            print("[DEBUG] SerialUI 元件初始化完成")
        except Exception as e:
            print(f"[ERROR] 初始化 SerialUI 元件時發生錯誤: {e}")

    def init_handlers(self):
        """初始化事件處理器"""
        try:
            # 創建事件處理器
            # 注意：這裡需要確保 self 有必要的屬性
            if not hasattr(self, 'config'):
                self.config = self.setup  # 為了向後相容

            self.handlers = UIHandlers(self, self.setup, self.highlight_keywords)

            print("[DEBUG] SerialUI 事件處理器初始化完成")
        except Exception as e:
            print(f"[ERROR] 初始化 SerialUI 事件處理器時發生錯誤: {e}")
    
    def activate(self):
        """啟動 UI"""
        try:
            # 載入並應用設定
            self.reload_and_apply_settings()
            
            # 更新 UI 狀態
            self.update_from_config()
            
            print("[DEBUG] SerialUI 已啟動")
        except Exception as e:
            print(f"[ERROR] 啟動 SerialUI 時發生錯誤: {e}")
    
    def on_close(self):
        """處理關閉事件"""
        try:
            print("[DEBUG] 開始關閉 SerialUI...")
            
            # 停止所有正在運行的任務
            self.stop_event.set()
            
            # 保存設定
            try:
                save_setup(self.setup)
                print("[DEBUG] SerialUI 設定已保存")
            except Exception as e:
                print(f"[WARNING] 保存 SerialUI 設定時發生錯誤: {e}")
            
            print("[DEBUG] SerialUI 已關閉")
            
        except Exception as e:
            print(f"[ERROR] 關閉 SerialUI 時發生錯誤: {e}")
    
    def get_settings_from_ui(self):
        """從 UI 獲取設定"""
        try:
            settings = {}
            
            # 獲取 DUT 控制設定
            if hasattr(self.components, 'combobox_com'):
                settings['Serial_COM_Port'] = self.components.combobox_com.get()
            
            if hasattr(self.components, 'combobox_timeout'):
                settings['Command_Timeout_Seconds'] = self.components.combobox_timeout.get()
            
            if hasattr(self.components, 'combobox_cmd'):
                settings['Selected_Command'] = self.components.combobox_cmd.get()
            
            return settings
            
        except Exception as e:
            print(f"[ERROR] 從 UI 獲取設定時發生錯誤: {e}")
            return {}
    
    def get_settings(self):
        """獲取當前設定"""
        try:
            return self.setup.copy()
        except Exception as e:
            print(f"[ERROR] 獲取設定時發生錯誤: {e}")
            return {}
    
    def reload_and_apply_settings(self):
        """重新載入並應用設定"""
        try:
            # 重新載入設定
            self.setup = load_setup()
            
            # 應用設定到 UI
            self.update_from_config()
            
            print("[DEBUG] SerialUI 設定已重新載入並應用")
        except Exception as e:
            print(f"[ERROR] 重新載入設定時發生錯誤: {e}")
    
    def update_from_config(self):
        """集中管理所有 UI 元件的設定同步"""
        try:
            # 更新 COM 端口設定
            if hasattr(self.components, 'combobox_com'):
                dut_setup = self.setup.get('DUT_Control', {})
                com_port = dut_setup.get('Serial_COM_Port', '')
                if com_port:
                    self.components.combobox_com.set(com_port)
            
            # 更新超時設定
            if hasattr(self.components, 'combobox_timeout'):
                timeout = self.setup.get('DUT_Control', {}).get('Command_Timeout_Seconds', '10')
                self.components.combobox_timeout.set(timeout)
            
            # 更新其他設定
            # 這裡可以添加更多設定的同步邏輯
            
            print("[DEBUG] SerialUI 設定同步完成")
        except Exception as e:
            print(f"[ERROR] 同步 SerialUI 設定時發生錯誤: {e}")
    
    def _safe_execute_command(self):
        """安全地在背景執行指令"""
        try:
            # 這裡會實現安全的命令執行邏輯
            # 具體實現會在後續添加
            pass
        except Exception as e:
            print(f"[ERROR] 執行命令時發生錯誤: {e}")


def fixtureframe_get_settings():
    """獲取治具框架設定的輔助函數"""
    try:
        setup = load_setup()
        return setup.get('Fixture_Control', {})
    except Exception as e:
        print(f"[ERROR] 獲取治具框架設定時發生錯誤: {e}")
        return {}
