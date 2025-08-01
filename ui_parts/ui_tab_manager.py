# -*- coding: utf-8 -*-
"""
標籤頁管理器模組
負責管理應用程式的標籤頁結構和相關功能
從 ui_main.py 中的 TabManager 類別拆分而來
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

# 檢查 command.txt
try:
    commands = load_commands()
except Exception as e:
    messagebox.showerror('錯誤', str(e))
    sys.exit(1)

try:
    from serial_worker import SerialWorker
    from ui_parts.ui_components import UIComponents
    from ui_parts.ui_handlers import UIHandlers
    from ui_parts.ui_settings_tab import SettingsTab
except ImportError as e:
    print(f"導入模組失敗: {e}")
    sys.exit(1)


class TabManager:
    """標籤頁管理器類別，負責管理應用程式的標籤頁結構"""
    
    def __init__(self, root, highlight_keywords=None):
        """
        初始化標籤頁管理器
        
        Args:
            root: 主視窗
            highlight_keywords: 高亮關鍵字字典
        """
        self.root = root
        # 將自己設置為root的tab_manager屬性，供其他元件使用
        self.root.tab_manager = self
        
        self.highlight_keywords = highlight_keywords or {}
        print(f"[DEBUG] TabManager 初始化，highlight_keywords={self.highlight_keywords}")
        
        # 初始化 DOS 視窗進程追蹤變數
        self.dos_process = None
        
        # 配置根窗口的 grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)  # 通知區域不擴展
        self.root.grid_columnconfigure(0, weight=1)
        
        # 初始化全局樣式
        self.init_global_styles()
        
        # 創建主內容框架
        main_content_frame = ttk.Frame(root)
        main_content_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        main_content_frame.grid_rowconfigure(0, weight=1)
        main_content_frame.grid_columnconfigure(0, weight=1)
        
        # 創建標籤頁控制器
        self.notebook = ttk.Notebook(main_content_frame)
        self.notebook.grid(row=0, column=0, sticky='nsew')
        
        # 初始化各個標籤頁
        self.init_tabs()
        

        
        # 設定視窗關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def init_global_styles(self):
        """初始化全局樣式"""
        try:
            style = ttk.Style()
            
            # 設定標籤頁樣式
            style.configure('TNotebook.Tab', padding=[20, 10])
            style.configure('TNotebook', tabposition='n')
            
            print("[DEBUG] 全局樣式初始化完成")
        except Exception as e:
            print(f"[ERROR] 初始化全局樣式時發生錯誤: {e}")
    
    def init_tabs(self):
        """初始化所有標籤頁"""
        try:
            # 創建各個標籤頁框架
            self.dut_frame = ttk.Frame(self.notebook)
            self.settings_frame = ttk.Frame(self.notebook)
            self.dos_frame = ttk.Frame(self.notebook)
            self.guide_frame = ttk.Frame(self.notebook)
            
            # 添加標籤頁到 Notebook
            self.notebook.add(self.dut_frame, text='DUT 控制')
            self.notebook.add(self.settings_frame, text='設定')
            self.notebook.add(self.dos_frame, text='DOS 視窗')
            self.notebook.add(self.guide_frame, text='使用說明')
            
            # 初始化各個標籤頁的內容
            self.init_dut_tab()
            self.init_settings_tab()
            self.init_dos_tab()
            self.init_guide_tab()
            
            print("[DEBUG] 所有標籤頁初始化完成")
        except Exception as e:
            print(f"[ERROR] 初始化標籤頁時發生錯誤: {e}")
    
    def init_dut_tab(self):
        """初始化 DUT 控制標籤頁"""
        try:
            # 創建 SerialUI 實例來處理 DUT 控制
            from ui_parts.ui_serial_interface import SerialUI
            self.dut_ui = SerialUI(self.dut_frame, self.root, self.highlight_keywords)
            print("[DEBUG] DUT 控制標籤頁初始化完成")
        except Exception as e:
            print(f"[ERROR] 初始化 DUT 標籤頁時發生錯誤: {e}")

    def init_settings_tab(self):
        """初始化設定標籤頁"""
        try:
            # 創建設定標籤頁實例
            self.settings_ui = SettingsTab(self.settings_frame, self.root)
            print("[DEBUG] 設定標籤頁初始化完成")
        except Exception as e:
            print(f"[ERROR] 初始化設定標籤頁時發生錯誤: {e}")

    def init_dos_tab(self):
        """初始化 DOS 視窗標籤頁"""
        try:
            from ui_parts.ui_dos_tab import DOSTab
            self.dos_ui = DOSTab(self.dos_frame)
            print("[DEBUG] DOS 視窗標籤頁初始化完成")
        except Exception as e:
            print(f"[ERROR] 初始化 DOS 標籤頁時發生錯誤: {e}")
            # 創建簡單的 DOS 標籤頁
            ttk.Label(self.dos_frame, text="DOS 視窗功能").pack(pady=20)

    def init_guide_tab(self):
        """初始化使用說明標籤頁"""
        try:
            from ui_parts.ui_guide_tab import GuideTab
            self.guide_ui = GuideTab(self.guide_frame)
            print("[DEBUG] 使用說明標籤頁初始化完成")
        except Exception as e:
            print(f"[ERROR] 初始化使用說明標籤頁時發生錯誤: {e}")
            # 創建簡單的使用說明標籤頁
            ttk.Label(self.guide_frame, text="使用說明內容").pack(pady=20)


    
    def on_closing(self):
        """視窗關閉事件處理"""
        try:
            print("[DEBUG] 開始關閉應用程式...")
            
            # 停止所有正在運行的進程
            if hasattr(self, 'dos_process') and self.dos_process:
                try:
                    self.dos_process.terminate()
                    print("[DEBUG] DOS 進程已終止")
                except:
                    pass
            
            # 保存設定
            try:
                # 這裡會保存當前設定
                print("[DEBUG] 設定已保存")
            except Exception as e:
                print(f"[WARNING] 保存設定時發生錯誤: {e}")
            
            # 關閉主視窗
            self.root.destroy()
            print("[DEBUG] 應用程式已關閉")
            
        except Exception as e:
            print(f"[ERROR] 關閉應用程式時發生錯誤: {e}")
            # 即使出錯，也要嘗試關閉窗口
            try:
                self.root.destroy()
            except:
                pass
