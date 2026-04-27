# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import sys
import json

# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from config_core import load_setup, save_setup

class UIComponentsSettings:
    def init_settings_components(self):
        settings_frame = ttk.LabelFrame(self.left_panel, text='設定', padding=5, style="TLabelframe")
        settings_frame.grid(row=4, column=0, sticky='ew', pady=5)  # 減少間距
        
        # 結束字串設定
        end_frame = ttk.Frame(settings_frame, style="TFrame")
        end_frame.grid(row=0, column=0, sticky='ew', pady=2)  # 減少間距
        self.label_end = ttk.Label(end_frame, text='結束字串:', style="TLabel")
        self.label_end.grid(row=0, column=0, sticky='w')
        self.combobox_end = ttk.Combobox(end_frame, width=15)
        self.combobox_end.grid(row=0, column=1, padx=5, sticky='ew')
        self.update_end_strings()
        self.combobox_end.set(self.parent.setup.get('Command_End_String', 'root'))
        # 加入刪除按鈕
        self.btn_remove_end = tk.Button(end_frame, text='-', command=self.parent.handlers.remove_end_string, width=2, bg='#ffcccc', fg='black')
        self.btn_remove_end.grid(row=0, column=2, padx=2)
        
        # 超時設定
        timeout_frame = ttk.Frame(settings_frame, style="TFrame")
        timeout_frame.grid(row=1, column=0, sticky='ew', pady=2)  # 減少間距
        self.label_timeout = ttk.Label(timeout_frame, text='超時(秒):', style="TLabel")
        self.label_timeout.grid(row=0, column=0, sticky='w')
        self.entry_timeout = ttk.Entry(
            timeout_frame, 
            width=8, 
            textvariable=self.shared_config.get_var('dut_timeout')
        )
        self.entry_timeout.grid(row=0, column=1, padx=5, sticky='ew')
        
        # 添加自動執行勾選框
        auto_exec_frame = ttk.Frame(settings_frame, style="TFrame")
        auto_exec_frame.grid(row=2, column=0, sticky='ew', pady=2)  # 減少間距
        self.auto_exec_var = tk.BooleanVar(value=self.parent.setup.get('Auto_Execute', False))
        self.auto_exec_checkbox = tk.Checkbutton(
            auto_exec_frame, 
            text='啟動時自動執行指令',
            variable=self.auto_exec_var,
            command=self.on_auto_exec_changed,
            bg='white',
            activebackground='white',
            highlightthickness=0,
            font=('Microsoft JhengHei UI', int(self.parent.setup.get('UI_Font_Size', '12')))
        )
        self.auto_exec_checkbox.grid(row=0, column=0, sticky='w', padx=5)

class SettingsUI:
    def __init__(self, parent):
        self.parent_frame = parent
        
        # 載入最新設定 (從 setup.json)
        self.setup = load_setup()
        self.dut_control = self.setup.get('DUT_Control', {})
        self.fixture_control = self.setup.get('Fixture_Control', {})
        
        print(f"[DEBUG] 設定頁面載入設定，Window_Title={self.setup.get('Window_Title')}")
        
        # 初始化 UI
        self.init_ui()
        
    def init_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.parent_frame, style="Main.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 標題
        title_label = ttk.Label(
            main_frame,
            text="系統設定",
            font=('Microsoft JhengHei UI', 18, 'bold'),
            style="TLabel"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky='w')
        
        # 建立 DUT 控制設定區域
        dut_frame = ttk.LabelFrame(main_frame, text="DUT 控制設定", padding=10, style="TLabelframe")
        dut_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        
        # 視窗標題設定
        ttk.Label(dut_frame, text="視窗標題:", style="TLabel").grid(row=0, column=0, sticky='w', pady=5)
        self.window_title_var = tk.StringVar()
        self.window_title_entry = ttk.Entry(dut_frame, textvariable=self.window_title_var, width=30)
        self.window_title_entry.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        # UI 字體大小設定
        ttk.Label(dut_frame, text="UI 字體大小:", style="TLabel").grid(row=1, column=0, sticky='w', pady=5)
        self.ui_font_size_var = tk.StringVar()
        self.ui_font_size_entry = ttk.Entry(dut_frame, textvariable=self.ui_font_size_var, width=10)
        self.ui_font_size_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        # 內容字體大小設定
        ttk.Label(dut_frame, text="內容字體大小:", style="TLabel").grid(row=2, column=0, sticky='w', pady=5)
        self.content_font_size_var = tk.StringVar()
        self.content_font_size_entry = ttk.Entry(dut_frame, textvariable=self.content_font_size_var, width=10)
        self.content_font_size_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5)
        
        # 命令結束字串設定
        ttk.Label(dut_frame, text="命令結束字串:", style="TLabel").grid(row=3, column=0, sticky='w', pady=5)
        self.cmd_end_string_var = tk.StringVar()
        self.cmd_end_string_entry = ttk.Entry(dut_frame, textvariable=self.cmd_end_string_var, width=20)
        self.cmd_end_string_entry.grid(row=3, column=1, sticky='w', padx=5, pady=5)
        
        # 可用結束字串設定 (顯示為文字框，用逗號分隔)
        ttk.Label(dut_frame, text="可用結束字串列表:", style="TLabel").grid(row=4, column=0, sticky='w', pady=5)
        self.available_end_strings_var = tk.StringVar()
        self.available_end_strings_entry = ttk.Entry(dut_frame, textvariable=self.available_end_strings_var, width=30)
        self.available_end_strings_entry.grid(row=4, column=1, sticky='w', padx=5, pady=5)
        tk.Label(dut_frame, text="(以逗號分隔多個值)", font=('Microsoft JhengHei UI', 8)).grid(row=4, column=2, sticky='w')
        
        # 建立治具控制設定區域
        fixture_frame = ttk.LabelFrame(main_frame, text="治具控制設定", padding=10, style="TLabelframe")
        fixture_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        
        # 測試類別設定 (Checkbutton)
        ttk.Label(fixture_frame, text="測試類別:", style="TLabel").grid(row=0, column=0, sticky='w', pady=5)
        
        # FUNCTION 測試類別
        self.test_category_function_var = tk.BooleanVar()
        self.test_category_function_cb = ttk.Checkbutton(
            fixture_frame, 
            text="FUNCTION", 
            variable=self.test_category_function_var
        )
        self.test_category_function_cb.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        # MB 測試類別
        self.test_category_mb_var = tk.BooleanVar()
        self.test_category_mb_cb = ttk.Checkbutton(
            fixture_frame, 
            text="MB", 
            variable=self.test_category_mb_var
        )
        self.test_category_mb_cb.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        # Original_Commands 測試類別
        self.test_category_original_var = tk.BooleanVar()
        self.test_category_original_cb = ttk.Checkbutton(
            fixture_frame, 
            text="原始指令", 
            variable=self.test_category_original_var
        )
        self.test_category_original_cb.grid(row=2, column=1, sticky='w', padx=5, pady=5)
        
        # 治具字體大小設定
        ttk.Label(fixture_frame, text="治具字體大小:", style="TLabel").grid(row=3, column=0, sticky='w', pady=5)
        self.fixture_font_size_var = tk.StringVar()
        self.fixture_font_size_entry = ttk.Entry(fixture_frame, textvariable=self.fixture_font_size_var, width=10)
        self.fixture_font_size_entry.grid(row=3, column=1, sticky='w', padx=5, pady=5)
        
        # 儲存按鈕
        save_frame = ttk.Frame(main_frame, style="TFrame")
        save_frame.grid(row=2, column=0, columnspan=2, pady=20, sticky='e')
        
        self.save_button = ttk.Button(
            save_frame,
            text="儲存設定",
            command=self.save_settings,
            style="TButton"
        )
        self.save_button.pack(side=tk.RIGHT, padx=5)
        
        # 重置按鈕
        self.reset_button = ttk.Button(
            save_frame,
            text="重置",
            command=self.reset_settings,
            style="TButton"
        )
        self.reset_button.pack(side=tk.RIGHT, padx=5)
        
        # 從配置初始化所有UI欄位值
        self.update_ui_from_config()
    
    def activate(self):
        """當分頁被選中時調用"""
        # 重新載入設定 (從 setup.json)
        self.setup = load_setup()
        self.dut_control = self.setup.get('DUT_Control', {})
        self.fixture_control = self.setup.get('Fixture_Control', {})
        
        # 更新 UI 顯示目前讀到的設定值
        self.update_ui_from_config()
    
    def update_ui_from_config(self):
        """從目前載入的設定更新 UI 欄位"""
        # 更新 DUT 控制設定
        self.window_title_var.set(self.setup.get('Window_Title', ''))
        self.ui_font_size_var.set(self.dut_control.get('UI_Font_Size', ''))
        self.content_font_size_var.set(self.dut_control.get('Content_Font_Size', ''))
        self.cmd_end_string_var.set(self.dut_control.get('Command_End_String', ''))
        
        available_end_strings = self.dut_control.get('Available_End_Strings', [])
        if isinstance(available_end_strings, list) and available_end_strings:
            end_strings_text = ", ".join(available_end_strings)
        else:
            end_strings_text = self.dut_control.get('Command_End_String', '')
        self.available_end_strings_var.set(end_strings_text)
        
        # 更新治具控制設定
        self.test_category_function_var.set(self.fixture_control.get('Test_Category_FUNCTION', False))
        self.test_category_mb_var.set(self.fixture_control.get('Test_Category_MB', True))
        self.test_category_original_var.set(self.fixture_control.get('Test_Category_Original_Commands', False))
        self.fixture_font_size_var.set(self.fixture_control.get('Fixture_Font_Size', ''))
    
    def reset_settings(self):
        """重置設定為目前載入的值 (從 setup.json 重新讀取)"""
        # 重新載入設定確保最新值
        self.setup = load_setup()
        self.dut_control = self.setup.get('DUT_Control', {})
        self.fixture_control = self.setup.get('Fixture_Control', {})
        
        print(f"[DEBUG] 重置設定，從 setup.json 重新載入，Window_Title={self.setup.get('Window_Title')}")
        
        # 更新 UI 顯示目前讀到的設定值
        self.update_ui_from_config()
        
        # 顯示重置成功消息
        messagebox.showinfo("成功", "已重置為目前儲存的設定")
    
    def save_settings(self):
        """儲存設定到 setup.json"""
        try:
            # 讀取當前設定
            current_setup = load_setup()
            
            # 更新 Window_Title (頂層)
            current_setup['Window_Title'] = self.window_title_var.get()
            
            # 更新 DUT_Control 設定
            current_setup['DUT_Control']['UI_Font_Size'] = self.ui_font_size_var.get()
            current_setup['DUT_Control']['Content_Font_Size'] = self.content_font_size_var.get()
            current_setup['DUT_Control']['Command_End_String'] = self.cmd_end_string_var.get()
            
            # 處理可用結束字串列表
            end_strings_text = self.available_end_strings_var.get()
            end_strings_list = [s.strip() for s in end_strings_text.split(',') if s.strip()]
            if not end_strings_list:  # 確保至少有一個值
                end_strings_list = ["root"]
            current_setup['DUT_Control']['Available_End_Strings'] = end_strings_list
            
            # 更新 Fixture_Control 設定
            current_setup['Fixture_Control']['Test_Category_FUNCTION'] = self.test_category_function_var.get()
            current_setup['Fixture_Control']['Test_Category_MB'] = self.test_category_mb_var.get()
            current_setup['Fixture_Control']['Test_Category_Original_Commands'] = self.test_category_original_var.get()
            current_setup['Fixture_Control']['Fixture_Font_Size'] = self.fixture_font_size_var.get()
            
            # 確保 DUT_Control 中的 Window_Title 與頂層一致
            current_setup['DUT_Control']['Window_Title'] = self.window_title_var.get()
            
            print(f"[DEBUG] 儲存設定，Window_Title={self.window_title_var.get()}")
            
            # 保存設定
            save_setup(current_setup)
            
            messagebox.showinfo("成功", "設定已儲存")
            
            # 更新主視窗標題
            if hasattr(self, 'parent_frame') and hasattr(self.parent_frame, 'master'):
                root = self.parent_frame.master
                if hasattr(root, 'title'):
                    version = root.title().split(' ')[-1] if ' ' in root.title() else ''
                    new_title = f"{self.window_title_var.get()} {version}"
                    root.title(new_title)
                    print(f"[DEBUG] 已更新主視窗標題為: {new_title}")
        
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存設定時發生錯誤: {e}") 