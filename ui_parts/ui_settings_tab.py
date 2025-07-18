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
from ui_parts.tooltip import ToolTipManager, AIToolTipGenerator

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
        # 創建主容器，使用 PanedWindow 來提供可調整的左右分隔
        main_container = ttk.PanedWindow(self, orient='horizontal')
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 左側容器
        left_frame = ttk.Frame(main_container)
        main_container.add(left_frame, weight=1)
        
        # 右側容器
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=1)
        
        # 設定分隔位置為中間
        main_container.sashpos(0, 400)
        
        # 移除儲存按鈕區域 - 因為已經移動到DUT控制區塊了
        
        # === 左側內容 ===
        left_container = ttk.Frame(left_frame)
        left_container.pack(fill='both', expand=True, padx=(0, 5))
        
        current_row = 0
        
        # 應用程式基本設定
        basic_frame = ttk.LabelFrame(left_container, text="應用程式基本設定", padding=(10, 4))
        basic_frame.pack(fill='x', pady=(0, 8))
        basic_frame.columnconfigure(1, weight=1)
        
        # 版本號 - width=20
        ttk.Label(basic_frame, text="版本:").grid(row=0, column=0, sticky="w", pady=4)
        self.vars["version"] = tk.StringVar(value=self.setup_data.get("version", "V1.5.0.2"))
        self.version_entry = ttk.Entry(basic_frame, textvariable=self.vars["version"], width=20)
        self.version_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)
        
        # 視窗標題 - width=40
        ttk.Label(basic_frame, text="視窗標題:").grid(row=1, column=0, sticky="w", pady=4)
        self.vars["Window_Title"] = tk.StringVar(value=self.setup_data.get("Window_Title", "VALO360 指令通"))
        self.window_title_entry = ttk.Entry(basic_frame, textvariable=self.vars["Window_Title"], width=40)
        self.window_title_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=4)
        
        # 視窗大小 - 視窗寬度 width=20
        size_frame = ttk.Frame(basic_frame)
        size_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=4)
        size_frame.columnconfigure(1, weight=1)
        size_frame.columnconfigure(3, weight=1)
        
        ttk.Label(size_frame, text="寬度:").grid(row=0, column=0, sticky="w")
        self.vars["Window_Width"] = tk.StringVar(value=self.setup_data.get("Window_Width", "1536"))
        self.window_width_entry = ttk.Entry(size_frame, textvariable=self.vars["Window_Width"], width=20)
        self.window_width_entry.grid(row=0, column=1, sticky="w", padx=(5, 10))
        
        ttk.Label(size_frame, text="高度:").grid(row=0, column=2, sticky="w")
        self.vars["Window_Height"] = tk.StringVar(value=self.setup_data.get("Window_Height", "793"))
        self.window_height_entry = ttk.Entry(size_frame, textvariable=self.vars["Window_Height"], width=20)
        self.window_height_entry.grid(row=0, column=3, sticky="w", padx=(5, 0))
        
        # DUT 控制設定
        dut_frame = ttk.LabelFrame(left_container, text="DUT 控制設定", padding=(10, 4))
        dut_frame.pack(fill='both', expand=True, pady=(0, 8))
        dut_frame.columnconfigure(1, weight=1)
        
        dut_settings = self.setup_data.get('DUT_Control', {})
        dut_row = 0
        
        # 串口設定 - width=20
        ttk.Label(dut_frame, text="串口:").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Serial_COM_Port"] = tk.StringVar(value=dut_settings.get("Serial_COM_Port", "COM5"))
        self.dut_com_entry = ttk.Entry(dut_frame, textvariable=self.vars["DUT_Serial_COM_Port"], width=20)
        self.dut_com_entry.grid(row=dut_row, column=1, sticky="w", padx=(10, 0), pady=4)
        dut_row += 1
        
        # 指令超時(秒) - width=20
        ttk.Label(dut_frame, text="指令超時(秒):").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Command_Timeout_Seconds"] = tk.StringVar(value=dut_settings.get("Command_Timeout_Seconds", "30"))
        self.dut_timeout_entry = ttk.Entry(dut_frame, textvariable=self.vars["DUT_Command_Timeout_Seconds"], width=20)
        self.dut_timeout_entry.grid(row=dut_row, column=1, sticky="w", padx=(10, 0), pady=4)
        dut_row += 1
        
        # 指令結束字串 - width=20
        ttk.Label(dut_frame, text="指令結束字串:").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Command_End_String"] = tk.StringVar(value=dut_settings.get("Command_End_String", "root"))
        self.dut_end_string_entry = ttk.Entry(dut_frame, textvariable=self.vars["DUT_Command_End_String"], width=20)
        self.dut_end_string_entry.grid(row=dut_row, column=1, sticky="w", padx=(10, 0), pady=4)
        dut_row += 1
        
        # 預設IP地址 - width=20
        ttk.Label(dut_frame, text="預設IP地址:").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Default_IP_Address"] = tk.StringVar(value=dut_settings.get("Default_IP_Address", "192.168.11.143"))
        self.dut_ip_entry = ttk.Entry(dut_frame, textvariable=self.vars["DUT_Default_IP_Address"], width=20)
        self.dut_ip_entry.grid(row=dut_row, column=1, sticky="w", padx=(10, 0), pady=4)
        dut_row += 1

        self.vars["DUT_Pane_Sash_Position"] = tk.StringVar(value=dut_settings.get("Pane_Sash_Position", "633"))
        self.vars["DUT_Auto_Execute"] = tk.BooleanVar(value=dut_settings.get("Auto_Execute", False))
        self.vars["UI_ToolTip_Enabled"] = tk.BooleanVar(value=self.setup_data.get('UI_Settings', {}).get("ToolTip_Enabled", True))
        
        # 創建ToolTip啟用勾選框
        self.tooltip_enabled_checkbox = ttk.Checkbutton(
            dut_frame, 
            text="啟用 ToolTip 提示", 
            variable=self.vars["UI_ToolTip_Enabled"],
            command=self.on_tooltip_setting_changed
        )
        self.tooltip_enabled_checkbox.grid(row=dut_row, column=0, columnspan=2, sticky="w", pady=4)
        dut_row += 1
        
        # 創建自動執行勾選框
        self.auto_execute_checkbox = ttk.Checkbutton(
            dut_frame,
            text="啟動時自動執行指令",
            variable=self.vars["DUT_Auto_Execute"]
        )
        self.auto_execute_checkbox.grid(row=dut_row, column=0, columnspan=2, sticky="w", pady=4)
        dut_row += 1

        # 字體設定 - 水平排版，並加入即時更新功能
        font_frame = ttk.Frame(dut_frame)
        font_frame.grid(row=dut_row, column=0, columnspan=2, sticky="ew", pady=4)
        font_frame.columnconfigure(1, weight=1)
        font_frame.columnconfigure(3, weight=1)
        
        # 介面字體 - width=20
        ttk.Label(font_frame, text="介面字體:").grid(row=0, column=0, sticky="w")
        self.vars["DUT_UI_Font_Size"] = tk.StringVar(value=dut_settings.get("UI_Font_Size", "13"))
        self.ui_font_spinbox = ttk.Spinbox(font_frame, textvariable=self.vars["DUT_UI_Font_Size"], 
                                          from_=8, to=24, width=8, command=self.on_ui_font_changed)
        self.ui_font_spinbox.grid(row=0, column=1, sticky="ew", padx=(5, 10))
        self.ui_font_spinbox.bind('<Return>', self.on_ui_font_changed)
        self.ui_font_spinbox.bind('<FocusOut>', self.on_ui_font_changed)
        
        ttk.Label(font_frame, text="內容字體:").grid(row=0, column=2, sticky="w")
        self.vars["DUT_Content_Font_Size"] = tk.StringVar(value=dut_settings.get("Content_Font_Size", "11"))
        self.content_font_spinbox = ttk.Spinbox(font_frame, textvariable=self.vars["DUT_Content_Font_Size"], 
                                               from_=8, to=24, width=8, command=self.on_content_font_changed)
        self.content_font_spinbox.grid(row=0, column=3, sticky="ew", padx=(5, 0))
        self.content_font_spinbox.bind('<Return>', self.on_content_font_changed)
        self.content_font_spinbox.bind('<FocusOut>', self.on_content_font_changed)
        dut_row += 1
        # 儲存設定按鈕 - 靠右對齊內容字體下方
        button_container = ttk.Frame(font_frame)
        button_container.grid(row=1, column=3, sticky="e", pady=(10, 4))
        self.save_button = tk.Button(
            button_container, 
            text="儲存\n設定", 
            font=('Microsoft JhengHei UI', 14, 'bold'),
            bg='#4CAF50', 
            fg='white', 
            relief='raised', 
            borderwidth=3,
            cursor="hand2",
            command=self.save_settings,
            width=10,
            height=3
        )
        self.save_button.pack(side=tk.RIGHT)
        self.save_button.bind("<Enter>", lambda e: self.save_button.config(bg='#45a049'))
        self.save_button.bind("<Leave>", lambda e: self.save_button.config(bg='#4CAF50'))
        dut_row += 1
        
        # 指令檔案路徑 - 改為兩行顯示
        ttk.Label(dut_frame, text="指令檔案路徑:").grid(row=dut_row, column=0, sticky="nw", pady=4)
        path_container = ttk.Frame(dut_frame)
        path_container.grid(row=dut_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        path_container.columnconfigure(0, weight=1)
        
        # 第一行：路徑輸入框
        self.vars["DUT_Command_File_Path"] = tk.StringVar(value=dut_settings.get("Command_File_Path", ""))
        self.dut_command_file_entry = ttk.Entry(path_container, textvariable=self.vars["DUT_Command_File_Path"])
        self.dut_command_file_entry.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # 第二行：瀏覽按鈕
        self.browse_button = ttk.Button(path_container, text="瀏覽檔案", command=lambda: self.browse_file("DUT_Command_File_Path"))
        self.browse_button.grid(row=1, column=0, sticky="w")
        dut_row += 1
        
        # === 右側內容 ===
        right_container = ttk.Frame(right_frame)
        right_container.pack(fill='both', expand=True, padx=(5, 0))
        
        # 標籤頁名稱設定
        tab_frame = ttk.LabelFrame(right_container, text="標籤頁名稱設定", padding=(10, 4))
        tab_frame.pack(fill='x', pady=(0, 8))
        tab_frame.columnconfigure(1, weight=1)
        
        # 獲取當前的標籤頁名稱
        tab_names = self.setup_data.get('tab_names', {})
        default_tab_names = ['DUT 控制', '治具控制', '使用說明', '設定']
        
        # 創建標籤頁名稱輸入框 - 標籤頁1~4 width=20
        for i in range(4):
            tab_key = f'tab{i}'
            tab_name = tab_names.get(tab_key, default_tab_names[i])
            ttk.Label(tab_frame, text=f"標籤頁 {i+1}:").grid(row=i, column=0, sticky="w", pady=4)
            self.vars[f"tab_names_{tab_key}"] = tk.StringVar(value=tab_name)
            entry = ttk.Entry(tab_frame, textvariable=self.vars[f"tab_names_{tab_key}"], width=20)
            entry.grid(row=i, column=1, sticky="ew", padx=(10, 0), pady=4)
            setattr(self, f"tab_names_{tab_key}_entry", entry)
        
        # 注意：治具控制設定已移動至「TAB 測試治具」的指令控制區塊中

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
        current_setup["DUT_Control"]["Pane_Sash_Position"] = self.vars["DUT_Pane_Sash_Position"].get()
        current_setup["DUT_Control"]["Auto_Execute"] = self.vars["DUT_Auto_Execute"].get()
        current_setup["DUT_Control"]["Command_File_Path"] = self.vars["DUT_Command_File_Path"].get()
        
        # 注意：Fixture_Control 設定已移動至治具控制TAB中，這裡不再處理
        # 只保留基本結構，確保不破壞現有設定
        if "Fixture_Control" not in current_setup:
            current_setup["Fixture_Control"] = {}
        
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
        """儲存設定到 setup.json"""
        import traceback
        try:
            # 生成設定字典
            settings_dict = self.generate_settings_dict()
            # 保存設定
            save_setup(settings_dict)
            # 調用回調函數通知其他組件設定已更新
            if self.on_save_callback:
                self.on_save_callback()
            # 顯示成功訊息
            messagebox.showinfo("成功", "設定已儲存")
        except Exception as e:
            print(f"[錯誤] 儲存設定失敗: {e}")
            traceback.print_exc()
            messagebox.showerror("錯誤", f"儲存設定時發生錯誤: {e}")

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
        """設置所有設定頁面元件的tooltip"""
        try:
            # 嘗試獲取全域通知管理器
            global_notification_manager = None
            
            # 從 parent 獲取
            if hasattr(self.parent, 'notification_manager'):
                global_notification_manager = self.parent.notification_manager
                print("[DEBUG] 設定頁面: 從 parent 獲取全域通知管理器")
            # 從 root 獲取
            elif hasattr(self.parent, 'master') and hasattr(self.parent.master, 'notification_manager'):
                global_notification_manager = self.parent.master.notification_manager
                print("[DEBUG] 設定頁面: 從 root 獲取全域通知管理器")
            # 從 TabManager 獲取
            elif hasattr(self.parent, 'master') and hasattr(self.parent.master, 'tab_manager') and \
                 hasattr(self.parent.master.tab_manager, 'notification_manager'):
                global_notification_manager = self.parent.master.tab_manager.notification_manager
                print("[DEBUG] 設定頁面: 從 tab_manager 獲取全域通知管理器")
            
            # 重新初始化 ToolTip 管理器，傳入全域通知管理器
            self.tooltip_manager = ToolTipManager(global_notification_manager)
            
            # 從設定中讀取 ToolTip 啟用狀態，預設為啟用
            tooltip_enabled = self.setup_data.get("UI_Settings", {}).get("ToolTip_Enabled", True)
            self.tooltip_manager.set_all_enabled(tooltip_enabled)
            
            # 為所有設定頁面元件添加tooltip
            self._add_tooltip_to_settings_widgets()
            
            print("[DEBUG] 設定頁面: 所有tooltip已初始化完成")
            
        except Exception as e:
            print(f"[ERROR] 設定頁面: 初始化tooltip時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def _add_tooltip_to_settings_widgets(self):
        """為設定頁面所有元件添加AI生成的tooltip"""
        
        # 定義需要添加tooltip的元件列表
        widget_list = [
            # 儲存按鈕
            ('save_button', 'settings_save_button'),
            
            # 基本設定區域
            ('version_entry', 'settings_version_entry'),
            ('window_title_entry', 'settings_window_title_entry'),
            ('window_width_entry', 'settings_window_width_entry'),
            ('window_height_entry', 'settings_window_height_entry'),
            
            # DUT控制設定區域
            ('dut_com_entry', 'settings_dut_com_entry'),
            ('dut_timeout_entry', 'settings_dut_timeout_entry'),
            ('dut_end_string_entry', 'settings_dut_end_string_entry'),
            ('dut_ip_entry', 'settings_dut_ip_entry'),
            ('dut_command_file_entry', 'settings_dut_command_file_entry'),
            
            # 字體設定
            ('ui_font_spinbox', 'settings_ui_font_spinbox'),
            ('content_font_spinbox', 'settings_content_font_spinbox'),
            
            # 瀏覽按鈕
            ('browse_button', 'settings_browse_button'),
            
            # 勾選框
            ('tooltip_enabled_checkbox', 'settings_tooltip_enabled_checkbox'),
            ('auto_execute_checkbox', 'settings_auto_execute_checkbox'),
        ]
        
        # 為每個元件添加tooltip
        for attr_name, widget_name in widget_list:
            if hasattr(self, attr_name):
                widget = getattr(self, attr_name)
                self._add_ai_tooltip_to_widget(widget, widget_name)
        
        # 為標籤頁名稱設定動態添加tooltip
        for i in range(4):
            tab_key = f'tab{i}'
            entry_name = f"tab_names_{tab_key}_entry"
            if hasattr(self, entry_name):
                entry = getattr(self, entry_name)
                tab_names = ['DUT 控制', '治具控制', '使用說明', '設定']
                self._add_ai_tooltip_to_widget(entry, f"settings_tab_names_{tab_key}")
    
    def _add_ai_tooltip_to_widget(self, widget, widget_name):
        """為單個元件添加AI生成的tooltip"""
        try:
            # 提取元件資訊
            widget_info = AIToolTipGenerator.extract_widget_info(widget)
            
            # 生成tooltip文字
            tooltip_text = AIToolTipGenerator.generate_tooltip_for_widget(
                widget=widget,
                widget_name=widget_name,
                widget_type=widget_info['type'],
                context=widget_info['context']
            )
            
            # 添加tooltip到元件
            self.tooltip_manager.add_tooltip(widget, tooltip_text)
            
            print(f"[DEBUG] 已為設定頁面 {widget_name} 添加tooltip: {tooltip_text[:50]}...")
            
        except Exception as e:
            print(f"[ERROR] 為設定頁面 {widget_name} 添加tooltip時發生錯誤: {e}")

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
            self.vars["DUT_Pane_Sash_Position"].set(dut_settings.get("Pane_Sash_Position", "633"))
            self.vars["DUT_Auto_Execute"].set(dut_settings.get("Auto_Execute", False))
            self.vars["DUT_Command_File_Path"].set(dut_settings.get("Command_File_Path", ""))
            
            # 注意：治具控制設定已移動至治具控制TAB中，這裡不再處理
            
            # 更新 UI 設定
            ui_settings = self.setup_data.get('UI_Settings', {})
            self.vars["UI_ToolTip_Enabled"].set(ui_settings.get("ToolTip_Enabled", True))
            
        except Exception as e:
            print(f"[ERROR] 更新 UI 設定時發生錯誤: {e}") 