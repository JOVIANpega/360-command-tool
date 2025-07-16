# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import json

# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from config_core import load_setup, save_setup
from ui_parts.tooltip import ToolTipManager

class SettingsTab(ttk.Frame):
    def __init__(self, parent, on_save_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.on_save_callback = on_save_callback
        self.setup_data = load_setup()
        self.vars = {}
        
        # 字體大小追蹤變數 (用於即時更新)
        self.font_size_trace_active = False
        
        # 初始化 ToolTip 管理器
        try:
            # 找到主視窗
            root_widget = self
            while root_widget.master:
                root_widget = root_widget.master
            self.tooltip_manager = ToolTipManager(root_widget)
        except Exception as e:
            print(f"初始化 ToolTip 管理器失敗: {e}")
            self.tooltip_manager = None
        
        self.create_widgets()
        self.setup_tooltips()

    def create_widgets(self):
        # 創建主容器，不使用Canvas滾動，直接使用緊湊佈局
        main_container = ttk.Frame(self)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        
        current_row = 0
        
        # 儲存按鈕區域 - 調整位置到最上方，尺寸更大
        button_frame = ttk.Frame(main_container)
        button_frame.grid(row=current_row, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        current_row += 1
        
        # 置右的儲存按鈕容器
        save_frame = ttk.Frame(button_frame)
        save_frame.pack(side=tk.RIGHT)
        
        # 更大尺寸的儲存按鈕
        self.save_button = ttk.Button(save_frame, text="儲存設定", command=self.save_settings, 
                                     style="Accent.TButton", width=15)
        self.save_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # --- 第一排：應用程式基本設定 + 標籤頁名稱設定 ---
        # 左側：應用程式基本設定
        basic_frame = ttk.LabelFrame(main_container, text="應用程式基本設定", padding=(10, 4))
        basic_frame.grid(row=current_row, column=0, sticky="nsew", padx=(0, 5), pady=(0, 8))
        basic_frame.columnconfigure(1, weight=1)
        
        # 應用程式版本
        ttk.Label(basic_frame, text="應用程式版本:").grid(row=0, column=0, sticky="w", pady=4)
        self.vars["version"] = tk.StringVar(value=self.setup_data.get("version", "V1.5.0.2"))
        ttk.Entry(basic_frame, textvariable=self.vars["version"], width=30).grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)
        
        # 視窗標題
        ttk.Label(basic_frame, text="視窗標題:").grid(row=1, column=0, sticky="w", pady=4)
        self.vars["Window_Title"] = tk.StringVar(value=self.setup_data.get("Window_Title", "VALO360 指令通"))
        ttk.Entry(basic_frame, textvariable=self.vars["Window_Title"], width=30).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=4)
        
        # 視窗大小 - 使用水平排版
        size_frame = ttk.Frame(basic_frame)
        size_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=4)
        size_frame.columnconfigure(1, weight=1)
        size_frame.columnconfigure(3, weight=1)
        
        ttk.Label(size_frame, text="視窗寬度:").grid(row=0, column=0, sticky="w")
        self.vars["Window_Width"] = tk.StringVar(value=self.setup_data.get("Window_Width", "1536"))
        ttk.Entry(size_frame, textvariable=self.vars["Window_Width"], width=8).grid(row=0, column=1, sticky="ew", padx=(5, 10))
        
        ttk.Label(size_frame, text="高度:").grid(row=0, column=2, sticky="w")
        self.vars["Window_Height"] = tk.StringVar(value=self.setup_data.get("Window_Height", "793"))
        ttk.Entry(size_frame, textvariable=self.vars["Window_Height"], width=8).grid(row=0, column=3, sticky="ew", padx=(5, 0))
        
        # 右側：標籤頁名稱設定
        tab_frame = ttk.LabelFrame(main_container, text="標籤頁名稱設定", padding=(10, 4))
        tab_frame.grid(row=current_row, column=1, sticky="nsew", padx=(5, 0), pady=(0, 8))
        tab_frame.columnconfigure(1, weight=1)
        current_row += 1
        
        # 獲取當前的標籤頁名稱
        tab_names = self.setup_data.get('tab_names', {})
        default_tab_names = ['DUT 控制', '治具控制', '使用說明', '設定']
        
        # 創建標籤頁名稱輸入框
        for i in range(4):
            tab_key = f'tab{i}'
            tab_name = tab_names.get(tab_key, default_tab_names[i])
            ttk.Label(tab_frame, text=f"標籤頁 {i+1}:").grid(row=i, column=0, sticky="w", pady=4)
            self.vars[f"tab_names_{tab_key}"] = tk.StringVar(value=tab_name)
            ttk.Entry(tab_frame, textvariable=self.vars[f"tab_names_{tab_key}"], width=25).grid(row=i, column=1, sticky="ew", padx=(10, 0), pady=4)
        
        # --- 第二排：DUT 控制設定 + 治具控制設定 ---
        # 左側：DUT 控制設定
        dut_frame = ttk.LabelFrame(main_container, text="DUT 控制設定", padding=(10, 4))
        dut_frame.grid(row=current_row, column=0, sticky="nsew", padx=(0, 5), pady=(0, 8))
        dut_frame.columnconfigure(1, weight=1)
        
        dut_settings = self.setup_data.get('DUT_Control', {})
        dut_row = 0
        
        # 串口設定
        ttk.Label(dut_frame, text="串口:").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Serial_COM_Port"] = tk.StringVar(value=dut_settings.get("Serial_COM_Port", "COM5"))
        ttk.Entry(dut_frame, textvariable=self.vars["DUT_Serial_COM_Port"], width=25).grid(row=dut_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        dut_row += 1
        
        # 指令超時
        ttk.Label(dut_frame, text="指令超時(秒):").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Command_Timeout_Seconds"] = tk.StringVar(value=dut_settings.get("Command_Timeout_Seconds", "30"))
        ttk.Entry(dut_frame, textvariable=self.vars["DUT_Command_Timeout_Seconds"], width=25).grid(row=dut_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        dut_row += 1
        
        # 指令結束字串
        ttk.Label(dut_frame, text="指令結束字串:").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Command_End_String"] = tk.StringVar(value=dut_settings.get("Command_End_String", "root"))
        ttk.Entry(dut_frame, textvariable=self.vars["DUT_Command_End_String"], width=25).grid(row=dut_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        dut_row += 1
        
        # 預設IP地址
        ttk.Label(dut_frame, text="預設IP地址:").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Default_IP_Address"] = tk.StringVar(value=dut_settings.get("Default_IP_Address", "192.168.11.143"))
        ttk.Entry(dut_frame, textvariable=self.vars["DUT_Default_IP_Address"], width=25).grid(row=dut_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        dut_row += 1
        
        # 字體設定 - 水平排版，並加入即時更新功能
        font_frame = ttk.Frame(dut_frame)
        font_frame.grid(row=dut_row, column=0, columnspan=2, sticky="ew", pady=4)
        font_frame.columnconfigure(1, weight=1)
        font_frame.columnconfigure(3, weight=1)
        
        ttk.Label(font_frame, text="介面字體:").grid(row=0, column=0, sticky="w")
        self.vars["DUT_UI_Font_Size"] = tk.StringVar(value=dut_settings.get("UI_Font_Size", "13"))
        self.ui_font_spinbox = ttk.Spinbox(font_frame, textvariable=self.vars["DUT_UI_Font_Size"], 
                                          from_=8, to=24, width=6, command=self.on_ui_font_changed)
        self.ui_font_spinbox.grid(row=0, column=1, sticky="ew", padx=(5, 10))
        # 綁定 Enter 鍵和失去焦點事件
        self.ui_font_spinbox.bind('<Return>', self.on_ui_font_changed)
        self.ui_font_spinbox.bind('<FocusOut>', self.on_ui_font_changed)
        
        ttk.Label(font_frame, text="內容字體:").grid(row=0, column=2, sticky="w")
        self.vars["DUT_Content_Font_Size"] = tk.StringVar(value=dut_settings.get("Content_Font_Size", "11"))
        self.content_font_spinbox = ttk.Spinbox(font_frame, textvariable=self.vars["DUT_Content_Font_Size"], 
                                               from_=8, to=24, width=6, command=self.on_content_font_changed)
        self.content_font_spinbox.grid(row=0, column=3, sticky="ew", padx=(5, 0))
        # 綁定 Enter 鍵和失去焦點事件
        self.content_font_spinbox.bind('<Return>', self.on_content_font_changed)
        self.content_font_spinbox.bind('<FocusOut>', self.on_content_font_changed)
        dut_row += 1
        
        # 通知字體大小設定
        ttk.Label(dut_frame, text="通知字體大小:").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Notification_Font_Size"] = tk.StringVar(value=dut_settings.get("Notification_Font_Size", "10"))
        self.notification_font_spinbox = ttk.Spinbox(dut_frame, textvariable=self.vars["DUT_Notification_Font_Size"], 
                                                    from_=8, to=20, width=6, command=self.on_notification_font_changed)
        self.notification_font_spinbox.grid(row=dut_row, column=1, sticky="w", padx=(10, 0), pady=4)
        # 綁定 Enter 鍵和失去焦點事件
        self.notification_font_spinbox.bind('<Return>', self.on_notification_font_changed)
        self.notification_font_spinbox.bind('<FocusOut>', self.on_notification_font_changed)
        dut_row += 1
        
        # 分隔面板位置
        ttk.Label(dut_frame, text="分隔面板位置:").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Pane_Sash_Position"] = tk.StringVar(value=dut_settings.get("Pane_Sash_Position", "633"))
        ttk.Entry(dut_frame, textvariable=self.vars["DUT_Pane_Sash_Position"], width=25).grid(row=dut_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        dut_row += 1
        
        # 自動執行設定
        self.vars["DUT_Auto_Execute"] = tk.BooleanVar(value=dut_settings.get("Auto_Execute", False))
        ttk.Checkbutton(dut_frame, text="啟用自動執行", variable=self.vars["DUT_Auto_Execute"]).grid(row=dut_row, column=0, columnspan=2, sticky="w", pady=4)
        dut_row += 1
        
        # ToolTip 設定
        ui_settings = self.setup_data.get('UI_Settings', {})
        self.vars["UI_ToolTip_Enabled"] = tk.BooleanVar(value=ui_settings.get("ToolTip_Enabled", True))
        
        self.tooltip_checkbox = ttk.Checkbutton(dut_frame, text="啟用提示說明（ToolTip）", 
                                              variable=self.vars["UI_ToolTip_Enabled"],
                                              command=self.on_tooltip_setting_changed)
        self.tooltip_checkbox.grid(row=dut_row, column=0, columnspan=2, sticky="w", pady=4)
        dut_row += 1
        
        # 指令檔案路徑 - 設定為150字元長度
        ttk.Label(dut_frame, text="指令檔案路徑:").grid(row=dut_row, column=0, sticky="w", pady=4)
        path_frame = ttk.Frame(dut_frame)
        path_frame.grid(row=dut_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        path_frame.columnconfigure(0, weight=1)
        self.vars["DUT_Command_File_Path"] = tk.StringVar(value=dut_settings.get("Command_File_Path", ""))
        ttk.Entry(path_frame, textvariable=self.vars["DUT_Command_File_Path"], width=150).grid(row=0, column=0, sticky="ew")
        self.browse_button = ttk.Button(path_frame, text="瀏覽", command=lambda: self.browse_file("DUT_Command_File_Path"))
        self.browse_button.grid(row=0, column=1, padx=(5,0))
        dut_row += 1
        
        # 右側：治具控制設定
        fixture_frame = ttk.LabelFrame(main_container, text="治具控制設定", padding=(10, 4))
        fixture_frame.grid(row=current_row, column=1, sticky="nsew", padx=(5, 0), pady=(0, 8))
        fixture_frame.columnconfigure(1, weight=1)
        current_row += 1
        
        fixture_settings = self.setup_data.get('Fixture_Control', {})
        fixture_row = 0
        
        # 治具串口
        ttk.Label(fixture_frame, text="治具串口:").grid(row=fixture_row, column=0, sticky="w", pady=4)
        self.vars["Fixture_COM_Port"] = tk.StringVar(value=fixture_settings.get("Fixture_COM_Port", "COM5"))
        ttk.Entry(fixture_frame, textvariable=self.vars["Fixture_COM_Port"], width=25).grid(row=fixture_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        fixture_row += 1
        
        # 治具字體大小 (與介面字體聯動)
        ttk.Label(fixture_frame, text="治具字體大小:").grid(row=fixture_row, column=0, sticky="w", pady=4)
        self.vars["Fixture_Font_Size"] = tk.StringVar(value=fixture_settings.get("Fixture_Font_Size", "11"))
        self.fixture_font_spinbox = ttk.Spinbox(fixture_frame, textvariable=self.vars["Fixture_Font_Size"], 
                                               from_=8, to=24, width=6, command=self.on_fixture_font_changed)
        self.fixture_font_spinbox.grid(row=fixture_row, column=1, sticky="w", padx=(10, 0), pady=4)
        # 綁定 Enter 鍵和失去焦點事件
        self.fixture_font_spinbox.bind('<Return>', self.on_fixture_font_changed)
        self.fixture_font_spinbox.bind('<FocusOut>', self.on_fixture_font_changed)
        fixture_row += 1
        
        # 測試類別
        tk.Label(fixture_frame, text="測試類別:", font=('Microsoft JhengHei UI', 10, 'bold')).grid(row=fixture_row, column=0, columnspan=2, sticky="w", pady=(10,4))
        fixture_row += 1
        
        self.vars["Fixture_Test_Category_FUNCTION"] = tk.BooleanVar(value=fixture_settings.get("Test_Category_FUNCTION", True))
        ttk.Checkbutton(fixture_frame, text="FUNCTION測試", variable=self.vars["Fixture_Test_Category_FUNCTION"]).grid(row=fixture_row, column=0, columnspan=2, sticky="w", pady=4)
        fixture_row += 1
        
        self.vars["Fixture_Test_Category_MB"] = tk.BooleanVar(value=fixture_settings.get("Test_Category_MB", True))
        ttk.Checkbutton(fixture_frame, text="MB測試", variable=self.vars["Fixture_Test_Category_MB"]).grid(row=fixture_row, column=0, columnspan=2, sticky="w", pady=4)
        fixture_row += 1
        
        self.vars["Fixture_Test_Category_Original_Commands"] = tk.BooleanVar(value=fixture_settings.get("Test_Category_Original_Commands", True))
        ttk.Checkbutton(fixture_frame, text="原始指令測試", variable=self.vars["Fixture_Test_Category_Original_Commands"]).grid(row=fixture_row, column=0, columnspan=2, sticky="w", pady=4)
        fixture_row += 1
        
        # 串列埠設定
        tk.Label(fixture_frame, text="串列埠設定:", font=('Microsoft JhengHei UI', 10, 'bold')).grid(row=fixture_row, column=0, columnspan=2, sticky="w", pady=(10,4))
        fixture_row += 1
        
        # 取得串列埠設定
        serial_settings = fixture_settings.get("Serial_Settings", {})
        
        # 波特率
        ttk.Label(fixture_frame, text="波特率:").grid(row=fixture_row, column=0, sticky="w", pady=4)
        self.vars["Fixture_Serial_Baudrate"] = tk.StringVar(value=serial_settings.get("Baudrate", "9600"))
        baudrate_combo = ttk.Combobox(fixture_frame, textvariable=self.vars["Fixture_Serial_Baudrate"], 
                                     values=["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"], 
                                     width=22, state="readonly")
        baudrate_combo.grid(row=fixture_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        fixture_row += 1
        
        # 資料位元
        ttk.Label(fixture_frame, text="資料位元:").grid(row=fixture_row, column=0, sticky="w", pady=4)
        self.vars["Fixture_Serial_Bytesize"] = tk.StringVar(value=serial_settings.get("Bytesize", "8"))
        bytesize_combo = ttk.Combobox(fixture_frame, textvariable=self.vars["Fixture_Serial_Bytesize"], 
                                     values=["5", "6", "7", "8"], width=22, state="readonly")
        bytesize_combo.grid(row=fixture_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        fixture_row += 1
        
        # 停止位元
        ttk.Label(fixture_frame, text="停止位元:").grid(row=fixture_row, column=0, sticky="w", pady=4)
        self.vars["Fixture_Serial_Stopbits"] = tk.StringVar(value=serial_settings.get("Stopbits", "1"))
        stopbits_combo = ttk.Combobox(fixture_frame, textvariable=self.vars["Fixture_Serial_Stopbits"], 
                                     values=["1", "1.5", "2"], width=22, state="readonly")
        stopbits_combo.grid(row=fixture_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        fixture_row += 1
        
        # 奇偶校驗
        ttk.Label(fixture_frame, text="奇偶校驗:").grid(row=fixture_row, column=0, sticky="w", pady=4)
        self.vars["Fixture_Serial_Parity"] = tk.StringVar(value=serial_settings.get("Parity", "None"))
        parity_combo = ttk.Combobox(fixture_frame, textvariable=self.vars["Fixture_Serial_Parity"], 
                                   values=["None", "Even", "Odd", "Mark", "Space"], width=22, state="readonly")
        parity_combo.grid(row=fixture_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        fixture_row += 1
        
        # 超時時間
        ttk.Label(fixture_frame, text="超時時間(秒):").grid(row=fixture_row, column=0, sticky="w", pady=4)
        self.vars["Fixture_Serial_Timeout"] = tk.StringVar(value=serial_settings.get("Timeout", "1.0"))
        ttk.Entry(fixture_frame, textvariable=self.vars["Fixture_Serial_Timeout"], width=25).grid(row=fixture_row, column=1, sticky="ew", padx=(10, 0), pady=4)

    def on_ui_font_changed(self, event=None):
        """介面字體大小即時更新"""
        try:
            new_size = self.vars["DUT_UI_Font_Size"].get()
            if new_size.isdigit():
                size = int(new_size)
                if 8 <= size <= 24:
                    # 立即更新設定檔
                    settings = load_setup()
                    if 'DUT_Control' not in settings:
                        settings['DUT_Control'] = {}
                    settings['DUT_Control']['UI_Font_Size'] = str(size)
                    settings['UIFontSize'] = size  # 全域字體設定
                    save_setup(settings)
                    
                    # 通知其他元件更新字體
                    self.apply_font_changes_immediately()
        except Exception as e:
            print(f"更新介面字體時發生錯誤: {e}")

    def on_content_font_changed(self, event=None):
        """內容字體大小即時更新"""
        try:
            new_size = self.vars["DUT_Content_Font_Size"].get()
            if new_size.isdigit():
                size = int(new_size)
                if 8 <= size <= 24:
                    # 立即更新設定檔
                    settings = load_setup()
                    if 'DUT_Control' not in settings:
                        settings['DUT_Control'] = {}
                    settings['DUT_Control']['Content_Font_Size'] = str(size)
                    settings['ContentFontSize'] = size  # 全域內容字體設定
                    save_setup(settings)
                    
                    # 通知其他元件更新字體
                    self.apply_font_changes_immediately()
        except Exception as e:
            print(f"更新內容字體時發生錯誤: {e}")

    def on_notification_font_changed(self, event=None):
        """通知字體大小即時更新"""
        try:
            new_size = self.vars["DUT_Notification_Font_Size"].get()
            if new_size.isdigit():
                size = int(new_size)
                if 8 <= size <= 20:
                    # 立即更新設定檔
                    settings = load_setup()
                    if 'DUT_Control' not in settings:
                        settings['DUT_Control'] = {}
                    settings['DUT_Control']['Notification_Font_Size'] = str(size)
                    save_setup(settings)
                    
                    # 通知其他元件更新字體
                    self.apply_font_changes_immediately()
        except Exception as e:
            print(f"更新通知字體時發生錯誤: {e}")

    def on_fixture_font_changed(self, event=None):
        """治具字體大小即時更新"""
        try:
            new_size = self.vars["Fixture_Font_Size"].get()
            if new_size.isdigit():
                size = int(new_size)
                if 8 <= size <= 24:
                    # 立即更新設定檔
                    settings = load_setup()
                    if 'Fixture_Control' not in settings:
                        settings['Fixture_Control'] = {}
                    settings['Fixture_Control']['Fixture_Font_Size'] = str(size)
                    save_setup(settings)
                    
                    # 通知制具控制頁面更新字體
                    self.apply_fixture_font_changes(size)
        except Exception as e:
            print(f"更新治具字體時發生錯誤: {e}")

    def apply_font_changes_immediately(self):
        """立即套用字體變更到所有相關元件"""
        try:
            # 找到主管理器
            parent = self.parent
            while parent and not hasattr(parent, 'dut_ui'):
                parent = getattr(parent, 'parent', None) or getattr(parent, 'master', None)
            
            if parent and hasattr(parent, 'dut_ui'):
                # 更新 DUT 控制頁面
                dut_ui = parent.dut_ui
                if hasattr(dut_ui, 'update_from_config'):
                    dut_ui.update_from_config()
                
                # 更新字體大小相關設定
                ui_font_size = self.vars["DUT_UI_Font_Size"].get()
                content_font_size = self.vars["DUT_Content_Font_Size"].get()
                notification_font_size = self.vars["DUT_Notification_Font_Size"].get()
                
                if hasattr(dut_ui, 'components'):
                    components = dut_ui.components
                    if hasattr(components, 'font_size_var') and ui_font_size.isdigit():
                        components.font_size_var.set(ui_font_size)
                    if hasattr(components, 'content_font_size_var') and content_font_size.isdigit():
                        components.content_font_size_var.set(content_font_size)
                    if hasattr(components, 'notification_font_size') and notification_font_size.isdigit():
                        components.notification_font_size = int(notification_font_size)
                        
                        # 更新通知相關的 UI 元件
                        if hasattr(components, 'label_countdown'):
                            components.label_countdown.config(
                                font=('Microsoft JhengHei UI', int(notification_font_size), 'bold')
                            )
                    
                    # 觸發字體更新
                    if hasattr(components, 'update_fonts'):
                        components.update_fonts()
                        
        except Exception as e:
            print(f"套用字體變更時發生錯誤: {e}")

    def apply_fixture_font_changes(self, size):
        """套用治具頁面字體變更"""
        try:
            # 找到主管理器
            parent = self.parent
            while parent and not hasattr(parent, 'fixture_ui'):
                parent = getattr(parent, 'parent', None) or getattr(parent, 'master', None)
            
            if parent and hasattr(parent, 'fixture_ui'):
                fixture_ui = parent.fixture_ui
                if hasattr(fixture_ui, 'update_font_size'):
                    fixture_ui.update_font_size(size)
                        
        except Exception as e:
            print(f"套用治具字體變更時發生錯誤: {e}")

    def browse_file(self, var_name):
        """瀏覽檔案"""
        filename = filedialog.askopenfilename(
            title="選取指令檔案",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.vars[var_name].set(filename)
            # 立即保存到setup.json
            try:
                setup = load_setup()
                setup["DUT_Control"]["Command_File_Path"] = filename
                save_setup(setup)
                print(f"[INFO] 指令檔案路徑已更新: {filename}")
            except Exception as e:
                print(f"[ERROR] 保存指令檔案路徑失敗: {e}")
                messagebox.showerror("錯誤", f"保存檔案路徑失敗：{str(e)}")

    def generate_settings_dict(self):
        """根據當前設定生成字典 - 保持現有設定不丟失"""
        # 首先載入現有的完整設定
        current_setup = load_setup()
        
        # 更新基本設定
        current_setup["version"] = self.vars["version"].get()
        current_setup["Window_Title"] = self.vars["Window_Title"].get()
        current_setup["Window_Width"] = self.vars["Window_Width"].get()
        current_setup["Window_Height"] = self.vars["Window_Height"].get()
        
        # 更新標籤頁名稱
        if "tab_names" not in current_setup:
            current_setup["tab_names"] = {}
        current_setup["tab_names"]["tab0"] = self.vars["tab_names_tab0"].get()
        current_setup["tab_names"]["tab1"] = self.vars["tab_names_tab1"].get()
        current_setup["tab_names"]["tab2"] = self.vars["tab_names_tab2"].get()
        current_setup["tab_names"]["tab3"] = self.vars["tab_names_tab3"].get()
        
        # 更新DUT_Control設定
        if "DUT_Control" not in current_setup:
            current_setup["DUT_Control"] = {}
        
        current_setup["DUT_Control"]["Serial_COM_Port"] = self.vars["DUT_Serial_COM_Port"].get()
        current_setup["DUT_Control"]["Command_Timeout_Seconds"] = self.vars["DUT_Command_Timeout_Seconds"].get()
        current_setup["DUT_Control"]["Command_End_String"] = self.vars["DUT_Command_End_String"].get()
        current_setup["DUT_Control"]["Default_IP_Address"] = self.vars["DUT_Default_IP_Address"].get()
        current_setup["DUT_Control"]["UI_Font_Size"] = self.vars["DUT_UI_Font_Size"].get()
        current_setup["DUT_Control"]["Content_Font_Size"] = self.vars["DUT_Content_Font_Size"].get()
        current_setup["DUT_Control"]["Notification_Font_Size"] = self.vars["DUT_Notification_Font_Size"].get()
        current_setup["DUT_Control"]["Pane_Sash_Position"] = self.vars["DUT_Pane_Sash_Position"].get()
        current_setup["DUT_Control"]["Auto_Execute"] = self.vars["DUT_Auto_Execute"].get()
        current_setup["DUT_Control"]["Command_File_Path"] = self.vars["DUT_Command_File_Path"].get()
        
        # 更新Fixture_Control設定
        if "Fixture_Control" not in current_setup:
            current_setup["Fixture_Control"] = {}
            
        current_setup["Fixture_Control"]["Fixture_COM_Port"] = self.vars["Fixture_COM_Port"].get()
        current_setup["Fixture_Control"]["Fixture_Font_Size"] = self.vars["Fixture_Font_Size"].get()
        current_setup["Fixture_Control"]["Test_Category_FUNCTION"] = self.vars["Fixture_Test_Category_FUNCTION"].get()
        current_setup["Fixture_Control"]["Test_Category_MB"] = self.vars["Fixture_Test_Category_MB"].get()
        current_setup["Fixture_Control"]["Test_Category_Original_Commands"] = self.vars["Fixture_Test_Category_Original_Commands"].get()
        
        # 更新串列埠設定
        if "Serial_Settings" not in current_setup["Fixture_Control"]:
            current_setup["Fixture_Control"]["Serial_Settings"] = {}
        
        current_setup["Fixture_Control"]["Serial_Settings"]["Baudrate"] = self.vars["Fixture_Serial_Baudrate"].get()
        current_setup["Fixture_Control"]["Serial_Settings"]["Bytesize"] = self.vars["Fixture_Serial_Bytesize"].get()
        current_setup["Fixture_Control"]["Serial_Settings"]["Stopbits"] = self.vars["Fixture_Serial_Stopbits"].get()
        current_setup["Fixture_Control"]["Serial_Settings"]["Parity"] = self.vars["Fixture_Serial_Parity"].get()
        current_setup["Fixture_Control"]["Serial_Settings"]["Timeout"] = self.vars["Fixture_Serial_Timeout"].get()
        
        # 更新 UI 設定
        if "UI_Settings" not in current_setup:
            current_setup["UI_Settings"] = {}
        current_setup["UI_Settings"]["ToolTip_Enabled"] = self.vars["UI_ToolTip_Enabled"].get()
        
        # 更新全域字體設定
        current_setup["UIFontSize"] = self.vars["DUT_UI_Font_Size"].get()
        current_setup["ContentFontSize"] = self.vars["DUT_Content_Font_Size"].get()
        
        return current_setup

    # 移除了 reload_settings 函數及相關程式碼

    def save_settings(self):
        """儲存所有設定"""
        try:
            settings_dict = self.generate_settings_dict()
            save_setup(settings_dict)
            
            # 調用回調函數通知主程式設定已更新
            if self.on_save_callback:
                self.on_save_callback(settings_dict)
            
            messagebox.showinfo("成功", "設定已儲存！")
            print("[DEBUG] 設定已成功儲存")
            
        except Exception as e:
            error_msg = f"儲存設定失敗：{str(e)}"
            print(f"[ERROR] {error_msg}")
            messagebox.showerror("錯誤", error_msg)

    def on_tooltip_setting_changed(self):
        """當 ToolTip 設定變更時的處理"""
        try:
            enabled = self.vars["UI_ToolTip_Enabled"].get()
            
            # 立即更新設定檔
            settings = load_setup()
            if "UI_Settings" not in settings:
                settings["UI_Settings"] = {}
            settings["UI_Settings"]["ToolTip_Enabled"] = enabled
            save_setup(settings)
            
            # 更新 ToolTip 管理器狀態
            if self.tooltip_manager:
                self.tooltip_manager.enabled = enabled
            
            # 通知主程式更新
            if self.on_save_callback:
                self.on_save_callback(settings)
            
            status = "啟用" if enabled else "停用"
            print(f"[DEBUG] ToolTip 設定已{status}")
            
        except Exception as e:
            print(f"[ERROR] 更新 ToolTip 設定失敗: {e}")

    def setup_tooltips(self):
        """設定工具提示"""
        if not self.tooltip_manager:
            return
            
        # 儲存按鈕 - 移除了重新載入按鈕的 tooltip
        if hasattr(self, 'save_button'):
            self.tooltip_manager.add_tooltip(self.save_button, "儲存所有設定到檔案")
        
        # 字體設定
        if hasattr(self, 'ui_font_spinbox'):
            self.tooltip_manager.add_tooltip(self.ui_font_spinbox, "調整使用者介面文字大小（即時生效）")
        if hasattr(self, 'content_font_spinbox'):
            self.tooltip_manager.add_tooltip(self.content_font_spinbox, "調整內容區域文字大小（即時生效）")
        if hasattr(self, 'notification_font_spinbox'):
            self.tooltip_manager.add_tooltip(self.notification_font_spinbox, "調整通知區域文字大小（即時生效）")
        if hasattr(self, 'fixture_font_spinbox'):
            self.tooltip_manager.add_tooltip(self.fixture_font_spinbox, "調整治具控制頁面文字大小（即時生效）")
        
        # 瀏覽按鈕
        if hasattr(self, 'browse_button'):
            self.tooltip_manager.add_tooltip(self.browse_button, "瀏覽並選擇指令檔案")

    def activate(self):
        """當分頁被選中時調用"""
        # 重新載入最新設定
        self.setup_data = load_setup()
        
        # 更新所有 UI 控件的值
        self.update_ui_from_settings()
        
        print("[DEBUG] 設定分頁已激活並更新")

    def update_ui_from_settings(self):
        """從設定更新 UI 控件的值"""
        try:
            # 更新基本設定
            self.vars["version"].set(self.setup_data.get("version", "V1.5.0.2"))
            self.vars["Window_Title"].set(self.setup_data.get("Window_Title", "VALO360 指令通"))
            self.vars["Window_Width"].set(self.setup_data.get("Window_Width", "1536"))
            self.vars["Window_Height"].set(self.setup_data.get("Window_Height", "793"))
            
            # 更新標籤頁名稱
            tab_names = self.setup_data.get('tab_names', {})
            for i in range(4):
                tab_key = f'tab{i}'
                if f"tab_names_{tab_key}" in self.vars:
                    default_names = ['DUT 控制', '治具控制', '使用說明', '設定']
                    self.vars[f"tab_names_{tab_key}"].set(tab_names.get(tab_key, default_names[i]))
            
            # 更新 DUT 控制設定
            dut_settings = self.setup_data.get('DUT_Control', {})
            self.vars["DUT_Serial_COM_Port"].set(dut_settings.get("Serial_COM_Port", "COM5"))
            self.vars["DUT_Command_Timeout_Seconds"].set(dut_settings.get("Command_Timeout_Seconds", "30"))
            self.vars["DUT_Command_End_String"].set(dut_settings.get("Command_End_String", "root"))
            self.vars["DUT_Default_IP_Address"].set(dut_settings.get("Default_IP_Address", "192.168.11.143"))
            self.vars["DUT_UI_Font_Size"].set(dut_settings.get("UI_Font_Size", "13"))
            self.vars["DUT_Content_Font_Size"].set(dut_settings.get("Content_Font_Size", "11"))
            self.vars["DUT_Notification_Font_Size"].set(dut_settings.get("Notification_Font_Size", "10"))
            self.vars["DUT_Pane_Sash_Position"].set(dut_settings.get("Pane_Sash_Position", "633"))
            self.vars["DUT_Auto_Execute"].set(dut_settings.get("Auto_Execute", False))
            self.vars["DUT_Command_File_Path"].set(dut_settings.get("Command_File_Path", ""))
            
            # 更新治具控制設定
            fixture_settings = self.setup_data.get('Fixture_Control', {})
            self.vars["Fixture_COM_Port"].set(fixture_settings.get("Fixture_COM_Port", "COM5"))
            self.vars["Fixture_Font_Size"].set(fixture_settings.get("Fixture_Font_Size", "11"))
            self.vars["Fixture_Test_Category_FUNCTION"].set(fixture_settings.get("Test_Category_FUNCTION", True))
            self.vars["Fixture_Test_Category_MB"].set(fixture_settings.get("Test_Category_MB", False))
            self.vars["Fixture_Test_Category_Original_Commands"].set(fixture_settings.get("Test_Category_Original_Commands", False))
            
            # 更新串列埠設定
            serial_settings = fixture_settings.get("Serial_Settings", {})
            self.vars["Fixture_Serial_Baudrate"].set(serial_settings.get("Baudrate", "9600"))
            self.vars["Fixture_Serial_Bytesize"].set(serial_settings.get("Bytesize", "8"))
            self.vars["Fixture_Serial_Stopbits"].set(serial_settings.get("Stopbits", "1"))
            self.vars["Fixture_Serial_Parity"].set(serial_settings.get("Parity", "None"))
            self.vars["Fixture_Serial_Timeout"].set(serial_settings.get("Timeout", "1.0"))
            
            # 更新 UI 設定
            ui_settings = self.setup_data.get('UI_Settings', {})
            self.vars["UI_ToolTip_Enabled"].set(ui_settings.get("ToolTip_Enabled", True))
            
        except Exception as e:
            print(f"[ERROR] 更新 UI 設定時發生錯誤: {e}") 