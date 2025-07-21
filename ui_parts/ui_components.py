# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import sys
import re
import threading
import time
from datetime import datetime
from ui_parts.ui_components_base import UIComponentsBase
from ui_parts.ui_components_input import UIComponentsInput
from ui_parts.ui_components_output import UIComponentsOutput
from ui_parts.ui_components_settings import UIComponentsSettings
from ui_parts.tooltip import ToolTipManager, ToolTip, AIToolTipGenerator
from config_utils import get_notification_text, get_app_version
from config_core import load_setup, save_setup, GUIDE_FILE, COMMAND_FILE, list_com_ports


# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)


class UIComponents(UIComponentsBase, UIComponentsInput, UIComponentsOutput, UIComponentsSettings):
    def __init__(self, parent, handlers, root):
        # Call the __init__ of the base class (UIComponentsBase) which sets up the UI structure
        self.parent = parent  # 先設定 parent 屬性
        super().__init__(parent, root)
        self.root = root
        self.handlers = handlers
        
        # 獲取全域通知管理器的引用
        self.global_notification_manager = None
        # 會在init_dut_tab中被設定
        
        # 初始化統一設定管理器
        try:
            from ui_parts.shared_config import get_shared_config
            self.shared_config = get_shared_config()
            print("[DEBUG] UIComponents: 統一設定管理器初始化成功")
        except ImportError as e:
            self.shared_config = None
            print(f"[WARNING] UIComponents: 無法載入統一設定管理器: {e}")
        
        # 初始化 ToolTip 管理器
        self.tooltip_manager = ToolTipManager()
        # 從設定中讀取 ToolTip 啟用狀態，預設為啟用
        tooltip_enabled = self.parent.setup.get("UI_Settings", {}).get("ToolTip_Enabled", True)
        self.tooltip_manager.set_all_enabled(tooltip_enabled)
        
        # 定義標準 UI 風格參數
        self.ui_font = "Segoe UI"  # Windows 預設字體
        self.ui_font_size = int(self.parent.setup.get('UI_Font_Size', '10'))
        self.ui_padding = 5        # 元件間距
        self.ui_button_width = 100 # 標準按鈕寬度
        self.ui_button_height = 30 # 標準按鈕高度
        self.ui_bg_color = "#f0f0f0" # 淺灰白底色
        
        # 初始化各個元件
        self.init_com_components()
        self.init_cmd_components()
        self.init_ping_components()
        self.init_settings_components()
        self.init_output_components()
        self.init_progress_components()
        
        # 初始化所有tooltip（在所有元件創建完成後）
        self.init_tooltips()
        
        # 強化 left_panel 內所有 Entry/Combobox 的 <Return> 綁定
        for widget in [self.combobox_cmd, self.entry_timeout, self.combobox_end, self.entry_ip, self.combobox_com]:
            widget.bind('<Return>', lambda e: self.parent.handlers.on_execute())
            
        # 恢復 PanedWindow 分割位置（延遲執行，確保視窗已完全載入）
        self.parent.root.after(200, self.restore_pane_position)
        
        # 使用全域通知管理器顯示歡迎訊息
        welcome_message = "歡迎使用 VALO360 指令通！\n選擇COM口和指令後點擊「執行指令」按鈕。"
        self.parent.root.after(3000, lambda: self.show_notification(welcome_message, "success", 5000))
        
        # 顯示系統狀態
        self.parent.root.after(8000, self.show_system_status)

    def init_com_components(self):
        """初始化 COM 口相關元件"""
        # 創建分組框架
        com_frame = ttk.LabelFrame(self.left_panel, text="COM 口設定", style="TLabelframe")
        com_frame.grid(row=0, column=0, sticky='ew', padx=self.ui_padding, pady=self.ui_padding)
        
        # 配置網格
        com_frame.columnconfigure(0, weight=0)  # 標籤固定寬度
        com_frame.columnconfigure(1, weight=1)  # 下拉選單可擴展
        com_frame.columnconfigure(2, weight=0)  # 刷新按鈕固定寬度
        com_frame.columnconfigure(3, weight=0)  # 狀態指示器固定寬度
        
        # COM口標籤
        self.label_com = ttk.Label(com_frame, text='COM口:', style="TLabel")
        self.label_com.grid(row=0, column=0, sticky='w', padx=self.ui_padding, pady=self.ui_padding)
        
        # COM口下拉選單
        com_values = list_com_ports()
        self.combobox_com = ttk.Combobox(com_frame, values=com_values, state='readonly', width=15)
        self.combobox_com.grid(row=0, column=1, sticky='ew', padx=self.ui_padding, pady=self.ui_padding)
        self.combobox_com.bind("<<ComboboxSelected>>", self.on_com_port_changed)
        
        # 刷新按鈕
        refresh_command = None
        if hasattr(self.parent, 'handlers') and hasattr(self.parent.handlers, 'refresh_com_ports'):
            refresh_command = self.parent.handlers.refresh_com_ports
        else:
            refresh_command = lambda: None
            print("[WARNING] handlers 不存在或沒有 refresh_com_ports 方法")
        
        self.btn_refresh = ttk.Button(com_frame, text='刷新', command=refresh_command, width=8)
        self.btn_refresh.grid(row=0, column=2, padx=self.ui_padding, pady=self.ui_padding)
        
        # 狀態指示燈
        self.status_canvas = tk.Canvas(com_frame, width=30, height=30, bg=self.ui_bg_color, highlightthickness=0)
        self.status_canvas.grid(row=0, column=3, padx=self.ui_padding, pady=self.ui_padding)
        self.status_light = self.status_canvas.create_oval(5, 5, 25, 25, fill='black')
        self.led_blinking = False

    def init_cmd_components(self):
        """初始化指令相關元件"""
        # 創建分組框架
        cmd_frame = ttk.LabelFrame(self.left_panel, text="指令設定", style="TLabelframe")
        cmd_frame.grid(row=1, column=0, sticky='ew', padx=self.ui_padding, pady=self.ui_padding)
        cmd_frame.columnconfigure(0, weight=1)  # 讓內容可以水平擴展
        
        # 分類選擇區域
        self.section_frame = ttk.Frame(cmd_frame, style="TFrame")
        self.section_frame.grid(row=0, column=0, sticky='ew', pady=self.ui_padding)
        
        # 配置網格
        for i in range(4):  # 假設最多4列
            self.section_frame.columnconfigure(i, weight=1)
        
        self.section_var = tk.StringVar()
        
        # 從 command.txt 動態讀取分類
        self.sections = []
        try:
            command_file_path = self.parent.setup.get("DUT_Control", {}).get("Command_File_Path", "")
            command_file = command_file_path if command_file_path and os.path.exists(command_file_path) else COMMAND_FILE
            with open(command_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('==') and line.endswith('=='):
                        section_name = line.strip('=')
                        if section_name and section_name not in self.sections:
                            self.sections.append(section_name)
        except Exception as e:
            print(f"[ERROR] 讀取分類時發生錯誤: {e}")
            
        if not self.sections:
            self.sections = ['全部指令']
        
        if self.sections:
            self.section_var.set(self.sections[0])
        
        max_buttons_per_row = 4
        self.section_radiobuttons = []
        
        # 創建分類選擇按鈕
        for i, sec in enumerate(self.sections):
            row, col = i // max_buttons_per_row, i % max_buttons_per_row
            rb = ttk.Radiobutton(
                self.section_frame, 
                text=sec, 
                variable=self.section_var, 
                value=sec, 
                command=self.update_cmd_list,
                style="TRadiobutton"
            )
            rb.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
            self.section_radiobuttons.append(rb)
        
        # 分類說明
        self.section_description = ttk.Label(
            self.section_frame, 
            text=self.get_section_description(self.section_var.get()), 
            style="TLabel", 
            wraplength=300
        )
        last_row = (len(self.sections) - 1) // max_buttons_per_row + 1
        self.section_description.grid(row=last_row, column=0, columnspan=max_buttons_per_row, pady=2, sticky='w')
        
        # 指令選擇區域
        cmd_control_frame = ttk.Frame(cmd_frame, style="TFrame")
        cmd_control_frame.grid(row=1, column=0, sticky='ew', pady=self.ui_padding)
        
        # 配置網格
        cmd_control_frame.columnconfigure(0, weight=0)  # 標籤固定寬度
        cmd_control_frame.columnconfigure(1, weight=1)  # 下拉選單可擴展
        cmd_control_frame.columnconfigure(2, weight=0)  # 執行按鈕固定寬度
        
        # 指令標籤
        self.label_cmd = ttk.Label(cmd_control_frame, text='指令:', style="TLabel")
        self.label_cmd.grid(row=0, column=0, sticky='w', padx=self.ui_padding, pady=self.ui_padding)
        
        # 指令下拉選單
        self.combobox_cmd = ttk.Combobox(cmd_control_frame, state='readonly', width=25)
        self.combobox_cmd.grid(row=0, column=1, sticky='ew', padx=self.ui_padding, pady=self.ui_padding)
        self.combobox_cmd.bind("<<ComboboxSelected>>", lambda e: self.on_cmd_selected())
        self.combobox_cmd.bind("<<ComboboxOpened>>", self.limit_dropdown_height)
        
        # 執行按鈕
        self.btn_execute = ttk.Button(
            cmd_control_frame, 
            text='執行指令', 
            command=lambda: self.parent.handlers.on_execute(),
            style="Accent.TButton",
            width=10
        )
        self.btn_execute.grid(row=0, column=2, padx=self.ui_padding, pady=self.ui_padding)
        
        # 超時設定區域
        timeout_frame = ttk.Frame(cmd_frame, style="TFrame")
        timeout_frame.grid(row=2, column=0, sticky='ew', pady=self.ui_padding)
        
        # 配置網格
        timeout_frame.columnconfigure(0, weight=0)  # 標籤固定寬度
        timeout_frame.columnconfigure(1, weight=1)  # 輸入框可擴展
        timeout_frame.columnconfigure(2, weight=0)  # 標籤固定寬度
        timeout_frame.columnconfigure(3, weight=1)  # 下拉選單可擴展
        
        # 超時標籤
        self.label_timeout = ttk.Label(timeout_frame, text='超時:', style="TLabel")
        self.label_timeout.grid(row=0, column=0, sticky='w', padx=self.ui_padding, pady=self.ui_padding)
        
        # 超時輸入框
        self.entry_timeout = ttk.Entry(timeout_frame, width=8)
        self.entry_timeout.grid(row=0, column=1, sticky='ew', padx=self.ui_padding, pady=self.ui_padding)
        self.entry_timeout.insert(0, "1000")  # 預設值
        
        # 結束符標籤
        self.label_end = ttk.Label(timeout_frame, text='結束符:', style="TLabel")
        self.label_end.grid(row=0, column=2, sticky='w', padx=self.ui_padding, pady=self.ui_padding)
        
        # 結束符下拉選單
        end_values = ["\\r", "\\n", "\\r\\n", "OK", "ERROR", "自定義..."]
        self.combobox_end = ttk.Combobox(timeout_frame, values=end_values, width=10)
        self.combobox_end.grid(row=0, column=3, sticky='ew', padx=self.ui_padding, pady=self.ui_padding)
        self.combobox_end.current(2)  # 預設選擇 \r\n
        
        # 更新指令列表
        self.update_cmd_list()

    def init_ping_components(self):
        """初始化 Ping 相關元件"""
        # 創建分組框架
        ping_frame = ttk.LabelFrame(self.left_panel, text="Ping 工具", style="TLabelframe")
        ping_frame.grid(row=2, column=0, sticky='ew', padx=self.ui_padding, pady=self.ui_padding)
        
        # 配置網格
        ping_frame.columnconfigure(0, weight=0)  # 標籤固定寬度
        ping_frame.columnconfigure(1, weight=1)  # 輸入框可擴展
        ping_frame.columnconfigure(2, weight=0)  # 按鈕固定寬度
        ping_frame.columnconfigure(3, weight=0)  # 按鈕固定寬度
        
        # IP 標籤
        self.label_ip = ttk.Label(ping_frame, text='IP:', style="TLabel")
        self.label_ip.grid(row=0, column=0, sticky='w', padx=self.ui_padding, pady=self.ui_padding)
        
        # IP 輸入框
        self.entry_ip = ttk.Combobox(ping_frame, width=15)
        self.entry_ip.grid(row=0, column=1, sticky='ew', padx=self.ui_padding, pady=self.ui_padding)
        
        # 載入 IP 歷史記錄
        self.load_ip_history()
        
        # Ping 按鈕
        self.btn_ping = ttk.Button(
            ping_frame, 
            text='Ping', 
            command=lambda: self.parent.handlers.on_ping(),
            style="TButton",
            width=8
        )
        self.btn_ping.grid(row=0, column=2, padx=self.ui_padding, pady=self.ui_padding)
        
        # 儲存按鈕
        self.btn_save_ip = ttk.Button(
            ping_frame, 
            text='儲存', 
            command=self.save_current_ip,
            style="TButton",
            width=8
        )
        self.btn_save_ip.grid(row=0, column=3, padx=self.ui_padding, pady=self.ui_padding)
        
        # IP 歷史記錄區域
        ip_history_frame = ttk.Frame(ping_frame, style="TFrame")
        ip_history_frame.grid(row=1, column=0, columnspan=4, sticky='ew', pady=self.ui_padding)
        
        # 配置網格
        ip_history_frame.columnconfigure(0, weight=1)  # 歷史記錄列表可擴展
        ip_history_frame.columnconfigure(1, weight=0)  # 按鈕固定寬度
        
        # 歷史記錄列表
        self.listbox_ip_history = tk.Listbox(ip_history_frame, height=4, exportselection=0)
        self.listbox_ip_history.grid(row=0, column=0, sticky='ew', padx=self.ui_padding)
        self.listbox_ip_history.bind('<<ListboxSelect>>', self.on_ip_history_selected)
        self.listbox_ip_history.bind('<Double-1>', lambda e: self.on_ping_with_save())
        
        # 歷史記錄滾動條
        scrollbar = ttk.Scrollbar(ip_history_frame, orient="vertical", command=self.listbox_ip_history.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.listbox_ip_history.configure(yscrollcommand=scrollbar.set)
        
        # 刪除按鈕
        self.btn_delete_ip = ttk.Button(
            ping_frame, 
            text='刪除', 
            command=self.delete_current_ip,
            style="TButton",
            width=8
        )
        self.btn_delete_ip.grid(row=2, column=2, padx=self.ui_padding, pady=self.ui_padding)
        
        # 清空按鈕
        self.btn_clear_ip = ttk.Button(
            ping_frame, 
            text='清空', 
            command=self.clear_ip_history,
            style="TButton",
            width=8
        )
        self.btn_clear_ip.grid(row=2, column=3, padx=self.ui_padding, pady=self.ui_padding)

    def init_settings_components(self):
        """初始化設定相關元件"""
        # 創建分組框架
        settings_frame = ttk.LabelFrame(self.left_panel, text="其他設定", style="TLabelframe")
        settings_frame.grid(row=3, column=0, sticky='ew', padx=self.ui_padding, pady=self.ui_padding)
        
        # 配置網格
        settings_frame.columnconfigure(0, weight=1)  # 讓內容可以水平擴展
        
        # 自動執行區域
        auto_exec_frame = ttk.Frame(settings_frame, style="TFrame")
        auto_exec_frame.grid(row=0, column=0, sticky='ew', pady=self.ui_padding)
        
        # 自動執行核取方塊
        self.auto_exec_var = tk.BooleanVar(value=False)
        self.checkbtn_auto_exec = ttk.Checkbutton(
            auto_exec_frame, 
            text='自動執行', 
            variable=self.auto_exec_var,
            command=self.on_auto_exec_changed,
            style="TCheckbutton"
        )
        self.checkbtn_auto_exec.pack(side=tk.LEFT, padx=self.ui_padding)
        
        # 顯示 Tooltip 核取方塊
        self.tooltip_enabled_var = tk.BooleanVar(value=True)
        self.checkbtn_tooltip = ttk.Checkbutton(
            auto_exec_frame, 
            text='顯示提示', 
            variable=self.tooltip_enabled_var,
            command=self.on_tooltip_changed,
            style="TCheckbutton"
        )
        self.checkbtn_tooltip.pack(side=tk.LEFT, padx=20)
        
        # 功能按鈕區域
        buttons_frame = ttk.Frame(settings_frame, style="TFrame")
        buttons_frame.grid(row=1, column=0, sticky='ew', pady=self.ui_padding)
        
        # 配置網格
        for i in range(3):
            buttons_frame.columnconfigure(i, weight=1)
        
        # 說明按鈕
        self.btn_guide = ttk.Button(
            buttons_frame, 
            text='使用說明', 
            command=lambda: self.parent.handlers.on_show_guide(),
            style="TButton",
            width=10
        )
        self.btn_guide.grid(row=0, column=0, padx=self.ui_padding, pady=self.ui_padding)
        
        # 清空輸出按鈕
        self.btn_clear_output = ttk.Button(
            buttons_frame, 
            text='清空輸出', 
            command=lambda: self.parent.handlers.on_clear_output(),
            style="TButton",
            width=10
        )
        self.btn_clear_output.grid(row=0, column=1, padx=self.ui_padding, pady=self.ui_padding)
        
        # 設定按鈕
        self.btn_settings = ttk.Button(
            buttons_frame, 
            text='進階設定', 
            command=lambda: self.parent.handlers.on_show_settings(),
            style="TButton",
            width=10
        )
        self.btn_settings.grid(row=0, column=2, padx=self.ui_padding, pady=self.ui_padding)

    def init_output_components(self):
        """初始化輸出相關元件"""
        # 右側面板已在 UIComponentsBase 中初始化
        pass

    def init_progress_components(self):
        """初始化進度條元件"""
        # 創建進度條框架
        self.progress_frame = ttk.Frame(self.left_panel, style="TFrame")
        self.progress_frame.grid(row=4, column=0, sticky='ew', padx=self.ui_padding, pady=self.ui_padding)
        self.progress_frame.grid_columnconfigure(0, weight=1)
        
        # 創建進度條
        self.progress = ttk.Progressbar(
            self.progress_frame, 
            orient="horizontal", 
            length=200, 
            mode="determinate",
            style="TProgressbar"
        )
        self.progress.grid(row=0, column=0, sticky='ew', padx=self.ui_padding, pady=self.ui_padding)
        
        # 默認隱藏進度條
        self.progress_frame.grid_remove()

    def on_tooltip_changed(self):
        """當 Tooltip 啟用狀態變更時"""
        enabled = self.tooltip_enabled_var.get()
        self.tooltip_manager.set_all_enabled(enabled)
        
        # 更新設定
        if "UI_Settings" not in self.parent.setup:
            self.parent.setup["UI_Settings"] = {}
        self.parent.setup["UI_Settings"]["ToolTip_Enabled"] = enabled
        
        # 保存設定
        from config_core import save_setup
        save_setup(self.parent.setup)
        
        # 顯示通知
        status = "啟用" if enabled else "停用"
        self.show_notification(f"已{status}元件提示功能", "info", 3000)

    def init_tooltips(self):
        """初始化所有UI元件的tooltip說明"""
        try:
            # 確保全域通知管理器已設定
            if not hasattr(self, 'global_notification_manager') or not self.global_notification_manager:
                # 嘗試從 parent 獲取全域通知管理器
                if hasattr(self.parent, 'notification_manager'):
                    self.global_notification_manager = self.parent.notification_manager
                    print("[DEBUG] 從 parent 獲取全域通知管理器")
                # 嘗試從 root 獲取全域通知管理器
                elif hasattr(self.root, 'notification_manager'):
                    self.global_notification_manager = self.root.notification_manager
                    print("[DEBUG] 從 root 獲取全域通知管理器")
                # 嘗試從 TabManager 獲取全域通知管理器
                elif hasattr(self.parent, 'tab_manager') and hasattr(self.parent.tab_manager, 'notification_manager'):
                    self.global_notification_manager = self.parent.tab_manager.notification_manager
                    print("[DEBUG] 從 tab_manager 獲取全域通知管理器")
            
            # 將全域通知管理器傳遞給 ToolTipManager
            self.tooltip_manager.global_notification_manager = self.global_notification_manager
            
            # 為所有元件添加 tooltip
            self._add_tooltip_to_widgets()
            
            print("[DEBUG] 已初始化所有 tooltip")
        except Exception as e:
            print(f"[ERROR] 初始化 tooltip 時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def _add_tooltip_to_widgets(self):
        """為所有元件添加 tooltip"""
        # COM 口相關元件
        self.tooltip_manager.add_tooltip(self.label_com, "COM 口選擇標籤")
        self.tooltip_manager.add_tooltip(self.combobox_com, "選擇要連接的 COM 口")
        self.tooltip_manager.add_tooltip(self.btn_refresh, "刷新 COM 口列表")
        self.tooltip_manager.add_tooltip(self.status_canvas, "連接狀態指示燈")
        
        # 指令相關元件
        self.tooltip_manager.add_tooltip(self.label_cmd, "指令選擇標籤")
        self.tooltip_manager.add_tooltip(self.combobox_cmd, "選擇要執行的指令")
        self.tooltip_manager.add_tooltip(self.btn_execute, "執行選定的指令")
        self.tooltip_manager.add_tooltip(self.label_timeout, "指令超時時間設定")
        self.tooltip_manager.add_tooltip(self.entry_timeout, "設定指令超時時間 (毫秒)")
        self.tooltip_manager.add_tooltip(self.label_end, "指令結束符設定")
        self.tooltip_manager.add_tooltip(self.combobox_end, "選擇指令結束符")
        
        # 分類按鈕
        for i, rb in enumerate(self.section_radiobuttons):
            if i < len(self.sections):
                self.tooltip_manager.add_tooltip(rb, f"顯示 {self.sections[i]} 分類的指令")
        
        # Ping 相關元件
        self.tooltip_manager.add_tooltip(self.label_ip, "IP 地址輸入標籤")
        self.tooltip_manager.add_tooltip(self.entry_ip, "輸入要 Ping 的 IP 地址")
        self.tooltip_manager.add_tooltip(self.btn_ping, "Ping 指定的 IP 地址")
        self.tooltip_manager.add_tooltip(self.btn_save_ip, "儲存當前 IP 到歷史記錄")
        self.tooltip_manager.add_tooltip(self.listbox_ip_history, "已儲存的 IP 歷史記錄")
        self.tooltip_manager.add_tooltip(self.btn_delete_ip, "刪除選定的 IP 記錄")
        self.tooltip_manager.add_tooltip(self.btn_clear_ip, "清空所有 IP 歷史記錄")
        
        # 設定相關元件
        self.tooltip_manager.add_tooltip(self.checkbtn_auto_exec, "啟用後，選擇指令時會自動執行")
        self.tooltip_manager.add_tooltip(self.checkbtn_tooltip, "啟用或停用元件提示功能")
        self.tooltip_manager.add_tooltip(self.btn_guide, "顯示使用說明")
        self.tooltip_manager.add_tooltip(self.btn_clear_output, "清空右側輸出區域")
        self.tooltip_manager.add_tooltip(self.btn_settings, "開啟進階設定視窗")
        
        # 進度條
        self.tooltip_manager.add_tooltip(self.progress, "指令執行進度")

    def on_com_port_changed(self, event=None):
        """當 COM 口選擇變更時，自動儲存到設定檔"""
        try:
            selected_com = self.combobox_com.get()
            if selected_com:
                print(f"[DEBUG] COM 口已變更為: {selected_com}")
                
                # 更新設定到 parent.setup
                if 'DUT_Control' not in self.parent.setup:
                    self.parent.setup['DUT_Control'] = {}
                self.parent.setup['DUT_Control']['Serial_COM_Port'] = selected_com
                
                # 保存完整的設定結構到檔案
                from config_core import load_setup, save_setup
                full_setup = load_setup()
                if 'DUT_Control' not in full_setup:
                    full_setup['DUT_Control'] = {}
                full_setup['DUT_Control']['Serial_COM_Port'] = selected_com
                save_setup(full_setup)
                
                # 顯示通知
                self.show_notification(f"COM 口已更新為 {selected_com}", "blue", 3000)
        except Exception as e:
            print(f"[ERROR] 儲存 COM 口設定時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def on_cmd_selected(self):
        """當選擇指令時的回調函數"""
        cmd_key = self.combobox_cmd.get()
        if cmd_key:
            section = self.section_var.get()
            cmd = self.parent.commands_by_section.get(section, {}).get(cmd_key, "")
            if not cmd:
                cmd = self.parent.commands_by_section.get("全部指令", {}).get(cmd_key, "")
            
            # 顯示選擇的指令內容
            self.show_notification(get_notification_text("cmd_selected", cmd_key), "blue", 3000)
            
            # 如果是特殊指令，顯示提示
            if cmd.startswith("DELAY:"):
                delay_time = cmd.split(":")[1]
                self.show_notification(get_notification_text("delay_cmd", delay_time), "purple", 3000)
            elif cmd.startswith("SHOW:"):
                message = cmd.split(":")[1]
                self.show_notification(get_notification_text("show_msg", message), "green", 3000)

    def show_system_status(self):
        """顯示系統狀態信息"""
        try:
            # 獲取 COM 口
            com = self.combobox_com.get() or "未選擇"
            
            # 獲取當前選擇的分類
            section = self.section_var.get()
            
            # 獲取指令數量
            cmd_count = len(self.parent.commands_by_section.get(section, {}))
            
            # 獲取超時設定
            timeout = self.entry_timeout.get() or "30"
            
            # 顯示系統狀態
            self.show_notification(get_notification_text("system_status", com, section, cmd_count, timeout), "blue", 5000)
        except Exception as e:
            print(f"[ERROR] 顯示系統狀態時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def change_notification_font_size(self, delta):
        """修改通知區域字體大小"""
        try:
            # 原本的通知區域已被全域通知管理器取代，不再需要
            pass
        except Exception as e:
            print(f"[ERROR] 修改通知區域字體大小時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def copy_selected_text(self):
        # 實現複製選中文字的功能
        try:
            selected_text = self.text_output.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.parent.root.clipboard_clear()
                self.parent.root.clipboard_append(selected_text)
                self.show_notification(get_notification_text("text_copied"), "green", 2000)
        except tk.TclError:
            # 如果沒有選中文字，會拋出 TclError
            self.show_notification(get_notification_text("no_text_selected"), "orange", 2000)

    def select_all_text(self):
        # 實現全選文字的功能
        self.text_output.tag_add(tk.SEL, "1.0", tk.END)
        self.show_notification(get_notification_text("all_text_selected"), "green", 2000)

    def show_output_context_menu(self, event):
        """顯示輸出區域的右鍵菜單"""
        try:
            self.output_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"[ERROR] 顯示右鍵菜單時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def load_ip_history(self):
        """載入IP記錄到下拉選單"""
        try:
            from config_core import load_setup
            setup = load_setup()
            ip_history = setup.get('DUT_Control', {}).get('IP_History', [])
            
            # 確保IP記錄是列表
            if not isinstance(ip_history, list):
                ip_history = []
            
            # 移除重複項目並保持順序
            unique_ips = []
            for ip in ip_history:
                if ip not in unique_ips:
                    unique_ips.append(ip)
            
            # 限制最多保存20個IP記錄
            if len(unique_ips) > 20:
                unique_ips = unique_ips[-20:]
            
            self.entry_ip['values'] = unique_ips
            print(f"[INFO] 載入 {len(unique_ips)} 個IP記錄")
            
        except Exception as e:
            print(f"[ERROR] 載入IP記錄時發生錯誤: {e}")
            self.entry_ip['values'] = []

    def save_current_ip(self):
        """保存當前IP到記錄中"""
        try:
            current_ip = self.entry_ip.get().strip()
            if not current_ip:
                from tkinter import messagebox
                messagebox.showwarning("警告", "請輸入IP地址")
                return
                
            # 簡單的IP格式檢查
            import re
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if not re.match(ip_pattern, current_ip):
                from tkinter import messagebox
                messagebox.showwarning("警告", "請輸入有效的IP地址格式")
                return
            
            from config_core import load_setup, save_setup
            setup = load_setup()
            
            if 'DUT_Control' not in setup:
                setup['DUT_Control'] = {}
            if 'IP_History' not in setup['DUT_Control']:
                setup['DUT_Control']['IP_History'] = []
            
            ip_history = setup['DUT_Control']['IP_History']
            
            # 如果IP已存在，先移除然後加到最前面
            if current_ip in ip_history:
                ip_history.remove(current_ip)
            ip_history.insert(0, current_ip)
            
            # 限制最多保存20個記錄
            if len(ip_history) > 20:
                ip_history = ip_history[:20]
            
            setup['DUT_Control']['IP_History'] = ip_history
            save_setup(setup)
            
            # 重新載入下拉選單
            self.load_ip_history()
            
            from tkinter import messagebox
            messagebox.showinfo("成功", f"IP地址 {current_ip} 已保存到記錄中")
            print(f"[INFO] IP {current_ip} 已保存到記錄")
            
        except Exception as e:
            print(f"[ERROR] 保存IP記錄時發生錯誤: {e}")
            from tkinter import messagebox
            messagebox.showerror("錯誤", f"保存IP記錄失敗: {e}")

    def delete_current_ip(self):
        """從記錄中刪除當前選中的IP"""
        try:
            current_ip = self.entry_ip.get().strip()
            if not current_ip:
                from tkinter import messagebox
                messagebox.showwarning("警告", "請選擇要刪除的IP地址")
                return
                
            from config_core import load_setup, save_setup
            setup = load_setup()
            
            ip_history = setup.get('DUT_Control', {}).get('IP_History', [])
            
            if current_ip not in ip_history:
                from tkinter import messagebox
                messagebox.showwarning("警告", "該IP地址不在記錄中")
                return
            
            # 詢問確認
            from tkinter import messagebox
            result = messagebox.askyesno("確認刪除", f"確定要刪除IP地址 {current_ip} 嗎？")
            if not result:
                return
            
            ip_history.remove(current_ip)
            setup['DUT_Control']['IP_History'] = ip_history
            save_setup(setup)
            
            # 重新載入下拉選單
            self.load_ip_history()
            
            # 清空輸入框
            self.entry_ip.set("")
            
            messagebox.showinfo("成功", f"IP地址 {current_ip} 已從記錄中刪除")
            print(f"[INFO] IP {current_ip} 已從記錄中刪除")
            
        except Exception as e:
            print(f"[ERROR] 刪除IP記錄時發生錯誤: {e}")
            from tkinter import messagebox
            messagebox.showerror("錯誤", f"刪除IP記錄失敗: {e}")

    def clear_ip_history(self):
        """清空所有IP記錄"""
        try:
            from tkinter import messagebox
            result = messagebox.askyesno("確認清空", "確定要清空所有IP記錄嗎？此操作無法恢復。")
            if not result:
                return
                
            from config_core import load_setup, save_setup
            setup = load_setup()
            
            if 'DUT_Control' not in setup:
                setup['DUT_Control'] = {}
            setup['DUT_Control']['IP_History'] = []
            save_setup(setup)
            
            # 重新載入下拉選單
            self.load_ip_history()
            
            messagebox.showinfo("成功", "所有IP記錄已清空")
            print(f"[INFO] 所有IP記錄已清空")
            
        except Exception as e:
            print(f"[ERROR] 清空IP記錄時發生錯誤: {e}")
            from tkinter import messagebox
            messagebox.showerror("錯誤", f"清空IP記錄失敗: {e}")

    def on_ping_with_save(self):
        """執行Ping並自動保存IP到記錄"""
        try:
            current_ip = self.entry_ip.get().strip()
            if current_ip:
                # 執行Ping前自動保存IP到記錄
                self.save_current_ip_silent()
            
            # 執行Ping操作
            if hasattr(self.parent, 'handlers') and hasattr(self.parent.handlers, 'on_ping'):
                self.parent.handlers.on_ping()
            else:
                print("[ERROR] 找不到ping處理程序")
                
        except Exception as e:
            print(f"[ERROR] 執行Ping時發生錯誤: {e}")

    def save_current_ip_silent(self):
        """靜默保存當前IP（不顯示訊息框）"""
        try:
            current_ip = self.entry_ip.get().strip()
            if not current_ip:
                return
                
            # 簡單的IP格式檢查
            import re
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if not re.match(ip_pattern, current_ip):
                return
            
            from config_core import load_setup, save_setup
            setup = load_setup()
            
            if 'DUT_Control' not in setup:
                setup['DUT_Control'] = {}
            if 'IP_History' not in setup['DUT_Control']:
                setup['DUT_Control']['IP_History'] = []
            
            ip_history = setup['DUT_Control']['IP_History']
            
            # 如果IP已存在，先移除然後加到最前面
            if current_ip in ip_history:
                ip_history.remove(current_ip)
            ip_history.insert(0, current_ip)
            
            # 限制最多保存20個記錄
            if len(ip_history) > 20:
                ip_history = ip_history[:20]
            
            setup['DUT_Control']['IP_History'] = ip_history
            save_setup(setup)
            
            # 重新載入下拉選單
            self.load_ip_history()
            
            print(f"[INFO] IP {current_ip} 已自動保存到記錄")
            
        except Exception as e:
            print(f"[ERROR] 自動保存IP記錄時發生錯誤: {e}")

    def update_progress(self, value, style="blue.Horizontal.TProgressbar"):
        """更新進度條值和樣式"""
        print(f"[DEBUG] update_progress: value={value}, style={style}")
        self.progress.config(style=style, value=value)
        self.progress.grid()  # 確保進度條顯示

    def reset_progress(self):
        """重置進度條並隱藏"""
        try:
            print("[DEBUG] reset_progress: set progress to 0 and hide")
            self.progress['value'] = 0
            self.show_progress(False)  # 隱藏進度條
            
            # 取消所有與進度條相關的定時器
            if hasattr(self.parent, 'root'):
                # 檢查是否有標記的進度條更新任務
                if hasattr(self.parent.handlers, '_progress_update_job') and self.parent.handlers._progress_update_job:
                    try:
                        self.parent.root.after_cancel(self.parent.handlers._progress_update_job)
                        self.parent.handlers._progress_update_job = None
                        print("[DEBUG] 已取消進度條更新任務")
                    except Exception as e:
                        print(f"[ERROR] 取消進度條更新任務時發生錯誤: {e}")
        except Exception as e:
            print(f"[ERROR] 重置進度條時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def update_radio_bg(self):
        selected = self.section_var.get()
        for rb, sec in zip(self.section_radiobuttons, self.sections):
            if rb['state'] == 'disabled':
                rb.config(bg="#e0e0e0", fg="#b0b0b0", activebackground="#e0e0e0", activeforeground="#b0b0b0")
            elif selected == sec:
                rb.config(bg="#2196f3", fg="white", activebackground="#2196f3", activeforeground="white")
            else:
                rb.config(bg="#d9d9d9", fg="black", activebackground="#d9d9d9", activeforeground="black")

    def update_cmd_list(self):
        """更新指令下拉選單的選項
        
        此方法會重新解析指令文件，並根據當前選擇的分類更新下拉選單的選項。
        當設定中的指令檔路徑變更時，此方法會被調用以重新載入指令。
        """
        # 重新讀取指令文件 - 確保每次都從設定中獲取最新的指令檔路徑
        print("[DEBUG] update_cmd_list: 重新解析指令文件")
        
        # 強制重新載入設定，確保獲取最新的指令檔路徎
        self.parent.setup = self.parent.config.load_setup()
        self.parent.handlers.reload_setup(self.parent.setup)
        
        # 解析指令文件
        self.parent.commands_by_section = self.parent.handlers.parse_commands_by_section()
        
        # 檢查是否需要重新生成分類按鈕
        available_sections = list(self.parent.commands_by_section.keys())
        current_sections = getattr(self, 'sections', [])
        
        print(f"[DEBUG] update_cmd_list: 當前分類按鈕: {current_sections}")
        print(f"[DEBUG] update_cmd_list: 檔案中的分類: {available_sections}")
        
        # 如果分類有變化，重新生成分類按鈕
        if set(current_sections) != set(available_sections):
            print("[DEBUG] update_cmd_list: 分類有變化，重新生成分類按鈕")
            self.regenerate_section_buttons(available_sections)
        
        # 獲取當前選擇的分類
        section = self.section_var.get()
        
        # 檢查當前選擇的分類是否存在於解析後的指令中
        if section not in self.parent.commands_by_section:
            print(f"[WARNING] 選擇的分類 '{section}' 不存在，使用第一個可用的分類")
            if self.parent.commands_by_section:
                # 使用第一個可用的分類
                section = next(iter(self.parent.commands_by_section.keys()))
                self.section_var.set(section)
            else:
                # 如果沒有可用的分類，使用預設值
                section = '全部指令'
                self.section_var.set(section)
        
        # 更新按鈕背景和說明文字
        self.update_radio_bg()
        self.section_description.config(text=self.get_section_description(section))
        
        # 獲取當前分類的指令
        cmds = self.parent.commands_by_section.get(section, {})
        if not cmds and section != '全部指令':  # 如果沒有找到對應分類的指令，使用全部指令
            cmds = self.parent.commands_by_section.get('全部指令', {})
            
        # 更新下拉選單選項
        self.combobox_cmd['values'] = list(cmds.keys())
        
        # 自動選中第一個指令
        if cmds:
            first_cmd = list(cmds.keys())[0]
            self.combobox_cmd.set(first_cmd)
        else:
            self.combobox_cmd.set('')
            
        print(f"[DEBUG] update_cmd_list: 已更新指令下拉選單，共 {len(cmds)} 個指令")

    def regenerate_section_buttons(self, new_sections):
        """重新生成分類按鈕"""
        try:
            print(f"[DEBUG] regenerate_section_buttons: 重新生成分類按鈕，新分類: {new_sections}")
            
            # 清除現有的分類按鈕
            if hasattr(self, 'section_radiobuttons'):
                for rb in self.section_radiobuttons:
                    rb.destroy()
                self.section_radiobuttons = []
            
            # 更新分類列表
            self.sections = new_sections
            
            # 更新設定檔中的分類標題
            self.update_section_titles_in_config(new_sections)
            
            # 設定預設選中的分類
            if self.sections:
                current_selection = self.section_var.get()
                if current_selection not in self.sections:
                    # 如果當前選擇的分類不在新分類中，選擇第一個分類
                    self.section_var.set(self.sections[0])
                    print(f"[DEBUG] regenerate_section_buttons: 設定預設選中的分類: {self.sections[0]}")
            
            # 限制每行最多顯示4個按鈕
            max_buttons_per_row = 4
            self.section_radiobuttons = []
            
            # 創建新的分類按鈕
            for i, sec in enumerate(self.sections):
                # 計算行和列位置
                row = i // max_buttons_per_row
                col = i % max_buttons_per_row
                
                rb = tk.Radiobutton(
                    self.section_frame, text=sec, variable=self.section_var, value=sec, 
                    command=self.update_cmd_list,
                    bg='#d9d9d9', fg='black', selectcolor='#d9d9d9', 
                    activebackground='#2196f3', activeforeground='white',
                    indicatoron=0, relief='flat', borderwidth=1, width=8, height=1,
                    font=('Microsoft JhengHei UI', int(self.parent.setup.get('UI_Font_Size', '12')))
                )
                rb.grid(row=row, column=col, padx=1, pady=1, sticky='ew')
                rb.bind("<Enter>", lambda e, b=rb: b.config(bg="#2196f3", fg='white'))
                rb.bind("<Leave>", lambda e, b=rb: self.update_radio_bg())
                self.section_radiobuttons.append(rb)
                
                # 設置列的權重，使按鈕平均分配空間
                self.section_frame.columnconfigure(col, weight=1)
            
            # 更新按鈕背景色
            self.update_radio_bg()
            
            # 更新說明文字的位置
            if hasattr(self, 'section_description'):
                last_row = (len(self.sections) - 1) // max_buttons_per_row + 1
                self.section_description.grid(row=last_row, column=0, columnspan=max_buttons_per_row, pady=2, sticky='w')
            
            print(f"[DEBUG] regenerate_section_buttons: 已重新生成 {len(self.sections)} 個分類按鈕")
            
        except Exception as e:
            print(f"[ERROR] regenerate_section_buttons: 重新生成分類按鈕時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def update_section_titles_in_config(self, section_titles):
        """更新設定檔中的分類標題"""
        try:
            from config_core import load_setup, save_setup
            
            # 載入當前設定
            setup = load_setup()
            
            # 確保 DUT_Control 存在
            if 'DUT_Control' not in setup:
                setup['DUT_Control'] = {}
            
            # 更新分類標題
            setup['DUT_Control']['Section_Titles'] = section_titles
            
            # 保存設定
            save_setup(setup)
            
            print(f"[DEBUG] update_section_titles_in_config: 已更新設定檔中的分類標題: {section_titles}")
            
        except Exception as e:
            print(f"[ERROR] update_section_titles_in_config: 更新設定檔中的分類標題時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def update_end_strings(self):
        try:
            end_strings = json.loads(self.parent.setup.get('Available_End_Strings', '["root"]'))
        except Exception:
            end_strings = ['root']
        self.combobox_end['values'] = end_strings

    def add_to_buffer(self, text, tag=None):
        if hasattr(self.parent, 'showing_guide') and self.parent.showing_guide:
            return
        self.text_output.configure(state='normal')
        if text.startswith('[發送]'):
            self.text_output.insert(tk.END, text, "send")
        elif text.startswith('[結束]'):
            self.text_output.insert(tk.END, text, "end")
        elif "inserted" in text:
            self.text_output.insert(tk.END, text, "purple")
        elif tag:
            self.text_output.insert(tk.END, text, tag)
        else:
            # 關鍵字高亮：每行只要包含 color_word.txt 的任一關鍵字就上色
            if hasattr(self.parent, 'highlight_keywords') and self.parent.highlight_keywords and hasattr(self, 'keyword_tag_map'):
                start_pos = self.text_output.index(tk.END)
                self.text_output.insert(tk.END, text)
                
                # 按關鍵字長度降序排列，讓較長的關鍵字優先匹配
                sorted_keywords = sorted(self.keyword_tag_map.items(), key=lambda x: len(x[0]), reverse=True)
                
                for keyword, tag_name in sorted_keywords:
                    search_start = start_pos
                    while True:
                        idx = self.text_output.search(keyword, search_start, tk.END)
                        if not idx:
                            break
                        end_idx = f"{idx}+{len(keyword)}c"
                        try:
                            self.text_output.tag_add(tag_name, idx, end_idx)
                            print(f"[DEBUG] 應用關鍵字高亮: '{keyword}' 於位置 {idx}-{end_idx}, 標籤: {tag_name}")
                        except Exception as e:
                            print(f"[ERROR] tag_add 失敗: {e}")
                        search_start = end_idx
            else:
                self.text_output.insert(tk.END, text)
        self.text_output.see(tk.END)
        self.text_output.configure(state='disabled')

    def update_ui_fonts(self, size=None):
        try:
            if size is None:
                size = int(self.ui_font_scale.get())
            font = ('Microsoft JhengHei UI', size)
            # 更新所有標籤和按鈕
            widgets = [
                self.label_com, self.label_cmd, self.label_end, self.label_timeout,
                self.label_ui_font, self.label_content_font, self.btn_refresh,
                self.btn_clear, self.btn_backup, self.btn_guide, self.label_ip, self.btn_ping
            ]
            for w in widgets:
                if w.winfo_exists():
                    try:
                        w.configure(font=font)
                    except Exception:
                        # 如果設定字體失敗，嘗試使用其他方式
                        try:
                            w['font'] = font
                        except Exception:
                            pass
            # 更新 section_radiobuttons 字體
            for rb in getattr(self, 'section_radiobuttons', []):
                if rb.winfo_exists():
                    try:
                        rb.configure(font=font)
                    except Exception:
                        try:
                            rb['font'] = font
                        except Exception:
                            pass
            # 更新輸入框和下拉選單
            for widget in [self.combobox_com, self.combobox_cmd, self.combobox_end, 
                         self.entry_timeout, self.entry_ip]:
                if widget.winfo_exists():
                    try:
                        widget.configure(font=('Consolas', size))
                    except Exception:
                        try:
                            widget['font'] = ('Consolas', size)
                        except Exception:
                            pass
            # 更新 ttk 樣式
            try:
                style = ttk.Style()
                style.configure("TLabelframe.Label", font=font)
                style.configure("TLabelframe", font=font)
                style.configure("TLabel", font=font)
            except Exception:
                pass
            # 強制更新 UI
            self.parent.root.update_idletasks()
        except Exception as e:
            print(f"[DEBUG] 更新介面字體時發生錯誤: {e}")
            # 不要讓錯誤影響程式運行

    def update_content_fonts(self, size=None):
        try:
            if size is None:
                size = int(self.content_font_scale.get())
            content_font = ('Consolas', size)
            # 更新文字輸出區域
            if self.text_output.winfo_exists():
                try:
                    self.text_output.configure(font=content_font)
                except Exception:
                    try:
                        self.text_output['font'] = content_font
                    except Exception:
                        pass
            # 更新所有下拉選單與輸入框
            for widget in [self.combobox_com, self.combobox_cmd, self.combobox_end, self.entry_timeout, self.entry_ip]:
                if widget.winfo_exists():
                    try:
                        widget.configure(font=content_font)
                    except Exception:
                        try:
                            widget['font'] = content_font
                        except Exception:
                            pass
            # 根據字體大小自動調整 combobox_cmd 寬度
            min_width = 25
            width = max(min_width, int(size * 2.2))
            try:
                self.combobox_cmd.config(width=width)
            except Exception:
                pass
            # 強制 combobox 下拉選單選項字體同步
            try:
                self.parent.root.option_add('*TCombobox*Listbox.font', content_font)
            except Exception as e:
                print(f'[DEBUG] Combobox Listbox 字體設置失敗: {e}')
            # # 更新使用說明視窗
            # if self.parent.guide_window and self.parent.guide_window.winfo_exists():
            #     for widget in self.parent.guide_window.winfo_children():
            #         if isinstance(widget, scrolledtext.ScrolledText) and widget.winfo_exists():
            #             try:
            #                 widget.configure(font=content_font)
            #             except Exception:
            #                 try:
            #                     widget['font'] = content_font
            #                 except Exception:
            #                     pass
            self.parent.root.update_idletasks()
        except Exception as e:
            print(f"[DEBUG] 更新內容字體時發生錯誤: {e}")
            # 不要讓錯誤影響程式運行

    def on_window_resize(self, event):
        # 只在主視窗且尺寸真的有變時記錄
        if event.widget == self.parent.root:
            w, h = event.width, event.height
            if (w, h) != self.last_size and w > 200 and h > 200:
                self.last_size = (w, h)
                # 更新當前設定
                self.parent.setup['Window_Width'] = str(w)
                self.parent.setup['Window_Height'] = str(h)
                # 保存完整的設定結構
                from config_core import load_setup, save_setup
                full_setup = load_setup()
                full_setup['DUT_Control'].update({
                    'Window_Width': str(w),
                    'Window_Height': str(h)
                })
                save_setup(full_setup)
                print(f"[DEBUG] 視窗大小已保存: {w}x{h}")
        # 不再自動縮放字體

    def stop_led_blink(self):
        self.led_blinking = False
        # 恢復為黑色，表示待命狀態
        self.status_canvas.itemconfig(self.status_light, fill='black')

    def on_pane_position_changed(self, event):
        """當 PanedWindow 分割位置改變時保存位置"""
        try:
            # 獲取當前分割位置
            sash_position = self.main_frame.sashpos(0)  # 第一個分割線的位置
            print(f"[DEBUG] PanedWindow 分割位置變更: {sash_position}")
            
            # 保存到設定中
            self.parent.setup['Pane_Sash_Position'] = str(sash_position)
            
            # 保存完整的設定結構
            from config_core import load_setup, save_setup
            full_setup = load_setup()
            full_setup['DUT_Control']['Pane_Sash_Position'] = str(sash_position)
            save_setup(full_setup)
            
        except Exception as e:
            print(f"[DEBUG] 保存分割位置時發生錯誤: {e}")

    def restore_pane_position(self):
        """恢復 PanedWindow 分割位置"""
        try:
            # 從設定中讀取分割位置
            sash_position = self.parent.setup.get('Pane_Sash_Position', '')
            if sash_position:
                position = int(sash_position)
                # 確保位置在合理範圍內
                window_width = self.parent.root.winfo_width()
                if 100 <= position <= window_width - 100:
                    self.main_frame.sashpos(0, position)
                    print(f"[DEBUG] 已恢復 PanedWindow 分割位置: {position}")
                else:
                    print(f"[DEBUG] 分割位置 {position} 超出範圍，使用預設位置")
            else:
                print(f"[DEBUG] 沒有保存的分割位置，使用預設位置")
        except Exception as e:
            print(f"[DEBUG] 恢復分割位置時發生錯誤: {e}")

    def limit_dropdown_height(self, event=None):
        """限制下拉列表的高度，最多顯示指定行數"""
        try:
            # 獲取下拉列表
            combo = self.combobox_cmd
            popup = combo.tk.call("ttk::combobox::PopdownWindow", combo)
            listbox = combo.tk.nametowidget(popup).winfo_children()[0]
            
            # 獲取項目總數和設置的最大顯示數
            total_items = len(combo['values'])
            max_items = min(total_items, self.max_dropdown_items)
            
            # 計算單個項目的高度（以像素為單位）
            item_height = 20  # 預設值，可能需要根據字體大小調整
            
            # 設置列表框的高度
            if max_items > 0:
                listbox.configure(height=max_items)
                print(f"[DEBUG] 限制下拉列表高度為 {max_items} 行")
            
        except Exception as e:
            print(f"[ERROR] 限制下拉列表高度時發生錯誤：{e}")
            import traceback
            traceback.print_exc()

    def on_auto_exec_changed(self):
        """當自動執行勾選框狀態變更時，保存設置"""
        try:
            # 獲取當前勾選狀態
            auto_exec = self.auto_exec_var.get()
            print(f"[DEBUG] 自動執行設置已變更為: {auto_exec}")
            
            # 更新設置到 parent.setup
            if 'DUT_Control' not in self.parent.setup:
                self.parent.setup['DUT_Control'] = {}
            self.parent.setup['DUT_Control']['Auto_Execute'] = auto_exec
            
            # 保存完整的設定結構到檔案
            from config_core import load_setup, save_setup
            full_setup = load_setup()
            if 'DUT_Control' not in full_setup:
                full_setup['DUT_Control'] = {}
            full_setup['DUT_Control']['Auto_Execute'] = auto_exec
            save_setup(full_setup)
            
            # 顯示通知給使用者
            message_key = "auto_exec_enabled" if auto_exec else "auto_exec_disabled"
            self.show_notification(
                get_notification_text(message_key),
                "green" if auto_exec else "blue",
                3000
            )
            
            print(f"[DEBUG] 自動執行設置已保存: {auto_exec}")
        except Exception as e:
            print(f"[ERROR] 保存自動執行設置時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            self.show_notification(get_notification_text("save_failed", str(e)), "red", 5000)

    def show_notification(self, message, color="info", duration=2000, callback=None):
        """
        統一的通知顯示方法，優先使用全域通知管理器
        
        參數:
            message: 要顯示的消息
            color: 訊息類型 ("info", "success", "warning", "error") 或顏色名稱
            duration: 顯示時間(毫秒)，默認2秒
            callback: 通知結束後要調用的回調函數
        """
        # 轉換顏色名稱到訊息類型
        color_mapping = {
            "blue": "info",
            "green": "success", 
            "orange": "warning",
            "red": "error",
            "purple": "info",
            "black": "default"
        }
        
        message_type = color_mapping.get(color, color)
        
        # 優先使用全域通知管理器
        try:
            if self.global_notification_manager:
                self.global_notification_manager.show_notification(message, message_type)
                return
            
            # 嘗試尋找TabManager並使用其通知管理器
            current_widget = self.root
            while current_widget:
                if hasattr(current_widget, 'notification_manager'):
                    current_widget.notification_manager.show_notification(message, message_type)
                    return
                current_widget = getattr(current_widget, 'master', None)
            
            # 如果找不到全域通知管理器，使用本地通知（備用方案）
            print(f"[INFO] 未找到全域通知管理器，使用本地通知: {message}")
            self._show_local_notification(message, color, duration, callback)
            
        except Exception as e:
            print(f"[ERROR] 顯示全域通知失敗，使用本地通知: {e}")
            self._show_local_notification(message, color, duration, callback)
    
    def _show_local_notification(self, message, color="red", duration=5000, callback=None):
        """
        本地通知顯示方法（備用方案）
        """
        # 原本的通知區域已被全域通知管理器取代，不再需要
        pass

    def _restore_after_notification(self, original_fg, callback=None):
        """通知結束後恢復"""
        # 原本的通知區域已被全域通知管理器取代，不再需要
        pass

    def on_cmd_selected(self):
        """當選擇指令時的回調函數"""
        cmd_key = self.combobox_cmd.get()
        if cmd_key:
            section = self.section_var.get()
            cmd = self.parent.commands_by_section.get(section, {}).get(cmd_key, "")
            if not cmd:
                cmd = self.parent.commands_by_section.get("全部指令", {}).get(cmd_key, "")
            
            # 顯示選擇的指令內容
            self.show_notification(get_notification_text("cmd_selected", cmd_key), "blue", 3000)
            
            # 如果是特殊指令，顯示提示
            if cmd.startswith("DELAY:"):
                delay_time = cmd.split(":")[1]
                self.show_notification(get_notification_text("delay_cmd", delay_time), "purple", 3000)
            elif cmd.startswith("SHOW:"):
                message = cmd.split(":")[1]
                self.show_notification(get_notification_text("show_msg", message), "green", 3000)

    def show_system_status(self):
        """顯示系統狀態信息"""
        try:
            # 獲取 COM 口
            com = self.combobox_com.get() or "未選擇"
            
            # 獲取當前選擇的分類
            section = self.section_var.get()
            
            # 獲取指令數量
            cmd_count = len(self.parent.commands_by_section.get(section, {}))
            
            # 獲取超時設定
            timeout = self.entry_timeout.get() or "30"
            
            # 顯示系統狀態
            self.show_notification(get_notification_text("system_status", com, section, cmd_count, timeout), "blue", 5000)
        except Exception as e:
            print(f"[ERROR] 顯示系統狀態時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def copy_selected_text(self):
        # 實現複製選中文字的功能
        try:
            selected_text = self.text_output.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.parent.root.clipboard_clear()
                self.parent.root.clipboard_append(selected_text)
                self.show_notification(get_notification_text("text_copied"), "green", 2000)
        except tk.TclError:
            # 如果沒有選中文字，會拋出 TclError
            self.show_notification(get_notification_text("no_text_selected"), "orange", 2000)

    def select_all_text(self):
        # 實現全選文字的功能
        self.text_output.tag_add(tk.SEL, "1.0", tk.END)
        self.show_notification(get_notification_text("all_text_selected"), "green", 2000)

    def show_output_context_menu(self, event):
        """顯示輸出區域的右鍵菜單"""
        try:
            self.output_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"[ERROR] 顯示右鍵菜單時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def load_ip_history(self):
        """載入IP記錄到下拉選單"""
        try:
            from config_core import load_setup
            setup = load_setup()
            ip_history = setup.get('DUT_Control', {}).get('IP_History', [])
            
            # 確保IP記錄是列表
            if not isinstance(ip_history, list):
                ip_history = []
            
            # 移除重複項目並保持順序
            unique_ips = []
            for ip in ip_history:
                if ip not in unique_ips:
                    unique_ips.append(ip)
            
            # 限制最多保存20個IP記錄
            if len(unique_ips) > 20:
                unique_ips = unique_ips[-20:]
            
            self.entry_ip['values'] = unique_ips
            print(f"[INFO] 載入 {len(unique_ips)} 個IP記錄")
            
        except Exception as e:
            print(f"[ERROR] 載入IP記錄時發生錯誤: {e}")
            self.entry_ip['values'] = []

    def save_current_ip(self):
        """保存當前IP到記錄中"""
        try:
            current_ip = self.entry_ip.get().strip()
            if not current_ip:
                from tkinter import messagebox
                messagebox.showwarning("警告", "請輸入IP地址")
                return
                
            # 簡單的IP格式檢查
            import re
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if not re.match(ip_pattern, current_ip):
                from tkinter import messagebox
                messagebox.showwarning("警告", "請輸入有效的IP地址格式")
                return
            
            from config_core import load_setup, save_setup
            setup = load_setup()
            
            if 'DUT_Control' not in setup:
                setup['DUT_Control'] = {}
            if 'IP_History' not in setup['DUT_Control']:
                setup['DUT_Control']['IP_History'] = []
            
            ip_history = setup['DUT_Control']['IP_History']
            
            # 如果IP已存在，先移除然後加到最前面
            if current_ip in ip_history:
                ip_history.remove(current_ip)
            ip_history.insert(0, current_ip)
            
            # 限制最多保存20個記錄
            if len(ip_history) > 20:
                ip_history = ip_history[:20]
            
            setup['DUT_Control']['IP_History'] = ip_history
            save_setup(setup)
            
            # 重新載入下拉選單
            self.load_ip_history()
            
            from tkinter import messagebox
            messagebox.showinfo("成功", f"IP地址 {current_ip} 已保存到記錄中")
            print(f"[INFO] IP {current_ip} 已保存到記錄")
            
        except Exception as e:
            print(f"[ERROR] 保存IP記錄時發生錯誤: {e}")
            from tkinter import messagebox
            messagebox.showerror("錯誤", f"保存IP記錄失敗: {e}")

    def delete_current_ip(self):
        """從記錄中刪除當前選中的IP"""
        try:
            current_ip = self.entry_ip.get().strip()
            if not current_ip:
                from tkinter import messagebox
                messagebox.showwarning("警告", "請選擇要刪除的IP地址")
                return
                
            from config_core import load_setup, save_setup
            setup = load_setup()
            
            ip_history = setup.get('DUT_Control', {}).get('IP_History', [])
            
            if current_ip not in ip_history:
                from tkinter import messagebox
                messagebox.showwarning("警告", "該IP地址不在記錄中")
                return
            
            # 詢問確認
            from tkinter import messagebox
            result = messagebox.askyesno("確認刪除", f"確定要刪除IP地址 {current_ip} 嗎？")
            if not result:
                return
            
            ip_history.remove(current_ip)
            setup['DUT_Control']['IP_History'] = ip_history
            save_setup(setup)
            
            # 重新載入下拉選單
            self.load_ip_history()
            
            # 清空輸入框
            self.entry_ip.set("")
            
            messagebox.showinfo("成功", f"IP地址 {current_ip} 已從記錄中刪除")
            print(f"[INFO] IP {current_ip} 已從記錄中刪除")
            
        except Exception as e:
            print(f"[ERROR] 刪除IP記錄時發生錯誤: {e}")
            from tkinter import messagebox
            messagebox.showerror("錯誤", f"刪除IP記錄失敗: {e}")

    def clear_ip_history(self):
        """清空所有IP記錄"""
        try:
            from tkinter import messagebox
            result = messagebox.askyesno("確認清空", "確定要清空所有IP記錄嗎？此操作無法恢復。")
            if not result:
                return
                
            from config_core import load_setup, save_setup
            setup = load_setup()
            
            if 'DUT_Control' not in setup:
                setup['DUT_Control'] = {}
            setup['DUT_Control']['IP_History'] = []
            save_setup(setup)
            
            # 重新載入下拉選單
            self.load_ip_history()
            
            messagebox.showinfo("成功", "所有IP記錄已清空")
            print(f"[INFO] 所有IP記錄已清空")
            
        except Exception as e:
            print(f"[ERROR] 清空IP記錄時發生錯誤: {e}")
            from tkinter import messagebox
            messagebox.showerror("錯誤", f"清空IP記錄失敗: {e}")

    def on_ping_with_save(self):
        """執行Ping並自動保存IP到記錄"""
        try:
            current_ip = self.entry_ip.get().strip()
            if current_ip:
                # 執行Ping前自動保存IP到記錄
                self.save_current_ip_silent()
            
            # 執行Ping操作
            if hasattr(self.parent, 'handlers') and hasattr(self.parent.handlers, 'on_ping'):
                self.parent.handlers.on_ping()
            else:
                print("[ERROR] 找不到ping處理程序")
                
        except Exception as e:
            print(f"[ERROR] 執行Ping時發生錯誤: {e}")

    def save_current_ip_silent(self):
        """靜默保存當前IP（不顯示訊息框）"""
        try:
            current_ip = self.entry_ip.get().strip()
            if not current_ip:
                return
                
            # 簡單的IP格式檢查
            import re
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if not re.match(ip_pattern, current_ip):
                return
            
            from config_core import load_setup, save_setup
            setup = load_setup()
            
            if 'DUT_Control' not in setup:
                setup['DUT_Control'] = {}
            if 'IP_History' not in setup['DUT_Control']:
                setup['DUT_Control']['IP_History'] = []
            
            ip_history = setup['DUT_Control']['IP_History']
            
            # 如果IP已存在，先移除然後加到最前面
            if current_ip in ip_history:
                ip_history.remove(current_ip)
            ip_history.insert(0, current_ip)
            
            # 限制最多保存20個記錄
            if len(ip_history) > 20:
                ip_history = ip_history[:20]
            
            setup['DUT_Control']['IP_History'] = ip_history
            save_setup(setup)
            
            # 重新載入下拉選單
            self.load_ip_history()
            
            print(f"[INFO] IP {current_ip} 已自動保存到記錄")
            
        except Exception as e:
            print(f"[ERROR] 自動保存IP記錄時發生錯誤: {e}")

    def init_tooltips(self):
        """初始化所有UI元件的tooltip說明"""
        try:
            # 確保全域通知管理器已設定
            if not hasattr(self, 'global_notification_manager') or not self.global_notification_manager:
                # 嘗試從 parent 獲取全域通知管理器
                if hasattr(self.parent, 'notification_manager'):
                    self.global_notification_manager = self.parent.notification_manager
                    print("[DEBUG] 從 parent 獲取全域通知管理器")
                # 嘗試從 root 獲取全域通知管理器
                elif hasattr(self.root, 'notification_manager'):
                    self.global_notification_manager = self.root.notification_manager
                    print("[DEBUG] 從 root 獲取全域通知管理器")
                # 嘗試從 TabManager 獲取全域通知管理器
                elif hasattr(self.parent, 'tab_manager') and hasattr(self.parent.tab_manager, 'notification_manager'):
                    self.global_notification_manager = self.parent.tab_manager.notification_manager
                    print("[DEBUG] 從 tab_manager 獲取全域通知管理器")
            
            # 將全域通知管理器傳遞給 ToolTipManager
            self.tooltip_manager.global_notification_manager = self.global_notification_manager
            
            # 為所有元件添加 tooltip
            self._add_tooltip_to_widgets()
            
            print("[DEBUG] 已初始化所有 tooltip")
        except Exception as e:
            print(f"[ERROR] 初始化 tooltip 時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def _add_tooltip_to_widgets(self):
        """為所有元件添加 tooltip"""
        # COM 口相關元件
        self.tooltip_manager.add_tooltip(self.label_com, "COM 口選擇標籤")
        self.tooltip_manager.add_tooltip(self.combobox_com, "選擇要連接的 COM 口")
        self.tooltip_manager.add_tooltip(self.btn_refresh, "刷新 COM 口列表")
        self.tooltip_manager.add_tooltip(self.status_canvas, "連接狀態指示燈")
        
        # 指令相關元件
        self.tooltip_manager.add_tooltip(self.label_cmd, "指令選擇標籤")
        self.tooltip_manager.add_tooltip(self.combobox_cmd, "選擇要執行的指令")
        self.tooltip_manager.add_tooltip(self.btn_execute, "執行選定的指令")
        self.tooltip_manager.add_tooltip(self.label_timeout, "指令超時時間設定")
        self.tooltip_manager.add_tooltip(self.entry_timeout, "設定指令超時時間 (毫秒)")
        self.tooltip_manager.add_tooltip(self.label_end, "指令結束符設定")
        self.tooltip_manager.add_tooltip(self.combobox_end, "選擇指令結束符")
        
        # 分類按鈕
        for i, rb in enumerate(self.section_radiobuttons):
            if i < len(self.sections):
                self.tooltip_manager.add_tooltip(rb, f"顯示 {self.sections[i]} 分類的指令")
        
        # Ping 相關元件
        self.tooltip_manager.add_tooltip(self.label_ip, "IP 地址輸入標籤")
        self.tooltip_manager.add_tooltip(self.entry_ip, "輸入要 Ping 的 IP 地址")
        self.tooltip_manager.add_tooltip(self.btn_ping, "Ping 指定的 IP 地址")
        self.tooltip_manager.add_tooltip(self.btn_save_ip, "儲存當前 IP 到歷史記錄")
        self.tooltip_manager.add_tooltip(self.listbox_ip_history, "已儲存的 IP 歷史記錄")
        self.tooltip_manager.add_tooltip(self.btn_delete_ip, "刪除選定的 IP 記錄")
        self.tooltip_manager.add_tooltip(self.btn_clear_ip, "清空所有 IP 歷史記錄")
        
        # 設定相關元件
        self.tooltip_manager.add_tooltip(self.checkbtn_auto_exec, "啟用後，選擇指令時會自動執行")
        self.tooltip_manager.add_tooltip(self.checkbtn_tooltip, "啟用或停用元件提示功能")
        self.tooltip_manager.add_tooltip(self.btn_guide, "顯示使用說明")
        self.tooltip_manager.add_tooltip(self.btn_clear_output, "清空右側輸出區域")
        self.tooltip_manager.add_tooltip(self.btn_settings, "開啟進階設定視窗")
        
        # 進度條
        self.tooltip_manager.add_tooltip(self.progress, "指令執行進度")

    def on_enter_exec(self, event):
        self.btn_execute.config(bg='#2196F3')

    def on_leave_exec(self, event):
        self.btn_execute.config(bg='#4CAF50')

    def get_section_description(self, section):
        # 預設描述
        default_descriptions = {
            '全部指令': '顯示所有可用的指令',
            '單板指令': '用於單板測試的指令集',
            '整機指令': '用於整機測試的指令集',
            '驗證喇叭': '用於驗證喇叭的指令集',
            '出貨指令': '用於出貨測試的指令集'
        }
        
        if section in default_descriptions:
            return default_descriptions[section]
        
        return f'用於{section}的指令集'
