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
from ui_parts.ui_handlers_core import UIHandlersCore


class ManualCommandUI:
    """手動輸入指令 UI 類別"""
    
    def __init__(self, parent, root, highlight_keywords=None):
        """
        初始化手動輸入指令 UI
        parent: 父級 tk 元件
        root: 根 tk 視窗
        highlight_keywords: 要高亮的關鍵字字典
        """
        self.parent = parent
        self.root = root
        self.highlight_keywords = highlight_keywords or {}
        
        # 載入設定
        self.setup = load_setup()
        self.manual_setup = self.setup.get('Manual_Command', {})
        
        # 初始化變數
        self.command_history = []  # 指令歷史記錄
        self.history_index = -1   # 歷史記錄索引
        self.current_worker = None # 當前工作執行緒
        self.serial_connection = None  # 串口連接
        self.notepad_process = None  # 記事本程序
        
        # 創建 UI 元件
        self.create_widgets()
        
        # 綁定快捷鍵
        self.bind_shortcuts()
        
        # 更新字體大小
        self.update_fonts_from_config()
    
    def create_widgets(self):
        """創建 UI 元件"""
        # 創建主分割視窗
        self.paned_window = ttk.PanedWindow(self.parent, orient='horizontal')
        self.paned_window.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 左側控制面板
        self.left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_frame, weight=1)
        
        # 右側輸出面板
        self.right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.right_frame, weight=2)
        
        # 創建左側元件
        self.create_left_panel()
        
        # 創建右側元件
        self.create_right_panel()
        
        # 設置分割位置
        sash_position = int(self.manual_setup.get('Pane_Sash_Position', 400))
        self.paned_window.sashpos(0, sash_position)
    
    def create_left_panel(self):
        """創建左側控制面板"""
        # 通訊設定區域（最上方）
        settings_frame = ttk.LabelFrame(self.left_frame, text="通訊設定", padding="5")
        settings_frame.pack(fill='x', padx=5, pady=5)
        
        # COM Port 選擇
        com_frame = ttk.Frame(settings_frame)
        com_frame.pack(fill='x', pady=(0, 5))
        com_frame.columnconfigure(0, weight=1)
        
        ttk.Label(com_frame, text="COM Port:").pack(anchor='w')
        self.com_port_var = tk.StringVar(value=self.manual_setup.get('Serial_COM_Port', ''))
        self.com_port_combo = ttk.Combobox(com_frame, textvariable=self.com_port_var, state='readonly')
        self.com_port_combo.pack(side='left', fill='x', expand=True)
        
        # 刷新 COM Port 按鈕
        self.refresh_com_button = ttk.Button(com_frame, text="🔄", width=3, command=self.refresh_com_ports)
        self.refresh_com_button.pack(side='right', padx=(5, 0))
        
        # 傳輸方式（只顯示 Console 和 ADB）
        ttk.Label(settings_frame, text="傳輸方式:").pack(anchor='w')
        self.transport_mode_var = tk.StringVar(value=self.manual_setup.get('Command_Transport_Mode', 'Console'))
        transport_combo = ttk.Combobox(settings_frame, textvariable=self.transport_mode_var, 
                                     values=['Console', 'ADB'], state='readonly')
        transport_combo.pack(fill='x', pady=(0, 5))
        
        # 結束字串設定
        end_string_frame = ttk.Frame(settings_frame)
        end_string_frame.pack(fill='x', pady=(0, 5))
        end_string_frame.columnconfigure(1, weight=1)
        
        ttk.Label(end_string_frame, text="結束字串:").pack(side='left')
        self.end_string_var = tk.StringVar(value=self.manual_setup.get('Command_End_String', 'root'))
        self.end_string_entry = ttk.Entry(end_string_frame, textvariable=self.end_string_var, width=15)
        self.end_string_entry.pack(side='left', fill='x', expand=True, padx=(5, 0))
        
        # Timeout 設定
        timeout_frame = ttk.Frame(settings_frame)
        timeout_frame.pack(fill='x', pady=(0, 5))
        timeout_frame.columnconfigure(1, weight=1)
        
        ttk.Label(timeout_frame, text="Timeout (秒):").pack(side='left')
        self.timeout_var = tk.StringVar(value=self.manual_setup.get('Command_Timeout_Seconds', '3'))
        timeout_entry = ttk.Entry(timeout_frame, textvariable=self.timeout_var, width=10)
        timeout_entry.pack(side='right')
        
        # 指令輸入區域
        input_frame = ttk.LabelFrame(self.left_frame, text="指令輸入", padding="5")
        input_frame.pack(fill='x', padx=5, pady=5)
        
        # 指令輸入框（淺綠色背景）
        self.command_entry = ttk.Entry(input_frame, font=('Consolas', 11))
        self.command_entry.pack(fill='x', pady=(0, 5))
        
        # 設置淺綠色背景
        self.command_entry.configure(style='LightGreen.TEntry')
        
        # 按鈕框架
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill='x')
        
        # 執行按鈕（綠色底，hover 變藍色）
        self.execute_button = ttk.Button(button_frame, text="執行", command=self.on_manual_command_click, style='Green.TButton')
        self.execute_button.pack(side='left', padx=(0, 5))
        
        # 添加滑鼠指針效果
        self.execute_button.bind('<Enter>', lambda e: self.execute_button.configure(cursor='hand2'))
        self.execute_button.bind('<Leave>', lambda e: self.execute_button.configure(cursor=''))
        
        # 清除按鈕
        self.clear_button = ttk.Button(button_frame, text="清除", command=self.clear_input)
        self.clear_button.pack(side='left', padx=(0, 5))
        
        # 開啟指令檔案按鈕
        self.open_file_button = ttk.Button(button_frame, text="開啟指令檔案", command=self.toggle_command_file)
        self.open_file_button.pack(side='left')
        
        # 提示文字區域
        hint_frame = ttk.LabelFrame(self.left_frame, text="提示", padding="5")
        hint_frame.pack(fill='x', padx=5, pady=5)
        
        self.hint_label = ttk.Label(hint_frame, text=self.manual_setup.get('Hint_Text', '請輸入指令並按執行'))
        self.hint_label.pack(fill='x')
        
        # 初始化 COM Port 列表
        self.refresh_com_ports()
        
        # 創建淺綠色輸入框樣式
        self.create_custom_styles()
    
    def create_custom_styles(self):
        """創建自定義樣式"""
        style = ttk.Style()
        
        # 淺綠色輸入框樣式
        style.configure('LightGreen.TEntry', 
                       fieldbackground='#e8f5e8',  # 淺綠色背景
                       borderwidth=1,
                       relief='solid')
        
        # 綠色執行按鈕樣式
        style.configure('Green.TButton',
                       background='#4CAF50',  # 綠色
                       foreground='white')
        
        # 藍色 hover 樣式
        style.map('Green.TButton',
                 background=[('active', '#2196F3')])  # hover 時變藍色
    
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
        content_font_size = int(dut_settings.get('Content_Font_Size', 12))
        content_font = ('Consolas', content_font_size)

        # 輸出文字區域
        self.output_text = scrolledtext.ScrolledText(
            output_container,
            font=content_font,
            wrap='word',
            bg='black',
            fg='white',
            insertbackground='white'
        )
        self.output_text.pack(fill='both', expand=True)
        
        # 綁定 Enter 鍵事件
        self.output_text.bind('<Return>', self.on_output_enter)
        self.output_text.bind('<Control-v>', self.on_paste_command)
        
        # 清除輸出按鈕
        clear_output_button = ttk.Button(output_container, text="清除輸出", command=self.clear_output)
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
        """從設定檔更新字體大小，並套用到所有主要元件"""
        try:
            dut_settings = self.setup.get('DUT_Control', {})
            ui_font_size = int(dut_settings.get('UI_Font_Size', 12))
            content_font_size = int(dut_settings.get('Content_Font_Size', 12))
            ui_font = ('Microsoft JhengHei UI', ui_font_size)
            content_font = ('Consolas', content_font_size)

            # 標籤
            for widget in [self.hint_label, self.status_label]:
                if widget.winfo_exists():
                    widget.configure(font=ui_font)
            # 輸出區
            if hasattr(self, 'output_text'):
                self.output_text.configure(font=content_font)
            # 指令輸入框
            if hasattr(self, 'command_entry'):
                self.command_entry.configure(font=content_font)
            # COM Port 下拉選單
            if hasattr(self, 'com_port_combo'):
                self.com_port_combo.configure(font=ui_font)
            # 傳輸模式下拉選單
            if hasattr(self, 'transport_mode_var'): # Changed from transport_mode_combo to transport_mode_var
                self.transport_mode_var.set(self.manual_setup.get('Command_Transport_Mode', 'Console')) # Ensure it's a StringVar
                self.transport_mode_var.configure(font=ui_font)
            # 超時時間輸入框
            if hasattr(self, 'timeout_var'): # Changed from timeout_entry to timeout_var
                self.timeout_var.set(self.manual_setup.get('Command_Timeout_Seconds', '3')) # Ensure it's a StringVar
                self.timeout_var.configure(font=ui_font)
            # 結束字串輸入框
            if hasattr(self, 'end_string_var'): # Changed from end_string_entry to end_string_var
                self.end_string_var.set(self.manual_setup.get('Command_End_String', 'root')) # Ensure it's a StringVar
                self.end_string_var.configure(font=ui_font)
            # 執行按鈕
            if hasattr(self, 'execute_button'):
                self.execute_button.configure(font=ui_font)
            # 清除按鈕
            if hasattr(self, 'clear_button'):
                self.clear_button.configure(font=ui_font)
            # 開啟指令檔案按鈕
            if hasattr(self, 'open_file_button'):
                self.open_file_button.configure(font=ui_font)
            # 連線狀態燈（如有文字）
            if hasattr(self, 'connection_light') and hasattr(self.connection_light, 'configure'):
                try:
                    self.connection_light.configure(font=ui_font)
                except Exception:
                    pass
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
        self.output_text.insert(tk.END, "root@MU310:~# ")
        self.output_text.see(tk.END)
    
    def execute_command_from_output(self, command):
        """從輸出區域執行指令"""
        if not command.strip():
            return
        
        # 獲取設定
        com_port = extract_com_port_name(self.com_port_var.get())
        timeout = int(self.timeout_var.get())
        transport_mode = self.transport_mode_var.get()
        end_string = self.end_string_var.get()
        
        # 顯示指令
        self.output_text.insert(tk.END, f"{command}\n")
        self.output_text.see(tk.END)
        
        # 執行指令
        self.execute_command_thread(command, com_port, timeout, transport_mode, end_string)
    
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
    
    def show_error(self, message):
        """顯示錯誤訊息"""
        self.output_text.insert(tk.END, f"錯誤: {message}\n")
        self.add_prompt()
        self.command_finished()
    
    def command_finished(self):
        """指令執行完成"""
        self.status_label.config(text="就緒")
        self.execute_button.config(state='normal')
        self.update_connection_light('gray')
        
        # 在互動模式下，添加提示符
        self.add_prompt()
    
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
        self.command_entry.delete(0, tk.END)
    
    def clear_output(self):
        """清除輸出區域"""
        self.output_text.delete(1.0, tk.END)
        self.add_prompt()
    
    def on_manual_command_click(self):
        """執行手動指令按鈕點擊事件"""
        command = self.command_entry.get().strip()
        if not command:
            return
        
        # 獲取設定
        com_port = extract_com_port_name(self.com_port_var.get())
        timeout = int(self.timeout_var.get())
        transport_mode = self.transport_mode_var.get()
        end_string = self.end_string_var.get()
        
        # 檢查 COM Port
        if not com_port:
            messagebox.showerror("錯誤", "請選擇 COM Port")
            return
        
        # 更新狀態
        self.status_label.config(text="執行中...")
        self.execute_button.config(state='disabled')
        self.update_connection_light('yellow')
        
        # 清空輸入框
        self.command_entry.delete(0, tk.END)
        
        # 在輸出區域顯示指令
        self.output_text.insert(tk.END, f"{command}\n")
        self.output_text.see(tk.END)
        
        # 執行指令
        self.execute_command_thread(command, com_port, timeout, transport_mode, end_string)
    
    def execute_command_thread(self, command, com_port, timeout, transport_mode, end_string):
        """
        在執行緒中執行指令，並即時顯示回應內容
        """
        def run():
            try:
                ser = serial.Serial(
                    port=com_port,
                    baudrate=115200,
                    timeout=timeout,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE
                )

                ser.write(f"{command}\r\n".encode('utf-8'))

                response = ""
                start_time = time.time()
                end_string_found = False

                while time.time() - start_time < timeout and not end_string_found:
                    if ser.in_waiting:
                        data = ser.read(ser.in_waiting)
                        decoded = data.decode('utf-8', errors='ignore')
                        response += decoded
                        # 即時顯示新收到的資料
                        self.root.after(0, lambda text=decoded: self.append_output(text))
                        if end_string and end_string in response:
                            print(f"[DEBUG] 找到結束字串: {end_string}")
                            end_string_found = True
                            break
                    time.sleep(0.01)

                ser.close()

                if end_string_found:
                    self.root.after(0, lambda: self.append_output(f"[結束] 找到結束字串 '{end_string}'，停止讀取\n"))
                # 不再一次性 append_output(response)，因為已即時顯示
                self.root.after(0, self.command_finished)

            except Exception as e:
                error_msg = f"執行指令失敗: {e}"
                self.root.after(0, lambda: self.show_error(error_msg))

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()
    
    def save_manual_settings(self):
        """保存手動指令設定"""
        try:
            # 更新設定
            self.manual_setup['Serial_COM_Port'] = extract_com_port_name(self.com_port_var.get())
            self.manual_setup['Command_Transport_Mode'] = self.transport_mode_var.get()
            self.manual_setup['Command_Timeout_Seconds'] = self.timeout_var.get()
            self.manual_setup['Command_End_String'] = self.end_string_var.get()
            
            # 保存到設定檔
            self.setup['Manual_Command'] = self.manual_setup
            save_setup(self.setup)
            
        except Exception as e:
            print(f"保存手動指令設定失敗: {e}")
    
    def update_hint_text(self, hint_text):
        """更新提示文字"""
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
            self.timeout_var.set(self.manual_setup.get('Command_Timeout_Seconds', '3'))
            self.end_string_var.set(self.manual_setup.get('Command_End_String', 'root'))
            
            # 更新字體大小
            self.update_fonts_from_config()
            
        except Exception as e:
            print(f"從設定檔更新 UI 失敗: {e}")
    
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
            self.save_manual_settings()
            
            # 清理變數
            self.command_history.clear()
            
        except Exception as e:
            print(f"關閉時清理失敗: {e}") 