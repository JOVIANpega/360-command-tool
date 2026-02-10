# -*- coding: utf-8 -*-
"""
UI元件模組 - 重構版本
原本超過1300行的檔案已拆分為多個專門模組
此檔案現在主要作為向後相容的入口點，整合所有拆分的元件模組
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import sys
import re
import threading
import time
import json
from datetime import datetime

# 導入拆分後的模組
from ui_parts.ui_components_base import UIComponentsBase
from ui_parts.ui_components_input import UIComponentsInput
from ui_parts.ui_components_output import UIComponentsOutput
from ui_parts.ui_components_settings import UIComponentsSettings
from ui_parts.tooltip import ToolTipManager
from ui_parts.ui_startup_label import StartupLabelManager
from config_utils import get_notification_text, get_app_version


# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)


from config_core import list_com_ports, save_setup, GUIDE_FILE, COMMAND_FILE


class UIComponents(UIComponentsBase, UIComponentsInput, UIComponentsOutput, UIComponentsSettings):
    """
    UI元件類別 - 重構版本
    整合所有拆分的元件模組，保持原有功能完全不變

    繼承順序：
    - UIComponentsBase: 基礎元件和框架
    - UIComponentsInput: 輸入相關元件
    - UIComponentsOutput: 輸出相關元件
    - UIComponentsSettings: 設定相關元件
    """
    def __init__(self, parent, handlers, root, tooltip_manager=None):
        # Call the __init__ of the base class (UIComponentsBase) which sets up the UI structure
        super().__init__(parent)
        self.root = root
        self.handlers = handlers
        self.current_left_row = 0
        


        # 初始化腳本檢視模式標記
        if not hasattr(self.parent, 'script_view_mode'):
            self.parent.script_view_mode = False
        
        # 初始化統一設定管理器
        try:
            from ui_parts.shared_config import get_shared_config
            self.shared_config = get_shared_config()
            print("[DEBUG] UIComponents: 統一設定管理器初始化成功")
        except ImportError as e:
            self.shared_config = None
            print(f"[WARNING] UIComponents: 無法載入統一設定管理器: {e}")
        
        # 初始化 ToolTip 管理器
        if tooltip_manager:
            self.tooltip_manager = tooltip_manager
            print(f"[DEBUG] UIComponents: 使用傳遞進來的 tooltip_manager")
        else:
            try:
                # 使用全域 tooltip 管理器實例
                from ui_parts.tooltip import get_tooltip_manager
                self.tooltip_manager = get_tooltip_manager()
                print(f"[DEBUG] UIComponents: 使用全域 ToolTipManager")
            except Exception as e:
                print(f"[ERROR] UIComponents: 無法獲取全域 ToolTipManager: {e}")
                self.tooltip_manager = None
        
        # 從設定中讀取 ToolTip 啟用狀態，預設為啟用
        if self.tooltip_manager:
            try:
                tooltip_enabled = self.parent.setup.get("UI_Settings", {}).get("ToolTip_Enabled", True)
                self.tooltip_manager.set_all_enabled(tooltip_enabled)
                print(f"[DEBUG] UIComponents: 設定 ToolTip 啟用狀態: {tooltip_enabled}")
            except Exception as e:
                print(f"[ERROR] UIComponents: 設定 ToolTip 啟用狀態失敗: {e}")
        else:
            print("[WARNING] UIComponents: tooltip_manager 不可用")

        # 初始化啟動標籤管理器
        self.startup_label_manager = StartupLabelManager(self)

        # 確保預設設定
        try:
            from config_core import ensure_default_settings
            ensure_default_settings()
            print("[DEBUG] 預設設定確保完成")
        except Exception as e:
            print(f"[ERROR] 確保預設設定失敗: {e}")
        
        # 初始化各個元件
        self.init_com_components()
        self.init_cmd_components()
        self.init_ping_components()
        self.init_settings_components()
        self.init_output_components()
        self.init_progress_components()
        
        # 為所有按鈕添加 ToolTip 提示
        self.init_tooltips()
        
        # 強化 left_panel 內所有 Entry/Combobox 的 <Return> 綁定
        for widget in [self.combobox_cmd, self.entry_timeout, self.combobox_end, self.combobox_com]:
            widget.bind('<Return>', lambda e: self.parent.handlers.on_execute())
        
        # 為所有 IP 輸入框添加 Return 綁定
        if hasattr(self, 'ip_entries'):
            for ip_entry in self.ip_entries:
                ip_entry.bind('<Return>', lambda e: self.parent.handlers.on_execute())
            
        # 恢復 PanedWindow 分割位置（延遲執行，確保視窗已完全載入）
        self.parent.root.after(200, self.restore_pane_position)
        


    def init_com_components(self):
        com_frame = ttk.Frame(self.left_panel, style="TFrame")
        com_frame.grid(row=0, column=0, sticky='ew', pady=3)
        com_frame.columnconfigure(0, weight=0)
        com_frame.columnconfigure(1, weight=1)
        com_frame.columnconfigure(2, weight=0)
        com_frame.columnconfigure(3, weight=0)

        # 定義紅色背景樣式
        try:
            style = ttk.Style()
            style.configure('Red.TCombobox', fieldbackground='#ffcccc', background='#ffcccc')
            style.map('Red.TCombobox', 
                     fieldbackground=[('readonly', '#ffcccc')], 
                     background=[('readonly', '#ffcccc')],
                     selectbackground=[('readonly', '#ffcccc')],
                     selectforeground=[('readonly', 'black')])
        except Exception:
            pass

        # 第一行：COM 口設定
        self.label_com = ttk.Label(com_frame, text='COM口:', style="TLabel")
        self.label_com.grid(row=0, column=0, sticky='w')
        
        # 獲取 COM 口列表
        com_values = list_com_ports()
        
        self.combobox_com = ttk.Combobox(com_frame, values=com_values, state='readonly', width=15, style='Red.TCombobox')
        self.combobox_com.grid(row=0, column=1, padx=5, sticky='ew')
        self.combobox_com.bind("<<ComboboxSelected>>", self.handlers.on_com_port_changed)
        
        # 自動選擇第一個 COM 口 (如果有的話)
        if com_values:
            # 優先使用設定中的 COM 口，如果沒有或無效，則使用第一個
            saved_com = self.parent.setup.get('DUT_Control', {}).get('Serial_COM_Port', '')
            if saved_com and saved_com in com_values:
                self.combobox_com.set(saved_com)
            else:
                self.combobox_com.current(0)
                # 更新設定中的 COM 口
                if 'DUT_Control' not in self.parent.setup:
                    self.parent.setup['DUT_Control'] = {}
                self.parent.setup['DUT_Control']['Serial_COM_Port'] = com_values[0]
                
        refresh_command = None
        if hasattr(self.parent, 'handlers') and hasattr(self.parent.handlers, 'refresh_com_ports'):
            refresh_command = self.parent.handlers.refresh_com_ports
        else:
            refresh_command = lambda: None
            print("[WARNING] handlers 不存在或沒有 refresh_com_ports 方法")
        self.btn_refresh = tk.Button(com_frame, text='刷新', command=refresh_command,
                                   bg='#e0e0e0', fg='black', activebackground='#2196f3', activeforeground='black')
        self.btn_refresh.grid(row=0, column=2, padx=3, sticky='ew')

        # 第二行：指令傳輸方式選擇
        self.label_transport = ttk.Label(com_frame, text='傳輸方式:', style="TLabel")
        self.label_transport.grid(row=1, column=0, sticky='w', pady=(5, 0))

        # 預設使用 Console
        current_mode = 'Console'
        
        # 更新設定檔
        self.parent.setup['Command_Transport_Mode'] = current_mode
            
        self.transport_mode_var = tk.StringVar(value=current_mode)
        self.combobox_transport = ttk.Combobox(com_frame, textvariable=self.transport_mode_var,
                                             values=['Console', 'ADB', 'SSH'], state='readonly', width=15, style='Red.TCombobox')
        self.combobox_transport.grid(row=1, column=1, padx=5, sticky='ew', pady=(5, 0))
        self.combobox_transport.bind("<<ComboboxSelected>>", self.on_transport_mode_changed)

        # 根據傳輸方式設定 COM 口的啟用狀態
        self.update_com_state()

        # 移除 COM 口旁的圓形閃爍功能 - 改用啟動標籤閃爍
        # self.status_canvas = tk.Canvas(com_frame, width=40, height=40, bg='white', highlightthickness=0)
        # self.status_canvas.grid(row=0, column=3, padx=3, sticky='ew')
        # self.status_light = self.status_canvas.create_oval(5, 5, 35, 35, fill='black')
        # self.led_blinking = False

        # 在 COM 組件後添加啟動標籤（僅在 DUT 控制頁面顯示）
        self.init_startup_label()

    def on_com_port_changed(self, event=None):
        """當 COM 口選擇變更時，立即更新顯示但延遲保存"""
        try:
            selected_display_name = self.combobox_com.get()
            if selected_display_name:
                # 從顯示名稱中提取實際的 COM 口名稱
                from config_core import extract_com_port_name
                actual_com_port = extract_com_port_name(selected_display_name)

                print(f"[DEBUG] COM 口已變更為: {actual_com_port} (顯示: {selected_display_name})")

                # 立即更新設定到 parent.setup（用於UI顯示）
                if 'DUT_Control' not in self.parent.setup:
                    self.parent.setup['DUT_Control'] = {}
                self.parent.setup['DUT_Control']['Serial_COM_Port'] = actual_com_port

                # 同步到 SharedConfig 並延遲保存
                if hasattr(self.parent, 'shared_config') and self.parent.shared_config:
                    try:
                        self.parent.shared_config.set_var('dut_com_port', actual_com_port)
                        self.parent.shared_config._schedule_delayed_save()
                    except Exception:
                        pass

                # 顯示通知（顯示完整資訊）
                self.show_notification(f"COM 口已更新為 {selected_display_name}", "blue", 3000)
        except Exception as e:
            print(f"[ERROR] 更新 COM 口設定時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def on_transport_mode_changed(self, event=None):
        """當指令傳輸方式變更時的處理"""
        try:
            selected_mode = self.transport_mode_var.get()
            print(f"[DEBUG] 指令傳輸方式變更為: {selected_mode}")

            # 更新設定檔中的傳輸方式
            if hasattr(self.parent, 'setup'):
                self.parent.setup['Command_Transport_Mode'] = selected_mode
                # 同步到 SharedConfig 並延遲保存
                if hasattr(self.parent, 'shared_config') and self.parent.shared_config:
                    try:
                        self.parent.shared_config.set_var('command_transport_mode', selected_mode)
                        self.parent.shared_config._schedule_delayed_save()
                    except Exception:
                        pass

                # 顯示通知
                self.show_notification(f"指令傳輸方式已更新為 {selected_mode}", "blue", 3000)
            else:
                print("[WARNING] parent.setup 不存在，無法保存指令傳輸方式設定")

            # 更新 COM 口的啟用狀態
            self.update_com_state()

        except Exception as e:
            print(f"[ERROR] 處理指令傳輸方式變更時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def update_com_state(self):
        """根據傳輸方式更新 COM 口的啟用狀態"""
        try:
            current_mode = self.transport_mode_var.get()
            if current_mode == 'ADB':
                # ADB 模式下讓 COM 口可見但顯示為灰色，表示不會被使用
                self.combobox_com.config(state='readonly')  # 保持可讀但不強調
                self.btn_refresh.config(state='normal')     # 保持刷新功能
                self.label_com.config(foreground='gray')    # 灰色表示不會被使用
                print("[DEBUG] ADB 模式：COM 口組件可見但不會被使用")

                # 顯示提示信息
                if hasattr(self, 'show_notification'):
                    self.show_notification("ADB 模式：COM 口僅供參考，不會被使用", "orange", 2000)
            else:
                # Console 模式下啟用 COM 口相關組件
                self.combobox_com.config(state='readonly')
                self.btn_refresh.config(state='normal')
                self.label_com.config(foreground='black')
                print("[DEBUG] Console 模式：COM 口組件已啟用")
        except Exception as e:
            print(f"[ERROR] 更新 COM 口狀態時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def init_startup_label(self):
        """初始化啟動標籤（僅在 DUT 控制頁面顯示）"""
        try:
            # 在 COM 組件下方（row=1）創建啟動標籤
            # 需要調整其他組件的 row 位置
            self.startup_label_manager.create_startup_label(self.left_panel, 1)
            print("[DEBUG] 啟動標籤已初始化")
        except Exception as e:
            print(f"[ERROR] 初始化啟動標籤失敗: {e}")
            import traceback
            traceback.print_exc()

    def init_cmd_components(self):
        # 分類按鈕區域（row=2）
        self.section_frame = ttk.Frame(self.left_panel, style="TFrame")
        self.section_frame.grid(row=2, column=0, sticky='ew', pady=5)
        
        # 建立專用的子容器，用於放置動態生成的分類按鈕/下拉選單
        self.selector_subframe = ttk.Frame(self.section_frame, style="TFrame")
        self.selector_subframe.pack(side='top', fill='x', expand=True)
        
        self.section_var = tk.StringVar()


        # 使用 CommandProcessor 進行統一解析
        if not hasattr(self.handlers, 'command_processor'):
            from ui_parts.command_processor import CommandProcessor
            self.handlers.command_processor = CommandProcessor(self.parent)
        
        print("[DEBUG] 正在初始化指令分類...")
        new_cmds = self.handlers.command_processor.parse_commands_by_section()
        self.parent.commands_by_section = new_cmds
        
        # 獲取區段列表
        self.sections = list(new_cmds.keys())
        if not self.sections:
            self.sections = ['全部指令']

        if self.sections:
            self.section_var.set(self.sections[0])

        # 創建區段選擇器（根據數量自動選擇 Radiobutton 或 Combobox）
        self.create_section_selector(self.sections)

        # 建立描述標籤，放置在 section_frame 底部 (改用 grid 避免與 packed selector_subframe 衝突導致元件消失)
        self.section_description = ttk.Label(self.section_frame, text=self.get_section_description(self.section_var.get()), style="TLabel", wraplength=300)
        self.section_description.pack(side='bottom', anchor='w', pady=(5, 0))

        # 初始指令列與 Ping 組件 (這兩個 gridded to left_panel)
        self.init_cmd_row()
        self.init_ping_components()

    def create_section_selector(self, sections):
        """
        建立區段選擇器
        若區段數量 > 8，使用下拉選單 (Combobox)
        若區段數量 <= 8，使用單選按鈕 (Radiobutton)
        """
        # 確保子容器存在且位置正確
        if not hasattr(self, 'selector_subframe') or not self.selector_subframe.winfo_exists():
            self.selector_subframe = ttk.Frame(self.section_frame, style="TFrame")
            self.selector_subframe.pack(side='top', fill='x', expand=True)
            print("[DEBUG] 已重新建立 selector_subframe")
        else:
            # 只清除子容器的元件
            for widget in self.selector_subframe.winfo_children():
                widget.destroy()
            print(f"[DEBUG] 已清除 selector_subframe 的 {len(self.selector_subframe.winfo_children())} 個子元件")
        
        target = self.selector_subframe
        
        self.sections = sections
        self.section_radiobuttons = []
        self.section_combobox = None
        
        if len(sections) > 8:
            self._create_section_combobox(target)
        else:
            self._create_section_radiobuttons(target)
        
        # 確認按鈕是否正確創建
        print(f"[DEBUG] create_section_selector 完成，selector_subframe 有 {len(self.selector_subframe.winfo_children())} 個子元件")

    def _create_section_combobox(self, parent):
        """建立區段下拉選單"""
        ttk.Label(parent, text="選擇分類: ", font=('Microsoft JhengHei UI', 10)).pack(side='left', padx=(0, 5))
        
        self.section_combobox = ttk.Combobox(
            parent, 
            textvariable=self.section_var, 
            values=self.sections, 
            state='readonly',
            font=('Microsoft JhengHei UI', 10),
            width=20
        )
        self.section_combobox.pack(side='left', fill='x', expand=True)
        self.section_combobox.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_list())
        
        print(f"[DEBUG] 區段數量 ({len(self.sections)}) > 8，已切換至下拉選單模式")

    def _create_section_radiobuttons(self, parent):
        """建立區段單選按鈕"""
        max_buttons_per_row = 4
        
        # 設定 grid 權重
        for i in range(max_buttons_per_row):
            parent.columnconfigure(i, weight=1)

        for i, sec in enumerate(self.sections):
            row, col = i // max_buttons_per_row, i % max_buttons_per_row
            rb = tk.Radiobutton(
                parent, text=sec, variable=self.section_var, value=sec,
                command=self.update_cmd_list, bg='#d9d9d9', fg='black', selectcolor='#d9d9d9',
                activebackground='#2196f3', activeforeground='white', indicatoron=0, relief='flat',
                borderwidth=1, width=8, height=1, font=('Microsoft JhengHei UI', int(self.parent.setup.get('UI_Font_Size', '12')))
            )
            rb.grid(row=row, column=col, padx=1, pady=1, sticky='ew')
            rb.bind("<Enter>", lambda e, b=rb: b.config(bg="#2196f3", fg='white'))
            rb.bind("<Leave>", lambda e, b=rb: self.update_radio_bg())
            self.section_radiobuttons.append(rb)

        self.update_radio_bg()
        print(f"[DEBUG] 區段數量 ({len(self.sections)}) <= 8，使用單選按鈕模式")

    def update_description_position(self):
        """更新描述標籤的位置（確保它在選擇器下方）"""
        pass

    def init_cmd_row(self):
        """初始化指令選擇與執行區域"""
        if hasattr(self, 'cmd_frame') and self.cmd_frame.winfo_exists():
            self.cmd_frame.grid(row=3, column=0, sticky='ew', pady=3)
            return self.cmd_frame

        # 指令下拉選單區域（row=3，避免與分類按鈕重疊）
        self.cmd_frame = ttk.Frame(self.left_panel, style="TFrame")
        self.cmd_frame.grid(row=3, column=0, sticky='ew', pady=3)
        self.cmd_frame.columnconfigure(1, weight=1)
        
        self.label_cmd = ttk.Label(self.cmd_frame, text='指令:', style="TLabel")
        self.label_cmd.grid(row=0, column=0, sticky='w')
        
        # 獲取字體大小
        ui_font_size = int(self.parent.setup.get('DUT_Control', {}).get('UI_Font_Size', self.parent.setup.get('UI_Font_Size', '12')))
        style = ttk.Style()
        style.configure('Custom.TCombobox', font=('Microsoft JhengHei UI', ui_font_size))
        
        self.combobox_cmd = ttk.Combobox(self.cmd_frame, state='readonly', width=25, style='Custom.TCombobox', postcommand=self.update_cmd_list)
        self.combobox_cmd.grid(row=0, column=1, padx=5, sticky='ew')
        self.combobox_cmd.bind("<<ComboboxSelected>>", lambda e: self.on_cmd_selected())
        self.combobox_cmd.bind("<<ComboboxOpened>>", self.limit_dropdown_height)

        # 執行腳本按鈕 (原本在 column 4)
        self.btn_run_script = tk.Button(
            self.cmd_frame, text='執行腳本', font=('Microsoft JhengHei UI', 10),
            bg='#FF9800', fg='white', relief='raised', borderwidth=2, cursor="hand2",
            command=self.parent.handlers.run_script_click, width=10, height=1
        )
        self.btn_run_script.grid(row=0, column=2, sticky='e', padx=(5, 2))

        # 執行指令按鈕 (原本在 column 5)
        self.btn_execute = tk.Button(
            self.cmd_frame, text='執行指令', font=('Microsoft JhengHei UI', 14, 'bold'),
            bg='#4CAF50', fg='white', relief='raised', borderwidth=2, cursor="hand2",
            command=self.parent.handlers.on_execute, width=12, height=2
        )
        self.btn_execute.grid(row=0, column=3, sticky='e', padx=(5, 5))
        self.btn_execute.bind("<Enter>", self.on_enter_exec)
        self.btn_execute.bind("<Leave>", self.on_leave_exec)

        # 指令內容顯示標籤（放在指令下拉選單下方）
        self.cmd_content_label = ttk.Label(
            self.cmd_frame, 
            text='', 
            style="TLabel", 
            wraplength=500,
            foreground='#666666'
        )
        self.cmd_content_label.grid(row=1, column=0, columnspan=4, sticky='w', padx=5, pady=(2, 0))

        self.combobox_cmd.bind('<Return>', lambda event: self.parent.handlers.on_execute())
        
        return self.cmd_frame

    def on_enter_exec(self, event):
        self.btn_execute.config(bg='#2196F3')

    def on_leave_exec(self, event):
        self.btn_execute.config(bg='#4CAF50')



    def on_open_command_script(self):
        """打開指令腳本文件編輯器視窗"""
        try:
            # 獲取指令檔案路徑
            command_file_path = self.parent.setup.get("DUT_Control", {}).get("Command_File_Path", "")

            if not command_file_path:
                # 如果沒有設定路徑，使用預設路徑
                from config_core import COMMAND_FILE
                command_file_path = COMMAND_FILE

            # 檢查檔案是否存在
            if not os.path.exists(command_file_path):
                self.show_notification(f"指令檔案不存在: {command_file_path}", "error", 5000)
                return

            # 創建編輯器視窗
            self.create_command_editor_window(command_file_path)
            
        except Exception as e:
            print(f"[ERROR] 打開指令腳本時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            self.show_notification(f"打開指令腳本失敗: {str(e)}", "error", 5000)
    
    def create_command_editor_window(self, file_path):
        """創建指令檔案編輯器視窗"""
        # 檢查是否已經開啟編輯器視窗
        if hasattr(self, 'editor_window') and self.editor_window and self.editor_window.winfo_exists():
            self.editor_window.lift()  # 將視窗提到前面
            return
        
        # 創建新視窗
        self.editor_window = tk.Toplevel(self.parent.root)
        self.editor_window.title(f"指令檔案編輯器 - {os.path.basename(file_path)}")
        self.editor_window.geometry("800x600")
        
        # 創建主框架
        main_frame = ttk.Frame(self.editor_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 頂部資訊框架
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"檔案路徑: {file_path}", font=('Microsoft JhengHei UI', 10, 'bold')).pack(anchor='w')
        
        # 文字編輯區域
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 創建帶滾動條的文字編輯器
        self.editor_text = tk.Text(
            text_frame,
            wrap=tk.NONE,
            font=('Consolas', 11),
            undo=True,
            maxundo=50
        )
        
        # 垂直滾動條
        v_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.editor_text.yview)
        self.editor_text.configure(yscrollcommand=v_scrollbar.set)
        
        # 水平滾動條
        h_scrollbar = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.editor_text.xview)
        self.editor_text.configure(xscrollcommand=h_scrollbar.set)
        
        # 排列組件
        self.editor_text.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        # 按鈕框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 儲存按鈕
        save_button = ttk.Button(
            button_frame,
            text="💾 儲存檔案",
            command=lambda: self.save_command_file(file_path)
        )
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 重新載入按鈕
        reload_button = ttk.Button(
            button_frame,
            text="🔄 重新載入",
            command=lambda: self.reload_command_file(file_path)
        )
        reload_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 關閉按鈕
        close_button = ttk.Button(
            button_frame,
            text="❌ 關閉",
            command=self.editor_window.destroy
        )
        close_button.pack(side=tk.RIGHT)
        
        # 載入檔案內容
        self.reload_command_file(file_path)
        
        # 設定快捷鍵
        self.editor_window.bind('<Control-s>', lambda e: self.save_command_file(file_path))
        
        # 顯示通知
        self.show_notification(f"已開啟指令檔案編輯器", "success")
    
    def reload_command_file(self, file_path):
        """重新載入指令檔案內容"""
        try:
            # 讀取檔案內容
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # 如果 UTF-8 解碼失敗，嘗試其他編碼
                try:
                    with open(file_path, 'r', encoding='big5') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='gbk') as f:
                        content = f.read()
            
            # 清空並插入內容
            self.editor_text.delete(1.0, tk.END)
            self.editor_text.insert(1.0, content)
            
            # 移動游標到開始位置
            self.editor_text.mark_set(tk.INSERT, 1.0)
            self.editor_text.see(1.0)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"載入檔案失敗：{str(e)}")

    def update_startup_label(self, new_text):
        """更新啟動標籤文字"""
        if hasattr(self, 'startup_label_manager'):
            self.startup_label_manager.update_label_text(new_text)

    def update_device_label(self, new_text):
        """更新設備標籤文字"""
        if hasattr(self, 'device_label'):
            # 限制最多顯示100個字元
            if len(new_text) > 100:
                new_text = new_text[:100]
            self.device_label.config(text=new_text)
            print(f"[DEBUG] 設備標籤已更新: {new_text}")

    def refresh_commands_fully(self):
        """徹底重新載入指令與分類區段"""
        try:
            print("[DEBUG] 正在徹底重新載入指令文件與分類...")
            # 1. 重新解析所有指令與區段
            if hasattr(self.handlers, 'command_processor'):
                new_cmds = self.handlers.command_processor.parse_commands_by_section()
            else:
                from ui_parts.command_processor import CommandProcessor
                self.handlers.command_processor = CommandProcessor(self.handlers)
                new_cmds = self.handlers.command_processor.parse_commands_by_section()
                
            if not new_cmds:
                self.show_notification("無法解析指令文件或文件不存在", "error")
                return

            self.parent.commands_by_section = new_cmds
            
            # 2. 獲取新的區段列表
            new_sections = list(new_cmds.keys())
            if not new_sections:
                new_sections = ['全部指令']
            
            # 3. 重新建立區段選擇器 (Radiobuttons 或 Combobox)
            current_section = self.section_var.get()
            print(f"[DEBUG] 準備重新建立區段選擇器，當前分類: {current_section}, 新分類列表: {new_sections}")
            self.create_section_selector(new_sections)
            print(f"[DEBUG] 區段選擇器重建完成")
            
            # 如果之前的區段還在，恢復它，否則選第一個
            if current_section in new_sections:
                self.section_var.set(current_section)
            else:
                self.section_var.set(new_sections[0])
            
            # 4. 更新指令下拉選單內容 (此方法內部也會呼叫 parse_commands_by_section)
            self.update_cmd_list()
            
            # 5. 強制確保各個容器依然在 grid 中 (防止因為佈局刷新導致元件縮小或隱藏)
            if hasattr(self, 'section_frame') and self.section_frame.winfo_exists():
                self.section_frame.grid(row=2, column=0, sticky='ew', pady=5)
                # 確保描述標籤位置正常（selector_subframe 已在 create_section_selector 中正確設置，不需要重複 pack）
                if hasattr(self, 'section_description') and self.section_description.winfo_exists():
                    self.section_description.pack(side='bottom', anchor='w', pady=(5, 0))
            
            self.init_cmd_row()
            if hasattr(self, 'init_ping_components'):
                self.init_ping_components()

            # 強制更新 UI 並重繪
            self.parent.root.update_idletasks()
            
            # 獲取實際讀取的檔名用於提示
            try:
                actual_path = self.handlers.command_processor.get_last_read_path()
                filename = os.path.basename(actual_path)
            except:
                filename = "command.txt"

            total_cmds = len(new_cmds.get('全部指令', {}))
            self.show_notification(f"✅ 指令已刷新！自 {filename} 載入 {total_cmds} 個指令", "green", 5000)
            print(f"[DEBUG] 徹底刷新完成: {filename}, 共 {total_cmds} 個指令")
            
            # 強制 UI 刷新畫面
            self.parent.root.update_idletasks()
            
        except Exception as e:
            print(f"[ERROR] 徹底刷新指令時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def save_command_file(self, file_path):
        """儲存指令檔案"""
        try:
            # 獲取編輯器內容
            content = self.editor_text.get(1.0, tk.END)
            
            # 移除最後的換行符（Text widget會自動添加）
            if content.endswith('\n'):
                content = content[:-1]
            
            # 儲存到檔案
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 重新載入指令按鈕（如果需要的話）
            if hasattr(self.parent, 'update_dut_buttons'):
                self.parent.update_dut_buttons()
            
            self.show_notification("檔案已儲存並重新載入指令按鈕", "success")
            messagebox.showinfo("成功", "檔案已成功儲存！")
            
        except Exception as e:
            error_msg = f"儲存檔案失敗：{str(e)}"
            self.show_notification(error_msg, "error")
            messagebox.showerror("錯誤", error_msg)





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
        
    def init_ping_components(self):
        """初始化 Ping 組件 - 使用下拉選單的 IP 管理功能"""
        ping_frame = ttk.Frame(self.left_panel, style="TFrame")
        ping_frame.grid(row=4, column=0, sticky='ew', pady=3)
        ping_frame.columnconfigure(0, weight=0)  # 標籤不需要擴展
        ping_frame.columnconfigure(1, weight=1)  # 下拉選單擴展
        ping_frame.columnconfigure(2, weight=0)  # 新增按鈕不需要擴展
        ping_frame.columnconfigure(3, weight=0)  # Ping 按鈕不需要擴展
        
        # IP 位址標籤
        self.label_ip = ttk.Label(ping_frame, text='IP位址:', style="TLabel")
        self.label_ip.grid(row=0, column=0, sticky='w')
        
        # IP 下拉選單
        self.ip_combobox = ttk.Combobox(ping_frame, width=20, state='readonly')
        self.ip_combobox.grid(row=0, column=1, sticky='ew', padx=5)
        self.ip_combobox.bind('<<ComboboxSelected>>', self.on_ip_selected)
        # 與舊代碼相容：提供 entry_ip 別名供 handlers 使用
        self.entry_ip = self.ip_combobox
        
        # 變更即保存：選擇或按 Enter 時立即寫入 Default_IP_Address 與歷史
        try:
            self.ip_combobox.bind('<<ComboboxSelected>>', lambda e: self.on_ip_changed())
            self.ip_combobox.bind('<Return>', lambda e: self.on_ip_changed())
            self.ip_combobox.bind('<FocusOut>', lambda e: self.on_ip_changed())
        except Exception:
            pass

        # 新增 IP 按鈕（重新啟用以供用戶手動輸入）
        self.btn_add_ip = tk.Button(ping_frame, text='+', command=self.add_new_ip, 
                                   width=2, bg='#90EE90', fg='black')
        self.btn_add_ip.grid(row=0, column=2, padx=2)
        
        # Ping 按鈕
        self.btn_ping = tk.Button(ping_frame, text='Ping', command=self.parent.handlers.on_ping, 
                                 width=6, bg='#87CEEB', fg='black')
        self.btn_ping.grid(row=0, column=3, padx=2)
        
        # 載入 IP 歷史記錄
        self.load_ip_history()
    
    def load_ip_history(self):
        """載入 IP 歷史記錄到下拉選單（從檔案讀取最新設定）"""
        try:
            from config_core import load_setup
            setup = load_setup()
            dut = setup.get('DUT_Control', {})
            ip_history = dut.get('IP_History', [])
            
            print(f"[DEBUG] 載入 IP 歷史記錄時發現 {len(ip_history)} 個 IP")
            
            # 更新下拉選單的值
            if ip_history:
                self.ip_combobox['values'] = ip_history
                # 優先選擇 Default_IP_Address，否則選第一個
                default_ip = dut.get('Default_IP_Address')
                if default_ip and default_ip in ip_history:
                    self.ip_combobox.set(default_ip)
                    print(f"[DEBUG] 已選擇預設 IP: {default_ip}")
                else:
                    self.ip_combobox.set(ip_history[0])
                    print(f"[DEBUG] 已選擇第一個 IP: {ip_history[0]}")
            else:
                # 如果沒有歷史記錄，設定預設值
                default_ip = dut.get('Default_IP_Address', '192.168.11.143')
                self.ip_combobox['values'] = [default_ip]
                self.ip_combobox.set(default_ip)
                print(f"[DEBUG] 使用預設 IP: {default_ip}")
                    
        except Exception as e:
            print(f"[DEBUG] 載入 IP 歷史記錄時發生錯誤: {e}")
    
    def on_ip_changed(self):
        """當下拉選擇或按 Enter 後，立即保存 IP 與歷史"""
        try:
            current_ip = (self.ip_combobox.get() or '').strip()
            if not current_ip:
                return
            # 驗證基本格式（僅 IPv4，若需支援 FQDN 可放寬）
            ip_only = current_ip.split(':')[0].strip()
            # 非嚴格檢查：即使格式不完全符合，也先做保存
            from config_core import load_setup, save_setup, resource_manager
            from core.config_manager import get_config_manager
            setup = load_setup()
            # 強制重載避免快取導致看不到更新
            try:
                resource_manager.invalidate_cache()
            except Exception:
                pass
            dut = setup.setdefault('DUT_Control', {})
            # 更新歷史（去重、置頂、最多5筆）
            history = list(dut.get('IP_History', []))
            history = [h for h in history if h != current_ip]
            history.insert(0, current_ip)
            if len(history) > 5:
                history = history[:5]
            dut['IP_History'] = history
            # 更新預設 IP
            dut['Default_IP_Address'] = current_ip
            # 透過 ConfigManager 直接保存，確保寫到正確路徑
            try:
                cfg_mgr = get_config_manager()
                cfg = cfg_mgr.load_config(force_reload=True)
                cfg['DUT_Control'] = dut
                cfg_mgr.save_config(cfg, manual_save=True)
            except Exception:
                # 後備方案
                save_setup(setup, manual_save=True)
            # 同步下拉值
            self.ip_combobox['values'] = history if history else [current_ip]
            self.ip_combobox.set(current_ip)
            print(f"[INFO] 已保存 Default_IP_Address 與 IP_History: {current_ip}")
            try:
                cfg_path = resource_manager.get_resource_path('setup.json')
                print(f"[INFO] 設定檔寫入路徑: {cfg_path}")
            except Exception:
                pass
        except Exception as e:
            print(f"[ERROR] 保存 IP 時發生錯誤: {e}")

    def add_new_ip(self):
        """新增新的 IP 地址"""
        try:
            # 創建輸入對話框
            from tkinter import simpledialog
            new_ip = simpledialog.askstring("新增 IP", "請輸入新的 IP 地址:")
            
            if new_ip and new_ip.strip():
                new_ip = new_ip.strip()
                
                # 驗證 IP 格式
                if not self.is_valid_ip(new_ip):
                    messagebox.showerror("錯誤", "IP 地址格式不正確")
                    return
                
                # 載入當前設定
                from config_core import load_setup, save_setup
                setup = load_setup()
                
                # 取得現有的 IP 歷史記錄
                ip_history = setup.get('DUT_Control', {}).get('IP_History', [])
                
                # 如果 IP 不在歷史記錄中，則新增
                if new_ip not in ip_history:
                    ip_history.insert(0, new_ip)
                    # 限制歷史記錄數量（最多保留 20 個）
                    if len(ip_history) > 20:
                        ip_history = ip_history[:20]
                    
                    # 保存設定
                    setup['DUT_Control']['IP_History'] = ip_history
                    save_setup(setup, manual_save=True)
                    
                    # 更新下拉選單並選中新增項，且更新 Default_IP_Address
                    self.load_ip_history()
                    try:
                        self.ip_combobox.set(new_ip)
                    except Exception:
                        pass
                    try:
                        # 同步更新 Default_IP_Address
                        setup['DUT_Control']['Default_IP_Address'] = new_ip
                        save_setup(setup, manual_save=True)
                    except Exception:
                        pass
                    
                    messagebox.showinfo("成功", f"IP 地址已新增: {new_ip}")
                    print(f"[INFO] IP 地址已新增: {new_ip}")
                else:
                    messagebox.showinfo("提示", f"IP 地址已存在: {new_ip}")
                    
        except Exception as e:
            print(f"[ERROR] 新增 IP 地址時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"新增 IP 地址失敗: {e}")
    
    def is_valid_ip(self, ip_address):
        """驗證 IP 地址格式"""
        try:
            parts = ip_address.split('.')
            if len(parts) != 4:
                return False
            
            for part in parts:
                if not part.isdigit():
                    return False
                num = int(part)
                if num < 0 or num > 255:
                    return False
            
            return True
        except:
            return False
    
    def on_ip_selected(self, event=None):
        """當選擇 IP 時的回調函數"""
        selected_ip = self.ip_combobox.get()
        if selected_ip:
            print(f"[DEBUG] 已選擇 IP: {selected_ip}")
    

    

    
    def on_ping(self):
        """執行 Ping 操作"""
        current_ip = self.ip_combobox.get()
        if not current_ip:
            messagebox.showwarning("警告", "請先選擇一個 IP 地址")
            return
        
        # 執行 ping 操作
        try:
            import subprocess
            import platform
            
            # 根據作業系統選擇 ping 命令
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "1", current_ip]
            else:
                cmd = ["ping", "-c", "1", current_ip]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                messagebox.showinfo("Ping 結果", f"IP {current_ip} 可以連通")
            else:
                messagebox.showwarning("Ping 結果", f"IP {current_ip} 無法連通")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"Ping 操作失敗: {e}")

    def init_settings_components(self):
        settings_frame = ttk.LabelFrame(self.left_panel, text='設定', padding=5, style="TLabelframe")
        settings_frame.grid(row=6, column=0, sticky='ew', pady=5)  # 調整 row 位置
        
        # 第一行：結束字串設定
        end_frame = ttk.Frame(settings_frame, style="TFrame")
        end_frame.grid(row=0, column=0, sticky='ew', pady=2)
        end_frame.columnconfigure(1, weight=1)  # 讓下拉選單可擴展
        
        self.label_end = ttk.Label(end_frame, text='結束字串:', style="TLabel")
        self.label_end.grid(row=0, column=0, sticky='w')
        
        # 使用StringVar來追蹤結束字串變化
        self.end_string_var = tk.StringVar()
        default_end = self.parent.setup.get('Command_End_String', 'root')
        self.end_string_var.set(default_end)
        
        # 綁定變化事件進行即時保存
        self.end_string_var.trace_add("write", self.on_end_string_changed)
        
        self.combobox_end = ttk.Combobox(end_frame, textvariable=self.end_string_var, width=15)
        self.combobox_end.grid(row=0, column=1, padx=(5, 4), sticky='ew')
        self.update_end_strings()
        
        # +/- 按鈕組合 - 與輸入框適當間距
        self.btn_add_end = tk.Button(end_frame, text='+', command=self.on_add_end_string, width=2, bg='#ccffcc', fg='black')
        self.btn_add_end.grid(row=0, column=2, padx=(0, 3))
        
        self.btn_remove_end = tk.Button(end_frame, text='-', command=self.on_remove_end_string, width=2, bg='#ffcccc', fg='black')
        self.btn_remove_end.grid(row=0, column=3, padx=0)
        
        # 第二行：超時設定
        timeout_frame = ttk.Frame(settings_frame, style="TFrame")
        timeout_frame.grid(row=1, column=0, sticky='ew', pady=2)
        self.label_timeout = ttk.Label(timeout_frame, text='超時(秒):', style="TLabel")
        self.label_timeout.grid(row=0, column=0, sticky='w')
        self.entry_timeout = ttk.Entry(timeout_frame, width=8)
        self.entry_timeout.grid(row=0, column=1, padx=5, sticky='ew')
        self.entry_timeout.insert(0, self.parent.setup.get('Command_Timeout_Seconds', '30'))
        
        # 第三行：字體大小設定
        font_frame = ttk.Frame(settings_frame, style="TFrame")
        font_frame.grid(row=2, column=0, sticky='ew', pady=2)
        font_frame.columnconfigure(1, weight=1)
        font_frame.columnconfigure(3, weight=1)
        
        # UI字體大小設定
        self.label_ui_font = ttk.Label(font_frame, text='介面字體:', style="TLabel")
        self.label_ui_font.grid(row=0, column=0, sticky='w', padx=(0,2))
        
        font_controls_frame = ttk.Frame(font_frame, style="TFrame")
        font_controls_frame.grid(row=0, column=1, sticky='ew')
        
        self.btn_ui_font_minus = tk.Button(font_controls_frame, text='－', width=2, command=lambda: self.ui_font_scale.set(self.ui_font_scale.get()-1))
        self.btn_ui_font_minus.grid(row=0, column=0, padx=1)
        
        self.ui_font_scale = tk.Scale(font_controls_frame, from_=8, to=20, orient='horizontal', 
                                    command=self.parent.handlers.change_ui_font_size, length=80, bg='white', fg='black', 
                                    highlightthickness=0)
        self.ui_font_scale.grid(row=0, column=1, padx=1)
        self.ui_font_scale.set(int(self.parent.setup.get('UI_Font_Size', '12')))
        
        self.btn_ui_font_plus = tk.Button(font_controls_frame, text='＋', width=2, command=lambda: self.ui_font_scale.set(self.ui_font_scale.get()+1))
        self.btn_ui_font_plus.grid(row=0, column=2, padx=1)
        
        # 內容字體大小設定
        self.label_content_font = ttk.Label(font_frame, text='內容字體:', style="TLabel")
        self.label_content_font.grid(row=0, column=2, sticky='w', padx=(10,2))
        
        content_font_controls_frame = ttk.Frame(font_frame, style="TFrame")
        content_font_controls_frame.grid(row=0, column=3, sticky='ew')
        
        self.btn_content_font_minus = tk.Button(content_font_controls_frame, text='－', width=2, 
                                              command=lambda: self.content_font_scale.set(self.content_font_scale.get()-1))
        self.btn_content_font_minus.grid(row=0, column=0, padx=1)
        
        self.content_font_scale = tk.Scale(content_font_controls_frame, from_=8, to=20, orient='horizontal', 
                                         command=self.parent.handlers.change_content_font_size, length=80, bg='white', fg='black', 
                                         highlightthickness=0)
        self.content_font_scale.grid(row=0, column=1, padx=1)
        self.content_font_scale.set(int(self.parent.setup.get('Content_Font_Size', '12')))
        
        self.btn_content_font_plus = tk.Button(content_font_controls_frame, text='＋', width=2, 
                                             command=lambda: self.content_font_scale.set(self.content_font_scale.get()+1))
        self.btn_content_font_plus.grid(row=0, column=2, padx=1)
        
        # 第四行：功能按鈕區 - 獨立區域，與設定區分開
        btn_frame = ttk.Frame(settings_frame, style="TFrame")
        btn_frame.grid(row=3, column=0, sticky='ew', pady=(5, 2))  # 上方間距大一些，分隔設定和按鈕
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)
        btn_frame.columnconfigure(3, weight=1)
        
        self.btn_clear = ttk.Button(btn_frame, text='清空回應', command=self.parent.handlers.clear_output, style='Blue.TButton')
        self.btn_clear.grid(row=0, column=0, padx=2, sticky='ew')
        
        self.btn_backup = ttk.Button(btn_frame, text='備份Log', command=self.parent.handlers.backup_output, style='Blue.TButton')
        self.btn_backup.grid(row=0, column=1, padx=2, sticky='ew')
        
        self.btn_guide = ttk.Button(btn_frame, text='使用說明', command=self.parent.handlers.toggle_guide, style='Blue.TButton')
        self.btn_guide.grid(row=0, column=2, padx=2, sticky='ew')

        self.btn_open_script = ttk.Button(btn_frame, text='open CMD table', command=self.on_open_command_script, style='Orange.TButton')
        self.btn_open_script.grid(row=0, column=3, padx=2, sticky='ew')
        
        # 設備標籤顯示區域 - 放在按鈕區下方
        device_label_frame = ttk.Frame(self.left_panel, style="TFrame")
        device_label_frame.grid(row=7, column=0, sticky='ew', pady=5)
        device_label_frame.columnconfigure(0, weight=1)
        
        # 從設定檔讀取設備標籤文字，預設顯示設備信息
        device_label_text = self.parent.setup.get('Device_Label', 'MU310 : root/oelinux123')
        # 限制最多顯示100個字元
        if len(device_label_text) > 100:
            device_label_text = device_label_text[:100]
        
        self.device_label = ttk.Label(
            device_label_frame, 
            text=device_label_text,
            style="TLabel",
            font=('Microsoft JhengHei UI', int(self.parent.setup.get('UI_Font_Size', '12'))),
            foreground='#333333',
            background='#FFFACD',  # 淡黃色背景
            wraplength=300,  # 自動換行
            justify='left'
        )
        self.device_label.grid(row=0, column=0, sticky='ew', padx=5, pady=2)
        
        # 將 ui_font_scale 的 command 綁定為 handlers.change_ui_font_size，避免 lambda 導致無法正確更新
        self.ui_font_scale.config(command=self.parent.handlers.change_ui_font_size)

    def init_output_components(self):
        try:
            # 建立輸出區域
            self.text_output = scrolledtext.ScrolledText(
                self.right_panel,
                wrap=tk.WORD,
                width=50,
                height=20,
                font=('Microsoft JhengHei UI', int(self.parent.setup.get('Content_Font_Size', '12')))
            )
            self.text_output.grid(row=0, column=0, sticky='nsew')
            self.right_panel.grid_rowconfigure(0, weight=1)
            self.right_panel.grid_columnconfigure(0, weight=1)
            
            # 設定 tag
            self.text_output.tag_configure("send", foreground="blue")
            self.text_output.tag_configure("end", foreground="green")  # 收到結束字串為綠色
            self.text_output.tag_configure("timeout", foreground="red")  # 超時為紅色
            self.text_output.tag_configure("purple", foreground="#800080")  # 紫色
            self.text_output.tag_configure("guide_title", foreground="#006400", font=('Microsoft JhengHei UI', int(self.parent.setup.get('Content_Font_Size', '12')) + 2, 'bold'))  # 使用說明標題
            self.text_output.tag_configure("error", foreground="red")  # 錯誤訊息為紅色
            self.text_output.tag_configure("success", foreground="green")  # 成功訊息為綠色
            self.text_output.tag_configure("warning", foreground="orange")  # 警告訊息為橙色
            
            # 為高亮關鍵字定義標籤
            print(f"[DEBUG] 初始化關鍵字高亮標籤，parent={self.parent}")
            if hasattr(self.parent, 'highlight_keywords'):
                print(f"[DEBUG] highlight_keywords={self.parent.highlight_keywords}")
                for keyword, color in self.parent.highlight_keywords.items():
                    print(f"[DEBUG] 創建關鍵字標籤: {keyword} -> {color}")
                    self.text_output.tag_configure(color, foreground=color)
            else:
                print(f"[WARNING] parent 沒有 highlight_keywords 屬性")
            
            # 設定唯讀
            self.text_output.config(state='disabled')
            
            # 添加右鍵菜單
            self.output_context_menu = tk.Menu(self.text_output, tearoff=0)
            self.output_context_menu.add_command(label="複製", command=self.copy_selected_text)
            self.output_context_menu.add_command(label="全選", command=self.select_all_text)
            self.output_context_menu.add_separator()
            self.output_context_menu.add_command(label="清空", command=self.parent.handlers.clear_output)
            self.text_output.bind("<Button-3>", self.show_output_context_menu)
            
        except Exception as e:
            print(f"Error in init_output_components: {e}")
            import traceback
            traceback.print_exc()
            raise

    def init_exec_button_left_panel(self):
        # This method is now empty as the button has been moved.
        pass

    def init_script_execution_feature(self, parent_frame):
        """初始化腳本執行功能按鈕"""
        try:
            # 創建一個框架來容納按鈕
            script_frame = ttk.Frame(parent_frame)
            script_frame.pack(side="left", padx=5)
            
            # 創建執行腳本按鈕
            self.btn_run_script = ttk.Button(
                script_frame,
                text="執行腳本",
                command=self.parent.handlers.run_script_file,
                width=10
            )
            self.btn_run_script.pack(side="left")
            
            # 添加 Tooltip
            if hasattr(self, 'tooltip_manager') and self.tooltip_manager:
                self.tooltip_manager.add_tooltip_with_text(self.btn_run_script, "載入並逐行執行腳本檔案 (.txt)")
                
        except Exception as e:
            print(f"[ERROR] 初始化腳本執行功能時發生錯誤: {e}")

    def init_progress_components(self):
        """初始化進度條組件"""
        self.progress = ttk.Progressbar(
            self.right_panel,
            mode='determinate',
            style="gray.Horizontal.TProgressbar",
            length=200
        )
        self.progress.grid(row=1, column=0, sticky='ew', pady=5)
        self.progress['value'] = 0
        # 確保進度條始終顯示
        self.progress.grid_remove()  # 初始隱藏
        self.right_panel.rowconfigure(1, weight=0)  # 進度條行不擴展

    def show_progress(self, show=True):
        """控制進度條顯示/隱藏"""
        print(f"[DEBUG] show_progress: show={show}")
        if show:
            self.progress.grid()
        else:
            self.progress.grid_remove()

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

    def _reload_commands_and_setup(self):
        """重新載入設定和指令 - 重構輔助函數"""
        print("[DEBUG] update_cmd_list: 重新解析指令文件")

        # 強制重新載入設定，確保獲取最新的指令檔路徑
        self.parent.setup = self.parent.config.load_setup()
        self.parent.handlers.reload_setup(self.parent.setup)

        # 解析指令文件
        self.parent.commands_by_section = self.parent.handlers.parse_commands_by_section()

    def _check_and_update_sections(self):
        """檢查並更新分類按鈕 - 重構輔助函數"""
        # 檢查是否需要重新生成分類按鈕
        available_sections = list(self.parent.commands_by_section.keys())
        current_sections = getattr(self, 'sections', [])

        print(f"[DEBUG] update_cmd_list: 當前分類按鈕: {current_sections}")
        print(f"[DEBUG] update_cmd_list: 檔案中的分類: {available_sections}")

        # 如果分類有變化，重新生成分類按鈕
        if set(current_sections) != set(available_sections):
            print("[DEBUG] update_cmd_list: 分類有變化，重新生成分類按鈕")
            self.regenerate_section_buttons(available_sections)

    def _validate_and_set_section(self):
        """驗證並設定當前分類 - 重構輔助函數"""
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

        return section

    def _update_command_dropdown(self, section):
        """更新指令下拉選單 - 重構輔助函數"""
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

    def update_cmd_list(self):
        """更新指令下拉選單的選項 - 重構版本

        此方法會重新解析指令文件，並根據當前選擇的分類更新下拉選單的選項。
        當設定中的指令檔路徑變更時，此方法會被調用以重新載入指令。
        """
        # 重新載入設定和指令
        self._reload_commands_and_setup()

        # 檢查並更新分類按鈕
        self._check_and_update_sections()

        # 驗證並設定當前分類
        section = self._validate_and_set_section()

        # 更新按鈕背景和說明文字
        self.update_radio_bg()
        self.section_description.config(text=self.get_section_description(section))

        # 更新指令下拉選單
        self._update_command_dropdown(section)

    def regenerate_section_buttons(self, new_sections):
        """重新生成分類按鈕"""
        try:
            print(f"[DEBUG] regenerate_section_buttons: 重新生成分類按鈕，新分類: {new_sections}")
            
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
            
            # 使用 create_section_selector 重新創建選擇器（避免 pack/grid 混用）
            self.create_section_selector(new_sections)
            
            # 更新按鈕背景色
            self.update_radio_bg()
            
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

    def flush_buffer(self):
        """將緩衝區的文字一次性添加到輸出區域"""
        if not hasattr(self.parent, 'text_buffer') or not self.parent.text_buffer:
            return
            
        if not hasattr(self, 'text_output'):
            print("[ERROR] text_output 不存在，無法刷新緩衝區")
            return
            
        try:
            self.text_output.configure(state='normal')
            for text, tag in self.parent.text_buffer:
                if tag:
                    self.text_output.insert(tk.END, text, tag)
                else:
                    self.text_output.insert(tk.END, text)
            self.text_output.see(tk.END)  # 自動捲到最底
            self.text_output.configure(state='disabled')  # 設回唯讀狀態
            self.parent.text_buffer = []
        except Exception as e:
            print(f"[ERROR] 刷新緩衝區時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

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
            
            # 更新設備標籤字體
            if hasattr(self, 'device_label'):
                widgets.append(self.device_label)
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
                          self.entry_timeout]:
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
            for widget in [self.combobox_com, self.combobox_cmd, self.combobox_end, self.entry_timeout]:
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

                # 延遲保存，避免頻繁寫入
                if hasattr(self, '_resize_timer'):
                    self.parent.root.after_cancel(self._resize_timer)
                self._resize_timer = self.parent.root.after(2000, self._delayed_save_window_size, w, h)
        # 不再自動縮放字體

    def _delayed_save_window_size(self, w, h):
        """延遲保存視窗大小"""
        try:
            from config_core import load_setup, save_setup
            full_setup = load_setup()
            full_setup['DUT_Control'].update({
                'Window_Width': str(w),
                'Window_Height': str(h)
            })
            save_setup(full_setup)
            print(f"[DEBUG] 視窗大小已保存: {w}x{h}")
        except Exception as e:
            print(f"[ERROR] 保存視窗大小時發生錯誤: {e}")

    # 移除 LED 閃爍功能 - 改用啟動標籤閃爍
    # def start_led_blink(self):
    #     self.led_blinking = True
    #     self._blink_led()

    # def _blink_led(self):
    #     if not self.led_blinking:
    #         return
    #     current_color = self.status_canvas.itemcget(self.status_light, 'fill')
    #     next_color = 'lime' if current_color == 'red' else 'red'
    #     self.status_canvas.itemconfig(self.status_light, fill=next_color)
    #     self.status_canvas.after(300, self._blink_led)

    # def stop_led_blink(self):
    #     self.led_blinking = False
    #     # 恢復為黑色，表示待命狀態
    #     self.status_canvas.itemconfig(self.status_light, fill='black')

    def on_pane_drag_start(self, event):
        self.main_frame.start_x = event.x
        self.main_frame.start_y = event.y

    def on_pane_drag_end(self, event):
        dx = event.x - self.main_frame.start_x
        dy = event.y - self.main_frame.start_y
        self.main_frame.move(dx, dy)

    # 移除重複的PanedWindow事件處理，使用基類的實現

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

    # 移除自動執行相關方法 - 功能已不需要

    # 指保留原本的 show_notification，不重複 override

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
            
            # 更新指令內容標籤（在指令下拉選單下方）
            if hasattr(self, 'cmd_content_label'):
                self.cmd_content_label.config(text=f"指令內容: {cmd}")
                print(f"[DEBUG] 更新指令內容顯示: {cmd}")
            
            # 如果是特殊指令，顯示提示
            if cmd.startswith("DELAY:"):
                delay_time = cmd.split(":")[1]
                self.show_notification(get_notification_text("delay_cmd", delay_time), "purple", 3000)
            elif cmd.startswith("SHOW:"):
                message = cmd.split(":")[1]
                self.show_notification(get_notification_text("show_msg", message), "green", 3000)



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









    def init_tooltips(self):
        """為所有按鈕添加 ToolTip 提示說明"""
        if not hasattr(self, 'tooltip_manager') or not self.tooltip_manager:
            print("[WARNING] init_tooltips: tooltip_manager 不可用，跳過 tooltip 初始化")
            return
            
        print(f"[DEBUG] init_tooltips: 開始初始化 tooltips，使用 tooltip_manager")
        
        try:
            # 執行指令按鈕
            if hasattr(self, 'btn_execute'):
                self.tooltip_manager.add_tooltip(self.btn_execute, "btn_execute")
            
            # 清空回應按鈕
            if hasattr(self, 'btn_clear'):
                self.tooltip_manager.add_tooltip(self.btn_clear, "btn_clear")
            
            # 備份Log按鈕
            if hasattr(self, 'btn_backup'):
                self.tooltip_manager.add_tooltip(self.btn_backup, "btn_backup")
            
            # 使用說明按鈕
            if hasattr(self, 'btn_guide'):
                self.tooltip_manager.add_tooltip(self.btn_guide, "btn_guide")
            
            # 刷新按鈕
            if hasattr(self, 'btn_refresh'):
                self.tooltip_manager.add_tooltip(self.btn_refresh, "btn_refresh")
            
            # Ping按鈕
            if hasattr(self, 'btn_ping'):
                self.tooltip_manager.add_tooltip(self.btn_ping, "btn_ping")
            
            # 保存IP按鈕
            if hasattr(self, 'btn_save_ip'):
                self.tooltip_manager.add_tooltip(self.btn_save_ip, "btn_save_ip")
            
            # 刪除IP按鈕
            if hasattr(self, 'btn_delete_ip'):
                self.tooltip_manager.add_tooltip(self.btn_delete_ip, "btn_delete_ip")
            
            # IP +/- 按鈕
            if hasattr(self, 'btn_ip_plus'):
                self.tooltip_manager.add_tooltip(self.btn_ip_plus, "btn_ip_plus")
            
            if hasattr(self, 'btn_ip_minus'):
                self.tooltip_manager.add_tooltip(self.btn_ip_minus, "btn_ip_minus")
            
            # 移除結束字串按鈕
            if hasattr(self, 'btn_remove_end'):
                self.tooltip_manager.add_tooltip(self.btn_remove_end, "btn_remove_end")
            
            # 清除IP記錄按鈕
            if hasattr(self, 'btn_clear_ip'):
                self.tooltip_manager.add_tooltip(self.btn_clear_ip, "btn_clear_ip")
            
            # 字體調整按鈕
            if hasattr(self, 'btn_ui_font_minus'):
                self.tooltip_manager.add_tooltip(self.btn_ui_font_minus, "btn_ui_font_minus")
            
            if hasattr(self, 'btn_ui_font_plus'):
                self.tooltip_manager.add_tooltip(self.btn_ui_font_plus, "btn_ui_font_plus")
            
            if hasattr(self, 'btn_content_font_minus'):
                self.tooltip_manager.add_tooltip(self.btn_content_font_minus, "btn_content_font_minus")
            
            if hasattr(self, 'btn_content_font_plus'):
                self.tooltip_manager.add_tooltip(self.btn_content_font_plus, "btn_content_font_plus")
            
            # open cmd table按鈕
            if hasattr(self, 'btn_open_script'):
                self.tooltip_manager.add_tooltip(self.btn_open_script, "btn_open_cmd_table")
            
            # 為combobox組件添加tooltip
            if hasattr(self, 'combobox_com'):
                self.tooltip_manager.add_tooltip(self.combobox_com, "combobox_com")
            
            if hasattr(self, 'combobox_cmd'):
                self.tooltip_manager.add_tooltip(self.combobox_cmd, "combobox_cmd")
            
            if hasattr(self, 'combobox_end'):
                self.tooltip_manager.add_tooltip(self.combobox_end, "combobox_end")
            
            if hasattr(self, 'combobox_transport'):
                self.tooltip_manager.add_tooltip(self.combobox_transport, "combobox_transport")
            
            # 為IP下拉選單添加tooltip
            if hasattr(self, 'ip_combobox'):
                self.tooltip_manager.add_tooltip(self.ip_combobox, "ip_combobox")
            
            if hasattr(self, 'entry_timeout'):
                self.tooltip_manager.add_tooltip(self.entry_timeout, "entry_timeout")
            
            # 自動執行checkbox已移除
            
            # 為label組件添加tooltip
            if hasattr(self, 'label_com'):
                self.tooltip_manager.add_tooltip(self.label_com, "label_com")
            
            if hasattr(self, 'label_cmd'):
                self.tooltip_manager.add_tooltip(self.label_cmd, "label_cmd")
            
            if hasattr(self, 'label_ip'):
                self.tooltip_manager.add_tooltip(self.label_ip, "label_ip")
            
            if hasattr(self, 'label_end'):
                self.tooltip_manager.add_tooltip(self.label_end, "label_end")
            
            if hasattr(self, 'label_timeout'):
                self.tooltip_manager.add_tooltip(self.label_timeout, "label_timeout")
            
            if hasattr(self, 'label_ui_font'):
                self.tooltip_manager.add_tooltip(self.label_ui_font, "label_ui_font")
            
            if hasattr(self, 'label_content_font'):
                self.tooltip_manager.add_tooltip(self.label_content_font, "label_content_font")
            
            # 為scale組件添加tooltip
            if hasattr(self, 'ui_font_scale'):
                self.tooltip_manager.add_tooltip(self.ui_font_scale, "ui_font_scale")
            
            if hasattr(self, 'content_font_scale'):
                self.tooltip_manager.add_tooltip(self.content_font_scale, "content_font_scale")
            
            # 為text組件添加tooltip
            if hasattr(self, 'text_output'):
                self.tooltip_manager.add_tooltip(self.text_output, "text_output")
            
            # 為progress組件添加tooltip
            if hasattr(self, 'progress'):
                self.tooltip_manager.add_tooltip(self.progress, "progress")
            
            # 為主要的frame和panel組件添加tooltip
            if hasattr(self, 'left_panel'):
                self.tooltip_manager.add_tooltip(self.left_panel, "left_panel")
            
            if hasattr(self, 'right_panel'):
                self.tooltip_manager.add_tooltip(self.right_panel, "right_panel")
            
            if hasattr(self, 'main_frame'):
                self.tooltip_manager.add_tooltip(self.main_frame, "main_frame")
            
            # 為section_description組件添加tooltip
            if hasattr(self, 'section_description'):
                self.tooltip_manager.add_tooltip(self.section_description, "section_description")
            
            # 為editor_text組件添加tooltip
            if hasattr(self, 'editor_text'):
                self.tooltip_manager.add_tooltip(self.editor_text, "editor_text")
            
            # 為editor_window中的按鈕添加tooltip
            if hasattr(self, 'save_button'):
                self.tooltip_manager.add_tooltip(self.save_button, "save_button")
            
            if hasattr(self, 'reload_button'):
                self.tooltip_manager.add_tooltip(self.reload_button, "reload_button")
            
            if hasattr(self, 'close_button'):
                self.tooltip_manager.add_tooltip(self.close_button, "close_button")
            
            print("[INFO] ToolTip 提示已初始化完成")
            
        except Exception as e:
            print(f"[ERROR] 初始化 ToolTip 時發生錯誤: {e}")

    def set_tooltips_enabled(self, enabled):
        """設定 ToolTip 的啟用狀態"""
        if hasattr(self, 'tooltip_manager'):
            self.tooltip_manager.set_all_enabled(enabled)

    def update_startup_label(self, new_text):
        """更新啟動標籤文字"""
        try:
            if hasattr(self, 'startup_label_manager'):
                self.startup_label_manager.update_label_text(new_text)
                print(f"[DEBUG] 啟動標籤已更新: {new_text}")
        except Exception as e:
            print(f"[ERROR] 更新啟動標籤失敗: {e}")

    def save_startup_label(self, new_text):
        """保存啟動標籤設定"""
        try:
            if hasattr(self, 'startup_label_manager'):
                return self.startup_label_manager.save_startup_label_setting(new_text)
        except Exception as e:
            print(f"[ERROR] 保存啟動標籤設定失敗: {e}")
            return False

    def notify_settings_tab_update(self):
        """通知設定標籤頁更新 IP 地址和結束字串列表"""
        try:
            # 獲取主視窗
            root = self.winfo_toplevel()
            if root and hasattr(root, 'tab_manager'):
                tab_manager = root.tab_manager
                if hasattr(tab_manager, 'settings_ui'):
                    # 調用設定標籤頁的刷新方法
                    tab_manager.settings_ui.refresh_from_dut_control()
                    print("[DEBUG] 已通知設定標籤頁更新")
                else:
                    print("[DEBUG] 設定標籤頁未找到")
            else:
                print("[DEBUG] 主視窗或標籤管理器未找到")
        except Exception as e:
            print(f"[ERROR] 通知設定標籤頁更新時發生錯誤: {e}")
    
    def on_end_string_changed(self, *args):
        """結束字串變化時即時保存"""
        try:
            current_end = self.end_string_var.get().strip()
            if current_end:
                from config_core import load_settings, save_settings
                settings = load_settings()
                if 'DUT_Control' not in settings:
                    settings['DUT_Control'] = {}
                settings['DUT_Control']['Command_End_String'] = current_end
                save_settings(settings)
                print(f"[INFO] 結束字串已保存: {current_end}")
        except Exception as e:
            print(f"[ERROR] 保存結束字串失敗: {e}")
    
    def on_add_end_string(self):
        """添加新結束字串並即時保存"""
        try:
            from tkinter import simpledialog
            new_end_string = simpledialog.askstring("添加結束字串", "請輸入新的結束字串:")
            if not new_end_string or not new_end_string.strip():
                return
                
            new_end_string = new_end_string.strip()
            
            # 檢查是否已存在
            current_values = list(self.combobox_end['values'])
            if new_end_string in current_values:
                from tkinter import messagebox
                messagebox.showwarning("警告", "該結束字串已存在")
                return
            
            # 添加到列表
            current_values.append(new_end_string)
            self.combobox_end['values'] = current_values
            
            # 立即保存到設定檔
            from config_core import load_settings, save_settings
            settings = load_settings()
            if 'DUT_Control' not in settings:
                settings['DUT_Control'] = {}
            settings['DUT_Control']['Available_End_Strings'] = current_values
            settings['DUT_Control']['Command_End_String'] = new_end_string
            save_settings(settings)
            
            # 設定為當前選擇
            self.end_string_var.set(new_end_string)
            
            print(f"[INFO] 已添加並保存結束字串: {new_end_string}")
            
        except Exception as e:
            print(f"[ERROR] 添加結束字串失敗: {e}")
    
    def on_remove_end_string(self):
        """移除結束字串並即時保存"""
        try:
            current_end = self.end_string_var.get().strip()
            current_values = list(self.combobox_end['values'])
            
            if current_end not in current_values:
                return
                
            if len(current_values) <= 1:
                from tkinter import messagebox
                messagebox.showwarning("警告", "至少需要保留一個結束字串")
                return
            
            # 從列表中移除
            current_values.remove(current_end)
            self.combobox_end['values'] = current_values
            
            # 設定為第一個可用的結束字串
            if current_values:
                new_end = current_values[0]
                self.end_string_var.set(new_end)
            
            # 立即保存到設定檔
            from config_core import load_settings, save_settings
            settings = load_settings()
            if 'DUT_Control' not in settings:
                settings['DUT_Control'] = {}
            settings['DUT_Control']['Available_End_Strings'] = current_values
            if current_values:
                settings['DUT_Control']['Command_End_String'] = current_values[0]
            save_settings(settings)
            
            print(f"[INFO] 已移除並保存結束字串: {current_end}")
            
        except Exception as e:
            print(f"[ERROR] 移除結束字串失敗: {e}")

    def on_close(self):
        """關閉前保存當前 IP 到歷史與預設"""
        try:
            from config_core import load_setup, save_setup
            setup = load_setup()
            dut = setup.setdefault('DUT_Control', {})
            current_ip = ''
            try:
                current_ip = self.ip_combobox.get().strip()
            except Exception:
                pass
            if current_ip:
                ip_history = dut.get('IP_History', [])
                if current_ip in ip_history:
                    ip_history.remove(current_ip)
                ip_history.insert(0, current_ip)
                if len(ip_history) > 20:
                    ip_history = ip_history[:20]
                dut['IP_History'] = ip_history
                dut['Default_IP_Address'] = current_ip
                save_setup(setup, manual_save=True)
        except Exception:
            pass