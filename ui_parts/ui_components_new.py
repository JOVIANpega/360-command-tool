import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import sys
import json

# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from config import list_com_ports, save_setup, GUIDE_FILE, COMMAND_FILE

class UIComponents:
    def __init__(self, parent):
        self.parent = parent
        self.init_ui()
        # 讀取 setup.txt 的寬高
        width = int(self.parent.setup.get('WinWidth', 800))
        height = int(self.parent.setup.get('WinHeight', 600))
        # 視窗最大化
        try:
            self.parent.root.state('zoomed')  # Windows
        except Exception:
            self.parent.root.attributes('-zoomed', True)  # Linux
        self.last_size = (width, height)
        self.parent.root.bind('<Configure>', self.on_window_resize)
        # 綁定 Enter 鍵執行指令
        self.parent.root.bind('<Return>', lambda e: self.parent.handlers.on_execute())

    def init_output_components(self):
        try:
            # 文字輸出區域
            self.text_output = scrolledtext.ScrolledText(
                self.right_panel,
                font=('Consolas', int(self.parent.setup.get('ContentFontSize', '12'))),
                bg='white', fg='black', insertbackground='black', wrap='none'
            )
            self.text_output.grid(row=0, column=0, sticky='nsew')
            
            # 設定文字標籤
            self.text_output.tag_configure("success", foreground="green")
            self.text_output.tag_configure("error", foreground="red")
            self.text_output.tag_configure("send", foreground="#0056d6")
            
            # 進度條框架
            progress_frame = ttk.Frame(self.right_panel)
            progress_frame.grid(row=1, column=0, sticky='ew', pady=5)
            progress_frame.columnconfigure(0, weight=1)

            # 進度條
            self.progress = ttk.Progressbar(
                progress_frame,
                mode='determinate',
                style="gray.Horizontal.TProgressbar"
            )
            self.progress.grid(row=0, column=0, sticky='ew')
            self.progress['value'] = 0
            
            # 倒數計時標籤
            self.label_countdown = ttk.Label(
                progress_frame,
                text='',
                style="TLabel",
                font=("Consolas", 18, "bold")
            )
            self.label_countdown.grid(row=0, column=1, padx=10)
            
            # 配置 grid 權重
            self.right_panel.rowconfigure(0, weight=1)
            self.right_panel.rowconfigure(1, weight=0)
            self.right_panel.columnconfigure(0, weight=1)
            
        except Exception as e:
            print(f"初始化輸出組件時發生錯誤: {e}")
            raise 