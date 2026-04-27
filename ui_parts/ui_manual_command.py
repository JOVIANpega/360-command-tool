# -*- coding: utf-8 -*-
"""
手動輸入指令 UI 模組
提供類似 Tera Term 的手動指令輸入功能
"""

import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import threading
from datetime import datetime
import serial
import time
import re
import subprocess

from config_core import load_setup, save_setup, list_com_ports, extract_com_port_name
from transport.serial_worker_v2 import SerialWorkerV2
from transport.adb_worker_v2 import ADBWorkerV2
from transport.ssh_worker_v2 import SSHWorkerV2


class ManualCommandUI:
    """手動輸入指令 UI 類別"""
    
    def __init__(self, parent, root, highlight_keywords=None, tooltip_manager=None):
        """
        初始化手動輸入指令 UI
        parent: 父級 tk 元件
        root: 根 tk 視窗
        highlight_keywords: 要高亮的關鍵字字典
        tooltip_manager: 工具提示管理器
        """
        self.parent = parent
        self.root = root
        self.highlight_keywords = highlight_keywords or {}
        self.tooltip_manager = tooltip_manager
        
        # 載入設定
        self.setup = load_setup()
        self.manual_setup = self.setup.get('Manual_Command', {})
        
        # 初始化變數
        self.command_history = []  # 指令歷史記錄
        self.history_index = -1   # 歷史記錄索引
        self.serial_connection = None  # 串口連接
        self.stop_event = threading.Event()  # 用於停止執行緒
        self.notepad_process = None  # 記事本程序
        
        # 創建自定義樣式
        self.create_custom_styles()
        
        # 創建 UI 元件
        self.create_widgets()
        
        # 綁定快捷鍵
        self.bind_shortcuts()
        
        # 更新字體大小
        self.update_fonts_from_config()
    
    def create_widgets(self):
        """創建 UI 元件"""
        # 創建主分割視窗
        self.paned_window = ttk.PanedWindow(self.parent, orient='horizontal', style='Main.TPanedwindow')
        self.paned_window.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 左側控制面板
        self.left_frame = ttk.Frame(self.paned_window, style='Main.TFrame')
        self.paned_window.add(self.left_frame, weight=1)
        
        # 右側輸出面板
        self.right_frame = ttk.Frame(self.paned_window, style='Main.TFrame')
        self.paned_window.add(self.right_frame, weight=2)
        
        # 創建左側元件
        self.create_left_panel()
        
        # 創建右側元件
        self.create_right_panel()
        
        # 設置分割位置
        sash_position = int(self.manual_setup.get('Pane_Sash_Position', 400))
        self.paned_window.sashpos(0, sash_position)
        
        # 綁定分割位置變更事件
        self.paned_window.bind("<ButtonRelease-1>", lambda e: self.on_sash_pos_changed())
    
    def create_left_panel(self):
        """創建左側控制面板"""
        # 通訊設定區域（最上方）
        settings_frame = ttk.LabelFrame(self.left_frame, text="通訊設定", padding="5", style='Main.TLabelframe')
        settings_frame.pack(fill='x', padx=5, pady=5)
        
        # 水平排列的設定區域
        horizontal_frame = ttk.Frame(settings_frame, style='Main.TFrame')
        horizontal_frame.pack(fill='x', pady=(0, 5))
        horizontal_frame.columnconfigure(0, weight=0)
        horizontal_frame.columnconfigure(1, weight=0)
        horizontal_frame.columnconfigure(2, weight=0)
        horizontal_frame.columnconfigure(3, weight=1) # 增加彈性空間將內容推向左側
        
        # COM Port 選擇
        com_frame = ttk.Frame(horizontal_frame, style='Main.TFrame')
        com_frame.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        
        ttk.Label(com_frame, text="COM Port:", style='Main.TLabel').pack(anchor='w')
        com_input_frame = ttk.Frame(com_frame, style='Main.TFrame')
        com_input_frame.pack(fill='x')
        
        self.com_port_var = tk.StringVar(value=self.manual_setup.get('Serial_COM_Port', ''))
        self.com_port_combo = ttk.Combobox(com_input_frame, textvariable=self.com_port_var, 
                                          state='readonly', width=20, font=('Microsoft JhengHei UI', 10))
        self.com_port_combo.pack(side='left', fill='none', expand=False)
        self.com_port_combo.bind("<<ComboboxSelected>>", self.on_com_port_changed)
        
        # 刷新 COM Port 按鈕 (與 DUT 一致)
        self.refresh_com_button = tk.Button(com_input_frame, text='刷新', command=self.refresh_com_ports,
                                          bg='#d9d9d9', fg='black', 
                                          activebackground='#2196F3', activeforeground='white',
                                          height=2, font=('Microsoft JhengHei UI', 9, 'bold'),
                                          relief='raised', borderwidth=1)
        self.refresh_com_button.pack(side='right', padx=(2, 0))

        # 懸停效果
        def on_btn_enter(e):
            self.refresh_com_button.config(bg='#2196F3', fg='white')
        def on_btn_leave(e):
            self.refresh_com_button.config(bg='#d9d9d9', fg='black')
        self.refresh_com_button.bind('<Enter>', on_btn_enter)
        self.refresh_com_button.bind('<Leave>', on_btn_leave)
        
        # 傳輸方式
        transport_frame = ttk.Frame(horizontal_frame, style='Main.TFrame')
        transport_frame.grid(row=0, column=1, sticky='ew', padx=(5, 5))
        
        ttk.Label(transport_frame, text="傳輸方式:", style='Main.TLabel').pack(anchor='w')
        self.transport_mode_var = tk.StringVar(value=self.manual_setup.get('Command_Transport_Mode', 'Console'))
        transport_combo = ttk.Combobox(transport_frame, textvariable=self.transport_mode_var, 
                                      values=['Console', 'ADB', 'SSH'], state='readonly', width=20, font=('Microsoft JhengHei UI', 10))
        transport_combo.pack(fill='none', anchor='w')
        transport_combo.bind("<<ComboboxSelected>>", self.on_transport_mode_changed)
        
        # 結束字串設定
        end_string_frame = ttk.Frame(horizontal_frame, style='Main.TFrame')
        end_string_frame.grid(row=0, column=2, sticky='ew', padx=(5, 0))
        
        ttk.Label(end_string_frame, text="結束字串:", style='Main.TLabel').pack(anchor='w')
        self.end_string_var = tk.StringVar(value=self.manual_setup.get('Command_End_String', 'root'))
        self.end_string_entry = ttk.Entry(end_string_frame, textvariable=self.end_string_var, width=22, font=('Microsoft JhengHei UI', 10))
        self.end_string_entry.pack(fill='none', anchor='w')
        
        
        # 指令輸入區域
        input_frame = ttk.LabelFrame(self.left_frame, text="指令輸入", padding="5", style='Main.TLabelframe')
        input_frame.pack(fill='x', padx=5, pady=5)
        
        # 指令輸入框（兩行高度，淺綠色背景）
        self.command_entry = tk.Text(input_frame, font=('Consolas', 11), height=2, wrap='none',
                                    bg='#e8f5e8', fg='black', insertbackground='black')
        self.command_entry.pack(fill='x', pady=(0, 5))
        
        # 綁定 ENTER 鍵執行指令（空白時也能送出）
        self.command_entry.bind('<Return>', self.on_entry_enter)
        
        # 按鈕框架
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill='x')
        
        # 執行按鈕（綠色底，hover 變藍色）
        self.execute_button = ttk.Button(button_frame, text="執行", command=self.on_manual_command_click, style='Green.TButton')
        self.execute_button.pack(side='left', padx=(0, 5))
        
        # 添加滑鼠指針效果
        self.execute_button.bind('<Enter>', lambda e: self.execute_button.configure(cursor='hand2'))
        self.execute_button.bind('<Leave>', lambda e: self.execute_button.configure(cursor=''))

        # 停止按鈕 (紅色)
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.on_stop_click, state='disabled')
        self.stop_button.pack(side='left', padx=(0, 5))
        
        # 清除按鈕
        self.clear_button = ttk.Button(button_frame, text="清除", command=self.clear_input)
        self.clear_button.pack(side='left', padx=(0, 5))
        
        # 開啟指令檔案按鈕
        self.open_file_button = ttk.Button(button_frame, text="開啟指令檔案", command=self.toggle_command_file)
        self.open_file_button.pack(side='left')
        
        # 提示文字區域
        hint_frame = ttk.LabelFrame(self.left_frame, text="提示", padding="5", style='Main.TLabelframe')
        hint_frame.pack(fill='x', padx=5, pady=5)
        
        self.hint_label = tk.Label(hint_frame, text=self.manual_setup.get('Hint_Text', '請輸入指令並按執行'),
                                  background='lightblue', foreground='black', wraplength=300, justify='left')
        self.hint_label.pack(fill='x')
        
        # 初始化 COM Port 列表
        self.refresh_com_ports()
    
    def create_custom_styles(self):
        """創建自定義樣式"""
        style = ttk.Style()
        
        # 設定白色背景樣式，模仿 DUT 控制頁面
        style.configure('Main.TFrame', background='white')
        style.configure('Main.TLabel', background='white', foreground='black')
        style.configure('Main.TLabelframe', background='white', foreground='black')
        style.configure('Main.TLabelframe.Label', background='white', foreground='black')
        style.configure('Main.TPanedwindow', background='white')
        
        # 淺綠色輸入框樣式
        style.configure('LightGreen.TEntry', 
                       fieldbackground='#e8f5e8',  # 淺綠色背景
                       borderwidth=1,
                       relief='solid')
        
        # 綠色執行按鈕樣式 (改為灰底黑字，hover藍底白字)
        style.configure('Green.TButton',
                       background='#d9d9d9', 
                       foreground='black')
        
        # 藍色 hover 樣式
        style.map('Green.TButton',
                 background=[('active', '#2196F3')],
                 foreground=[('active', 'white')])
        
        # 藍色按鈕樣式 (改為灰底黑字，hover藍底白字)
        style.configure('Blue.TButton', 
                       background='#d9d9d9', 
                       foreground='black')
        style.map('Blue.TButton',
                 background=[('active', '#2196F3')],
                 foreground=[('active', 'white')])
    
    def create_right_panel(self):
        """創建右側輸出面板"""
        # 輸出標題
        output_title_frame = ttk.Frame(self.right_frame)
        output_title_frame.pack(fill='x', padx=5, pady=(5, 0))
        ttk.Label(output_title_frame, text="執行結果", font=('Arial', 12, 'bold')).pack(side='left')

        # 輸出文字區域（包含清除按鈕）
        output_container = ttk.Frame(self.right_frame)
        output_container.pack(fill='both', expand=True, padx=5, pady=5)

        # 取得 Content_Font_Size 設定
        dut_settings = self.setup.get('DUT_Control', {})
        try:
            content_font_size_value = dut_settings.get('Content_Font_Size', 12)
            content_font_size = int(content_font_size_value) if content_font_size_value != '' else 12
        except (ValueError, TypeError):
            content_font_size = 12
        content_font = ('Consolas', content_font_size)

        # 輸出文字區域
        self.output_text = scrolledtext.ScrolledText(
            output_container,
            font=content_font,
            wrap='word',
            bg='white',
            fg='black',
            insertbackground='black'
        )
        self.output_text.pack(fill='both', expand=True)
        
        # 設定彩色顯示標籤，完全複製 DUT 控制頁的顏色配置
        self.output_text.tag_configure("send", foreground="blue")        # [發送] 藍色
        self.output_text.tag_configure("error", foreground="red")        # [錯誤] 紅色
        self.output_text.tag_configure("end", foreground="green")        # [結束] 綠色
        self.output_text.tag_configure("purple", foreground="#800080")   # 標題紫色
        self.output_text.tag_configure("success", foreground="green")    # 成功訊息為綠色
        self.output_text.tag_configure("warning", foreground="orange")   # 警告訊息為橙色
        
        # 為高亮關鍵字定義標籤
        if hasattr(self, 'highlight_keywords'):
            for keyword, color in self.highlight_keywords.items():
                self.output_text.tag_configure(color, foreground=color)
        
        # 綁定 Enter 鍵事件
        self.output_text.bind('<Return>', self.on_output_enter)
        self.output_text.bind('<Control-v>', self.on_paste_command)
        
        # 清除輸出按鈕
        clear_output_button = ttk.Button(output_container, text="清除輸出", command=self.clear_output, style='Blue.TButton')
        clear_output_button.pack(pady=(5, 0))
        
        # 狀態列
        status_frame = ttk.Frame(self.right_frame)
        status_frame.pack(fill='x', padx=5, pady=(0, 5))
        
        # 連線狀態指示燈
        self.connection_light = tk.Label(status_frame, text="●", fg='gray', font=('Arial', 12))
        self.connection_light.pack(side='left')
        
        # 狀態標籤
        self.status_label = ttk.Label(status_frame, text="就緒")
        self.status_label.pack(side='left', padx=(5, 0))
        
        # 初始化輸出區域
        self.add_prompt()
    
    def update_fonts_from_config(self):
        """從設定檔更新字體大小，並套用到所有主要元件，與 DUT 控制設定完全同步"""
        try:
            dut_settings = self.setup.get('DUT_Control', {})
            
            # 安全解析字體大小
            try:
                ui_font_size_value = dut_settings.get('UI_Font_Size', 12)
                ui_font_size = int(ui_font_size_value) if ui_font_size_value != '' else 12
            except (ValueError, TypeError):
                ui_font_size = 12
                
            try:
                content_font_size_value = dut_settings.get('Content_Font_Size', 12)
                content_font_size = int(content_font_size_value) if content_font_size_value != '' else 12
            except (ValueError, TypeError):
                content_font_size = 12
            ui_font = ('Microsoft JhengHei UI', ui_font_size)
            content_font = ('Consolas', content_font_size)

            # 更新所有 Label 元件
            labels_to_update = []
            if hasattr(self, 'hint_label') and self.hint_label.winfo_exists():
                labels_to_update.append(self.hint_label)
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                labels_to_update.append(self.status_label)
            
            for widget in labels_to_update:
                try:
                    widget.configure(font=ui_font)
                except Exception as e:
                    print(f"[WARNING] 更新標籤字體失敗: {e}")

            # 更新所有 Entry 元件
            entries_to_update = []
            if hasattr(self, 'command_entry') and self.command_entry.winfo_exists():
                entries_to_update.append(self.command_entry)
            if hasattr(self, 'end_string_entry') and self.end_string_entry.winfo_exists():
                entries_to_update.append(self.end_string_entry)
            
            for widget in entries_to_update:
                try:
                    widget.configure(font=content_font)
                except Exception as e:
                    print(f"[WARNING] 更新輸入框字體失敗: {e}")

            # 更新所有 Combobox 元件
            combos_to_update = []
            if hasattr(self, 'com_port_combo') and self.com_port_combo.winfo_exists():
                combos_to_update.append(self.com_port_combo)
            
            for widget in combos_to_update:
                try:
                    widget.configure(font=content_font)
                except Exception as e:
                    print(f"[WARNING] 更新下拉選單字體失敗: {e}")

            # 更新所有 Button 元件
            buttons_to_update = []
            if hasattr(self, 'execute_button') and self.execute_button.winfo_exists():
                buttons_to_update.append(self.execute_button)
            if hasattr(self, 'clear_button') and self.clear_button.winfo_exists():
                buttons_to_update.append(self.clear_button)
            if hasattr(self, 'open_file_button') and self.open_file_button.winfo_exists():
                buttons_to_update.append(self.open_file_button)
            if hasattr(self, 'refresh_com_button') and self.refresh_com_button.winfo_exists():
                buttons_to_update.append(self.refresh_com_button)
            
            for widget in buttons_to_update:
                try:
                    widget.configure(font=ui_font)
                except Exception as e:
                    print(f"[WARNING] 更新按鈕字體失敗: {e}")

            # 更新 Text 輸出區域
            if hasattr(self, 'output_text') and self.output_text.winfo_exists():
                try:
                    self.output_text.configure(font=content_font)
                except Exception as e:
                    print(f"[WARNING] 更新輸出區域字體失敗: {e}")

            print(f"[DEBUG] 手動輸入指令頁面字體已更新 - UI: {ui_font_size}, 內容: {content_font_size}")
        except Exception as e:
            print(f"[ERROR] 更新字體大小失敗: {e}")
    
    def on_output_enter(self, event):
        """在輸出區域按 Enter 鍵時執行指令"""
        # 獲取當前行的指令
        command = self.get_current_line()
        if command.strip():
            self.execute_command_from_output(command)
        return 'break'  # 阻止預設的換行行為
    
    def on_paste_command(self, event):
        """在輸出區域按 Ctrl+V 時貼上指令"""
        try:
            clipboard_text = self.root.clipboard_get()
            if clipboard_text.strip():
                # 在當前位置插入剪貼簿內容
                self.output_text.insert(tk.INSERT, clipboard_text)
                print("[DEBUG] 已貼上指令到輸入框")
        except Exception as e:
            print(f"貼上指令失敗: {e}")
        return 'break'
    
    def get_current_line(self):
        """獲取當前行的指令內容"""
        try:
            # 獲取當前游標位置
            current_pos = self.output_text.index(tk.INSERT)
            line_start = self.output_text.index(f"{current_pos} linestart")
            line_end = self.output_text.index(f"{current_pos} lineend")
            
            # 獲取當前行文字
            line_text = self.output_text.get(line_start, line_end)
            
            # 移除提示符
            if line_text.startswith("root@MU310:~# "):
                return line_text[14:]  # 移除 "root@MU310:~# " 前綴
            elif line_text.startswith("root@MU310:~#"):
                return line_text[13:]  # 移除 "root@MU310:~#" 前綴
            
            return line_text.strip()
        except Exception as e:
            print(f"獲取當前行失敗: {e}")
            return ""
    
    def add_prompt(self):
        """添加提示符"""
        self.output_text.configure(state='normal')
        self.output_text.insert(tk.END, "root@MU310:~# ")
        self.output_text.see(tk.END)
        self.output_text.configure(state='disabled')
    
    def execute_command_from_output(self, command):
        """從輸出區域執行指令"""
        if not command.strip():
            return
        
        # 獲取設定
        com_port = extract_com_port_name(self.com_port_var.get())
        transport_mode = self.transport_mode_var.get()
        end_string = self.end_string_var.get()
        
        # 獲取超時
        timeout = 30
        cmd_timeout = 10.0
        try:
            cmd_timeout = float(self.setup.get('DUT_Control', {}).get('Single_Command_Timeout', 10.0))
        except (ValueError, TypeError):
            cmd_timeout = 10.0
        
        # 顯示指令
        self.output_text.configure(state='normal')
        self.output_text.insert(tk.END, f"{command}\n", "send")
        self.output_text.see(tk.END)
        self.output_text.configure(state='disabled')
        
        # 執行指令
        self.execute_command_thread(command, com_port, timeout, transport_mode, end_string, cmd_timeout)
    
    def append_output(self, text):
        """添加輸出文字（垂直排列）"""
        # 確保每個輸出都換行
        if text and not text.endswith('\n'):
            text += '\n'
        
        # 將文字按行分割並逐行顯示
        lines = text.split('\n')
        for line in lines:
            if line.strip():  # 只顯示非空行
                self.output_text.insert(tk.END, f"{line}\n")
        
        self.output_text.see(tk.END)
    
    def add_colored_output(self, text, tag=None):
        """添加彩色輸出文字，完全複製 DUT 控制頁的顯示邏輯"""
        self.output_text.configure(state='normal')
        
        if tag:
            self.output_text.insert(tk.END, text, tag)
        elif text.startswith('[發送]'):
            self.output_text.insert(tk.END, text, "send")
        elif text.startswith('[錯誤]'):
            self.output_text.insert(tk.END, text, "error")
        elif text.startswith('[結束]'):
            self.output_text.insert(tk.END, text, "end")
        elif text.startswith('===') or "執行指令:" in text:
            self.output_text.insert(tk.END, text, "purple")
        else:
            # 自動檢測關鍵字並應用顏色
            if hasattr(self, 'highlight_keywords') and self.highlight_keywords:
                start_pos = self.output_text.index(tk.END)
                self.output_text.insert(tk.END, text)
                
                # 按關鍵字長度降序排列，讓較長的關鍵字優先匹配
                sorted_keywords = sorted(self.highlight_keywords.items(), key=lambda x: len(x[0]), reverse=True)
                
                for keyword, color in sorted_keywords:
                    search_start = start_pos
                    while True:
                        idx = self.output_text.search(keyword, search_start, tk.END)
                        if not idx:
                            break
                        end_idx = f"{idx}+{len(keyword)}c"
                        try:
                            self.output_text.tag_add(color, idx, end_idx)
                        except Exception as e:
                            print(f"[ERROR] tag_add 失敗: {e}")
                        search_start = end_idx
            else:
                self.output_text.insert(tk.END, text)
        
        self.output_text.see(tk.END)
        self.output_text.configure(state='disabled')
    
    def show_error(self, message):
        """顯示錯誤訊息"""
        self.output_text.configure(state='normal')
        self.output_text.insert(tk.END, f"錯誤: {message}\n", "error")
        self.add_prompt()
        self.command_finished()
    
    def command_finished(self):
        """指令執行完成"""
        self.status_label.config(text="就緒")
        self.execute_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.update_connection_light('gray')
        
        # 在互動模式下，添加提示符
        self.add_prompt()
    
    def on_stop_click(self):
        """停止當前執行的指令"""
        self.stop_event.set()
        self.status_label.config(text="停止中...")
        self.stop_button.config(state='disabled')

    def update_connection_light(self, color):
        """更新連線狀態指示燈"""
        self.connection_light.config(bg=color)
    
    def refresh_com_ports(self):
        """刷新 COM Port 列表並保持當前選擇"""
        try:
            # 保存當前選擇
            current_selection = self.com_port_var.get()
            
            # 更新 COM 口列表
            new_ports = list_com_ports()
            self.com_port_combo['values'] = new_ports
            
            # 如果當前選擇仍在新列表中，保持選擇
            from config_core import extract_com_port_name
            current_actual_port = extract_com_port_name(current_selection) if current_selection else ""
            
            # 找到匹配的顯示名稱
            matching_display_name = None
            for display_name in new_ports:
                if extract_com_port_name(display_name) == current_actual_port:
                    matching_display_name = display_name
                    break
            
            if matching_display_name:
                self.com_port_var.set(matching_display_name)
                print(f"[DEBUG] refresh_com_ports: 保持選擇 {matching_display_name}")
            elif new_ports:
                # 選擇第一個可用的COM口
                selected_display_name = new_ports[0]
                actual_com_port = extract_com_port_name(selected_display_name)
                self.com_port_var.set(selected_display_name)
                print(f"[DEBUG] refresh_com_ports: 選擇新的COM口 {selected_display_name}")
                
                # 保存到設定檔
                self.manual_setup['Serial_COM_Port'] = actual_com_port
                self.save_manual_settings()
            else:
                # 如果沒有可用的COM口，清空選擇
                self.com_port_var.set('')
                print(f"[DEBUG] refresh_com_ports: 沒有可用的COM口")
                
        except Exception as e:
            print(f"刷新 COM Port 列表失敗: {e}")
    
    def toggle_command_file(self):
        """切換開啟/關閉指令檔案"""
        try:
            if self.notepad_process is None or self.notepad_process.poll() is not None:
                # 開啟指令檔案 - 使用 DUT_Control 中的指令檔案路徑
                command_file_path = self.setup.get('DUT_Control', {}).get('Command_File_Path', '')
                
                if not command_file_path or not os.path.exists(command_file_path):
                    messagebox.showwarning("警告", "指令檔案路徑未設定或檔案不存在")
                    return
                
                # 使用記事本開啟檔案
                self.notepad_process = subprocess.Popen(['notepad', command_file_path])
                self.open_file_button.config(text="關閉指令檔案")
                print(f"[DEBUG] 已開啟指令檔案: {command_file_path}")
            else:
                # 關閉記事本
                self.notepad_process.terminate()
                self.notepad_process = None
                self.open_file_button.config(text="開啟指令檔案")
                print("[DEBUG] 已關閉指令檔案")
                
        except Exception as e:
            print(f"操作指令檔案失敗: {e}")
            messagebox.showerror("錯誤", f"操作指令檔案失敗: {e}")
    
    def clear_input(self):
        """清除輸入框"""
        self.command_entry.delete("1.0", tk.END)
    
    def clear_output(self):
        """清除輸出區域"""
        self.output_text.configure(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state='disabled')
        self.add_prompt()
    
    def on_entry_enter(self, event):
        """輸入欄位按 ENTER 鍵時執行指令（空白時也能送出，如 Tera Term）"""
        self.on_manual_command_click()
        return 'break'  # 阻止預設行為
    
    def on_manual_command_click(self):
        """執行手動指令按鈕點擊事件"""
        command = self.command_entry.get("1.0", tk.END).rstrip('\n')  # 從Text widget獲取內容
        
        # 獲獲取設定
        com_port = extract_com_port_name(self.com_port_var.get())
        
        # 獲取總超時和單個指令超時
        timeout = 30  # 預設總超時
        cmd_timeout = 10.0  # 預設單個指令超時
        
        try:
            # 嘗試讀取全域設定中的單個指令超時
            cmd_timeout = float(self.setup.get('DUT_Control', {}).get('Single_Command_Timeout', 10.0))
        except (ValueError, TypeError):
            cmd_timeout = 10.0
            
        transport_mode = self.transport_mode_var.get()
        end_string = self.end_string_var.get()
        
        # 檢查 COM Port（僅在 Console 模式下檢查）
        if transport_mode == "Console" and not com_port:
            messagebox.showerror("錯誤", "請選擇 COM Port")
            return
        
        # 更新狀態
        self.status_label.config(text="執行中...")
        self.execute_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.update_connection_light('yellow')
        
        # 不清空輸入框，保留使用者輸入
        
        # 獲取並處理顯示用的 SSH 帳號資訊 (限制20字)
        display_acc = end_string
        if transport_mode == "SSH":
            ssh_acc = self.setup.get('DUT_Control', {}).get('SSH_Username', 'root')
            if len(ssh_acc) > 20:
                display_acc = ssh_acc[:17] + "..."
            else:
                display_acc = ssh_acc

        # 在輸出區域顯示指令（使用彩色顯示）
        if command.strip():
            self.add_colored_output(f"=== 執行指令: {command} ===\n", "send")
            if transport_mode == "SSH":
                self.add_colored_output(f"[SSH] 使用帳號: {display_acc}\n", "purple")
        
        # 執行指令
        self.execute_command_thread(command, com_port, timeout, transport_mode, end_string, cmd_timeout)
    
    def execute_command_thread(self, command, com_port, timeout, transport_mode, end_string, cmd_timeout=10.0, cmd_interval=1.0):
        """
        在執行緒中執行指令，並即時顯示回應內容
        支援 Console, ADB 和 SSH 三種傳輸模式
        """
        def on_data_callback(text, tag=None):
            self.root.after(0, lambda: self.add_colored_output(text, tag))
        
        def on_status_callback(connected):
            color = 'green' if connected else 'red'
            self.root.after(0, lambda: self.update_connection_light(color))
        
        def on_progress_callback(progress):
            pass
        
        def on_finish_callback():
            self.root.after(0, self.command_finished)

        # 重置停止事件
        self.stop_event.clear()
        
        # 獲取指令間隔
        try:
            cmd_interval = float(self.setup.get('DUT_Control', {}).get('Command_Interval', 1.0))
        except (ValueError, TypeError):
            cmd_interval = 1.0

        # 準備指令列表
        cmd_list = [command] if command.strip() else [""]

        try:
            if transport_mode == "ADB":
                # 使用 ADBWorkerV2
                worker = ADBWorkerV2(
                    cmd_list=cmd_list,
                    end_str=end_string,
                    timeout=timeout,
                    on_data=on_data_callback,
                    on_status=on_status_callback,
                    on_progress=on_progress_callback,
                    on_finish=on_finish_callback,
                    stop_event=self.stop_event,
                    cmd_timeout=cmd_timeout,
                    cmd_interval=cmd_interval
                )
            elif transport_mode == "SSH":
                # 使用 SSHWorkerV2
                dut_setup = self.setup.get('DUT_Control', {})
                worker = SSHWorkerV2(
                    cmd_list=cmd_list,
                    end_str=end_string,
                    timeout=timeout,
                    host=dut_setup.get('SSH_IP', '192.168.11.143'),
                    port=int(dut_setup.get('SSH_Port', 22)),
                    username=dut_setup.get('SSH_Username', 'root'),
                    password=dut_setup.get('SSH_Password', 'oelinux123'),
                    on_data=on_data_callback,
                    on_status=on_status_callback,
                    on_progress=on_progress_callback,
                    on_finish=on_finish_callback,
                    stop_event=self.stop_event,
                    cmd_timeout=cmd_timeout,
                    cmd_interval=cmd_interval
                )
            else:
                # 預設使用 SerialWorkerV2 (Console)
                # 從設定中獲取 Baudrate
                baudrate = 115200
                try:
                    baudrate = int(self.setup.get('DUT_Control', {}).get('Serial_Baudrate', 115200))
                except (ValueError, TypeError):
                    baudrate = 115200
                    
                worker = SerialWorkerV2(
                    com=com_port,
                    baudrate=baudrate,
                    cmd_list=cmd_list,
                    end_str=end_string,
                    timeout=timeout,
                    on_data=on_data_callback,
                    on_status=on_status_callback,
                    on_progress=on_progress_callback,
                    on_finish=on_finish_callback,
                    stop_event=self.stop_event,
                    cmd_timeout=cmd_timeout,
                    cmd_interval=cmd_interval
                )
            
            # 開始執行
            thread = threading.Thread(target=worker.run)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            error_msg = f"初始化工作執行緒失敗: {e}"
            self.root.after(0, lambda: self.show_error(error_msg))
    
    def on_com_port_changed(self, event=None):
        """COM口變更時保存設定"""
        try:
            self.manual_setup['Serial_COM_Port'] = extract_com_port_name(self.com_port_var.get())
            self.setup['Manual_Command'] = self.manual_setup
            save_setup(self.setup)
        except Exception as e:
            print(f"保存COM口設定失敗: {e}")
    
    def on_transport_mode_changed(self, event=None):
        """傳輸方式變更時保存設定"""
        try:
            self.manual_setup['Command_Transport_Mode'] = self.transport_mode_var.get()
            self.setup['Manual_Command'] = self.manual_setup
            save_setup(self.setup)
        except Exception as e:
            print(f"保存傳輸方式設定失敗: {e}")
    
    def save_manual_settings(self):
        """保存手動指令設定"""
        try:
            # 更新設定
            self.manual_setup['Serial_COM_Port'] = extract_com_port_name(self.com_port_var.get())
            self.manual_setup['Command_Transport_Mode'] = self.transport_mode_var.get()
            self.manual_setup['Command_End_String'] = self.end_string_var.get()
            
            # 保存到設定檔
            self.setup['Manual_Command'] = self.manual_setup
            save_setup(self.setup)
            
        except Exception as e:
            print(f"保存手動指令設定失敗: {e}")
    
    def update_hint_text(self, hint_text):
        """更新提示文字，限制顯示長度最多30個字"""
        if len(hint_text) > 30:
            hint_text = hint_text[:27] + "..."
        self.hint_label.config(text=hint_text)
    
    def update_from_config(self):
        """從設定檔更新 UI"""
        try:
            # 重新載入設定
            self.setup = load_setup()
            self.manual_setup = self.setup.get('Manual_Command', {})
            
            # 更新 COM Port
            com_port = self.manual_setup.get('Serial_COM_Port', '')
            if com_port:
                # 找到對應的顯示名稱
                available_ports = list_com_ports()
                for display_name in available_ports:
                    if extract_com_port_name(display_name) == com_port:
                        self.com_port_var.set(display_name)
                        break
            
            # 更新其他設定
            self.transport_mode_var.set(self.manual_setup.get('Command_Transport_Mode', 'Console'))
            self.end_string_var.set(self.manual_setup.get('Command_End_String', 'root'))
            
            # 更新字體大小
            self.update_fonts_from_config()
            
        except Exception as e:
            print(f"從設定檔更新 UI 失敗: {e}")
            
    def activate(self):
        """分頁激活時調用"""
        self.refresh_com_ports()
        self.restore_sash()
        
    def restore_sash(self):
        """恢復分割位置"""
        try:
            self.setup = load_setup()
            self.manual_setup = self.setup.get('Manual_Command', {})
            sash_position = int(self.manual_setup.get('Pane_Sash_Position', 400))
            self.paned_window.sashpos(0, sash_position)
        except:
            pass
            
    def on_sash_pos_changed(self):
        """分割位置變更時記錄"""
        try:
            pos = self.paned_window.sashpos(0)
            if pos > 0:
                print(f"[DEBUG] 記錄手動指令分頁分欄位置: {pos}")
                # 這裡不鎖定 IO，只在 save 時寫入磁碟
        except:
            pass
    
    def bind_shortcuts(self):
        """綁定快捷鍵"""
        # 在輸出區域綁定 Ctrl+C 複製選中的文字
        self.output_text.bind('<Control-c>', self.copy_selected_text)
    
    def copy_selected_text(self, event):
        """複製選中的文字"""
        try:
            selected_text = self.output_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                print("[DEBUG] 已複製選中的指令")
        except tk.TclError:
            print("[WARNING] 沒有選中的文字")
        return 'break'
    
    def on_close(self):
        """關閉時的清理工作"""
        try:
            # 關閉串口連接
            if self.serial_connection:
                self.serial_connection.close()
                self.serial_connection = None
            
            # 關閉記事本程序
            if self.notepad_process and self.notepad_process.poll() is None:
                self.notepad_process.terminate()
                self.notepad_process = None
            
            # 保存設定
            try:
                # 獲取當前分欄位置
                sash_pos = self.paned_window.sashpos(0)
                if 'Manual_Command' not in self.setup:
                    self.setup['Manual_Command'] = {}
                self.setup['Manual_Command']['Pane_Sash_Position'] = str(sash_pos)
            except: pass
            
            save_setup(self.setup)
            
            # 清理變數
            self.command_history.clear()
            
        except Exception as e:
            print(f"關閉時清理失敗: {e}") 