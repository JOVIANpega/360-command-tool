# -*- coding: utf-8 -*-

import tkinter as tk


from tkinter import ttk, scrolledtext


import os


import sys


import json





# 將當前目錄加入 Python 路徑


current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


sys.path.append(current_dir)





from config_core import list_com_ports, save_setup, GUIDE_FILE, COMMAND_FILE





import platform


import re


import threading


import time


from datetime import datetime


import psutil


# 導入通知訊息系統


from config_utils import get_notification_text, get_app_version


from ui_parts.tooltip import ToolTip





class UIComponentsBase:


    def __init__(self, parent, root):


        self.parent = parent


        self.root = root


        self.last_size = (0, 0)


        self.led_blinking = False


        self.main_frame = None


        self.radiobutton_frame = None


        self.section_radiobuttons = []


        # 控制下拉列表最大顯示項目數


        self.max_dropdown_items = 20  # 將下拉菜單最大顯示項目數從10改為20


        # 下拉列表字典


        self.dropdown_boxes = {}


        # 左側面板行數追蹤


        self.current_left_row = 0


        # 獲取高亮關鍵字


        self.highlight_keywords = getattr(parent, 'highlight_keywords', {})


        print(f"[DEBUG] 載入了 {len(self.highlight_keywords)} 個高亮關鍵字到 UIComponents")
        
        # 定義標準 UI 風格參數
        self.ui_font = "Segoe UI"  # Windows 預設字體
        self.ui_font_size = 10     # 預設字體大小
        self.ui_padding = 5        # 元件間距
        self.ui_button_width = 100 # 標準按鈕寬度
        self.ui_button_height = 30 # 標準按鈕高度
        self.ui_bg_color = "#f0f0f0" # 淺灰白底色
        
        # 初始化 UI
        self.init_ui()
        self.init_styles()

        # 讀取 setup.txt 的寬高
        width_str = self.parent.setup.get('Window_Width', 1600)
        try:
            width = int(width_str)
        except (ValueError, TypeError):
            width = 1600

        height_str = self.parent.setup.get('Window_Height', 900)
        try:
            height = int(height_str)
        except (ValueError, TypeError):
            height = 900

        # 視窗最大化
        try:
            self.parent.root.state('zoomed')  # Windows
        except Exception:
            self.parent.root.attributes('-zoomed', True)  # Linux
        self.last_size = (width, height)
        self.parent.root.bind('<Configure>', self.on_window_resize)
        # 綁定 Enter 鍵執行指令
        self.parent.root.bind('<Return>', lambda e: self.parent.handlers.on_execute())

    def init_styles(self):
        """初始化 ttk 樣式，設定 Windows 風格的外觀"""
        style = ttk.Style()
        
        # 設定主題為 'clam'，這是一個較為現代的主題
        try:
            style.theme_use('clam')
        except:
            print("[WARNING] 無法設定 'clam' 主題，使用預設主題")
        
        # 設定全局字體
        default_font = (self.ui_font, self.ui_font_size)
        
        # 設定各種元件樣式
        style.configure('TLabel', font=default_font, background=self.ui_bg_color)
        style.configure('TFrame', background=self.ui_bg_color)
        style.configure('TButton', font=default_font, width=self.ui_button_width)
        style.configure('TEntry', font=default_font)
        style.configure('TCombobox', font=default_font)
        
        # 設定按鈕懸停效果
        style.map('TButton',
                 foreground=[('active', '#000000')],
                 background=[('active', '#d1d1d1')])
        
        # 設定 Notebook (Tab) 樣式
        style.configure('TNotebook', background=self.ui_bg_color)
        style.configure('TNotebook.Tab', font=default_font, padding=[10, 5])
        
        # 設定分隔線樣式
        style.configure('TSeparator', background='#d1d1d1')
        
        # 設定進度條樣式
        style.configure('TProgressbar', background='#2196f3')
        
        # 設定 Panedwindow 樣式
        style.configure('TPanedwindow', background=self.ui_bg_color)
        
        # 設定 Labelframe (分組框) 樣式
        style.configure('TLabelframe', font=default_font, background=self.ui_bg_color)
        style.configure('TLabelframe.Label', font=default_font, background=self.ui_bg_color)
        
        # 設定 Scrollbar 樣式
        style.configure('TScrollbar', background=self.ui_bg_color, arrowcolor='#000000')

    def center_window(self, width, height):
        self.parent.root.update_idletasks()
        screen_width = self.parent.root.winfo_screenwidth()
        screen_height = self.parent.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.parent.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def init_ui(self):
        # 建立主框架
        self.main_frame = ttk.PanedWindow(self.parent.parent, orient='horizontal', style="TPanedwindow")
        self.main_frame.grid(row=0, column=0, sticky='nsew', padx=self.ui_padding, pady=self.ui_padding)
        
        # 左側面板 (控制區)
        self.left_panel = ttk.Frame(self.main_frame, style="TFrame")
        self.left_panel.grid_columnconfigure(0, weight=1)  # 讓左側面板內容可以水平擴展
        
        # 右側面板 (輸出區)
        self.right_panel = ttk.Frame(self.main_frame, style="TFrame")
        self.right_panel.grid_columnconfigure(0, weight=1)  # 讓右側面板內容可以水平擴展
        self.right_panel.grid_rowconfigure(0, weight=1)    # 讓右側面板內容可以垂直擴展
        
        # 添加面板到 PanedWindow
        self.main_frame.add(self.left_panel, weight=1)
        self.main_frame.add(self.right_panel, weight=3)
        
        # 設定 PanedWindow 的拖動事件
        self.main_frame.bind("<ButtonPress-1>", self.on_pane_drag_start)
        self.main_frame.bind("<ButtonRelease-1>", self.on_pane_drag_end)
        self.main_frame.bind("<B1-Motion>", self.on_pane_position_changed)
        
        # 從配置中恢復面板位置
        pane_position = self.parent.setup.get('Pane_Position', 400)
        try:
            pane_position = int(pane_position)
        except (ValueError, TypeError):
            pane_position = 400
        
        # 設定初始分割位置
        self.parent.root.after(100, lambda: self.main_frame.sashpos(0, pane_position))
        
        # 初始化右側輸出區域
        self.init_right_panel()
        
    def init_right_panel(self):
        """初始化右側輸出面板"""
        # 創建輸出區域框架
        output_frame = ttk.LabelFrame(self.right_panel, text="輸出區域", style="TLabelframe")
        output_frame.grid(row=0, column=0, sticky='nsew', padx=self.ui_padding, pady=self.ui_padding)
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)
        
        # 創建輸出文本框
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            wrap=tk.WORD, 
            font=(self.ui_font, self.ui_font_size),
            background='white',
            foreground='black'
        )
        self.output_text.grid(row=0, column=0, sticky='nsew', padx=self.ui_padding, pady=self.ui_padding)
        
        # 配置文本標籤
        self.output_text.tag_configure('red', foreground='red')
        self.output_text.tag_configure('blue', foreground='blue')
        self.output_text.tag_configure('green', foreground='green')
        self.output_text.tag_configure('orange', foreground='orange')
        self.output_text.tag_configure('purple', foreground='purple')
        self.output_text.tag_configure('bold', font=(self.ui_font, self.ui_font_size, 'bold'))
        
        # 添加右鍵選單
        self.output_text.bind("<Button-3>", self.show_output_context_menu)
        
        # 創建控制按鈕區域
        control_frame = ttk.Frame(output_frame, style="TFrame")
        control_frame.grid(row=1, column=0, sticky='ew', padx=self.ui_padding, pady=self.ui_padding)
        
        # 添加清空按鈕
        self.btn_clear = ttk.Button(
            control_frame, 
            text="清空輸出", 
            command=lambda: self.output_text.delete(1.0, tk.END),
            style="TButton"
        )
        self.btn_clear.pack(side=tk.LEFT, padx=self.ui_padding)
        
        # 添加複製按鈕
        self.btn_copy = ttk.Button(
            control_frame, 
            text="複製全部", 
            command=self.copy_selected_text,
            style="TButton"
        )
        self.btn_copy.pack(side=tk.LEFT, padx=self.ui_padding)

    def show_output_context_menu(self, event):
        """顯示輸出區域的右鍵選單"""
        context_menu = tk.Menu(self.parent.root, tearoff=0)
        context_menu.add_command(label="複製", command=self.copy_selected_text)
        context_menu.add_command(label="全選", command=self.select_all_text)
        context_menu.add_command(label="清空", command=lambda: self.output_text.delete(1.0, tk.END))
        context_menu.tk_popup(event.x_root, event.y_root)

    def copy_selected_text(self):
        """複製選中的文字"""
        try:
            selected_text = self.output_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.parent.root.clipboard_clear()
            self.parent.root.clipboard_append(selected_text)
        except tk.TclError:
            # 如果沒有選中文字，則複製全部
            all_text = self.output_text.get(1.0, tk.END)
            self.parent.root.clipboard_clear()
            self.parent.root.clipboard_append(all_text)

    def select_all_text(self):
        """全選文字"""
        self.output_text.tag_add(tk.SEL, "1.0", tk.END)
        self.output_text.mark_set(tk.INSERT, "1.0")
        self.output_text.see(tk.INSERT)
        return 'break'

    def on_window_resize(self, event):


        # 只在主視窗且尺寸真的有變時記錄


        if event.widget == self.parent.root:


            new_size = (self.parent.root.winfo_width(), self.parent.root.winfo_height())


            if new_size != self.last_size and new_size[0] > 100 and new_size[1] > 100:


                self.last_size = new_size


                print(f"[DEBUG] 視窗大小變更為: {new_size}")


                # 更新設定中的視窗大小


                self.parent.setup['Window_Width'] = str(new_size[0])


                self.parent.setup['Window_Height'] = str(new_size[1])





    def on_pane_position_changed(self, event):
        """當分割位置變更時儲存位置"""
        try:
            # 獲取當前分割位置
            sash_position = self.main_frame.sashpos(0)
            
            # 如果位置有效（大於0），則保存到設定
            if sash_position > 0:
                # 更新內存中的設定
                self.parent.setup['Pane_Sash_Position'] = str(sash_position)
                print(f"[DEBUG] 分割位置已更新: {sash_position}")
                
                # 立即保存到設定檔
                try:
                    from config_core import load_setup, save_setup
                    full_setup = load_setup()
                    if 'DUT_Control' not in full_setup:
                        full_setup['DUT_Control'] = {}
                    full_setup['DUT_Control']['Pane_Sash_Position'] = str(sash_position)
                    save_setup(full_setup)
                    print(f"[DEBUG] 分割位置已保存到設定檔: {sash_position}")
                except Exception as e:
                    print(f"[ERROR] 保存分割位置到設定檔時發生錯誤: {e}")
        except Exception as e:
            print(f"[ERROR] 更新分割位置時發生錯誤: {e}")
            import traceback
            traceback.print_exc()





    def restore_pane_position(self):
        """恢復上次保存的分割位置"""
        try:
            # 從設定中獲取分割位置
            sash_position = self.parent.setup.get('Pane_Sash_Position', '400')
            
            # 確保是整數
            if sash_position and sash_position.isdigit():
                sash_position = int(sash_position)
                
                # 獲取當前窗口寬度
                window_width = self.parent.root.winfo_width()
                
                # 確保分割位置在合理範圍內 (10% ~ 90% 窗口寬度)
                min_pos = int(window_width * 0.1)
                max_pos = int(window_width * 0.9)
                
                if sash_position < min_pos:
                    sash_position = min_pos
                elif sash_position > max_pos:
                    sash_position = max_pos
                
                # 設置分割位置
                self.main_frame.update_idletasks()  # 確保UI元素已經完成佈局
                self.main_frame.sashpos(0, sash_position)
                print(f"[DEBUG] 已恢復分割位置: {sash_position}, 窗口寬度: {window_width}")
                
                # 再次確認分割位置是否設置成功
                actual_pos = self.main_frame.sashpos(0)
                if actual_pos != sash_position:
                    print(f"[WARNING] 分割位置設置不成功，嘗試再次設置。預期: {sash_position}, 實際: {actual_pos}")
                    # 延遲500毫秒後再次嘗試設置
                    self.parent.root.after(500, lambda: self.main_frame.sashpos(0, sash_position))
            else:
                print(f"[DEBUG] 無效的分割位置值: {sash_position}，使用預設值")
                # 使用預設值 (窗口寬度的40%)
                window_width = self.parent.root.winfo_width()
                default_pos = int(window_width * 0.4)
                self.main_frame.sashpos(0, default_pos)
                
        except Exception as e:
            print(f"[ERROR] 恢復分割位置時發生錯誤: {e}")
            import traceback
            traceback.print_exc()





    def show_notification(self, message, color="red", duration=5000, callback=None):


        """在倒數計時標籤顯示通知訊息"""


        try:


            if hasattr(self, 'label_countdown'):


                # 保存原來的顏色


                original_fg = self.label_countdown.cget('fg')


                # 設置新的顏色和訊息


                self.label_countdown.config(fg=color, text=message)


                # 設定計時器，在指定時間後恢復原來的顏色和清空訊息


                self.parent.root.after(duration, lambda: self._restore_after_notification(original_fg, callback))


        except Exception as e:


            print(f"[ERROR] 顯示通知時發生錯誤: {e}")





    def _restore_after_notification(self, original_fg, callback=None):


        """恢復通知標籤的原始狀態"""


        if hasattr(self, 'label_countdown'):


            self.label_countdown.config(fg=original_fg, text='')


        if callback:


            callback()





    def show_system_status(self):
        """顯示系統狀態（COM口、超時設定、分類）"""
        try:
            if hasattr(self, 'label_countdown') and hasattr(self.parent, 'setup'):
                # 獲取COM口設定
                com_port = self.parent.setup.get('Serial_COM_Port', 'N/A')
                
                # 獲取當前選中的分類及該分類下的指令數量
                section = "全部指令"
                cmd_count = 0
                
                if hasattr(self, 'section_var') and hasattr(self, 'sections'):
                    section = self.section_var.get()
                
                # 獲取指令數量
                if hasattr(self.parent, 'handlers') and hasattr(self.parent.handlers, 'commands'):
                    cmd_count = len(self.parent.handlers.commands.get(section, {}))
                
                # 獲取超時設定
                timeout = self.parent.setup.get('Command_Timeout_Seconds', '30')
                
                # 構建狀態訊息
                status_message = get_notification_text("system_status", com_port, section, cmd_count, timeout)
                
                # 顯示狀態訊息
                self.show_notification(status_message, "blue", 10000)
        except Exception as e:
            print(f"[ERROR] 顯示系統狀態時發生錯誤: {e}")
            import traceback
            traceback.print_exc()