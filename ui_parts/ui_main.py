import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
from datetime import datetime

# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from config import load_setup, save_setup, list_com_ports, GUIDE_FILE, COMMAND_FILE, load_commands

# 檢查 command.txt
try:
    commands = load_commands()
except Exception as e:
    messagebox.showerror('錯誤', str(e))
    sys.exit(1)

from serial_worker import SerialWorker
from ui_parts.ui_components import UIComponents
from ui_parts.ui_handlers import UIHandlers

class TabManager:
    def __init__(self, root):
        self.root = root
        
        # 配置根窗口的 grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # 初始化全局樣式
        self.init_global_styles()
        
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        # 創建分頁
        self.dut_frame = ttk.Frame(self.notebook, style='Main.TFrame')
        self.fixture_frame = ttk.Frame(self.notebook, style='Main.TFrame')
        
        # 配置分頁的 grid
        self.dut_frame.grid_rowconfigure(0, weight=1)
        self.dut_frame.grid_columnconfigure(0, weight=1)
        self.fixture_frame.grid_rowconfigure(0, weight=1)
        self.fixture_frame.grid_columnconfigure(0, weight=1)
        
        # 添加分頁到 notebook
        self.notebook.add(self.dut_frame, text='DUT 控制')
        self.notebook.add(self.fixture_frame, text='治具控制')
        
        # 設置分頁切換事件
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        
        # 初始化分頁內容
        self.init_dut_tab()
        self.init_fixture_tab()
    
    def init_global_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Main.TFrame', background='white')
        style.configure('TNotebook', background='white')
        # 分頁標籤字體、大小、padding，預設灰底黑字，選取為藍底白字
        style.configure('TNotebook.Tab', font=('Microsoft JhengHei UI', 13, 'bold'), padding=[16, 6], background='#d9d9d9', foreground='black')
        style.map('TNotebook.Tab',
            background=[('selected', '#2196f3'), ('active', '#0056d6'), ('!active', '#d9d9d9')],
            foreground=[('selected', 'white'), ('active', 'white'), ('!active', 'black')]
        )
        # HANDOVER 分頁綠底白字
        style.element_create('Green.Tab', 'from', 'default')
        style.layout('Green.TNotebook.Tab', style.layout('TNotebook.Tab'))
        style.configure('Green.TNotebook.Tab', background='#1abc1a', foreground='white')
        style.map('Green.TNotebook.Tab',
            background=[('selected', '#1abc1a'), ('active', '#1abc1a'), ('!active', '#d9d9d9')],
            foreground=[('selected', 'white'), ('active', 'white'), ('!active', 'black')]
        )
        # 一般TButton維持灰底黑字hover藍底白字
        style.configure('TButton', font=('Microsoft JhengHei UI', 12), padding=[8, 4])
        style.map('TButton',
            background=[('active', '#003a80'), ('!active', '#f5f5f5')],
            foreground=[('active', 'white'), ('!active', 'black')]
        )
    
    def init_dut_tab(self):
        # 初始化 DUT 控制分頁
        self.dut_ui = SerialUI(self.dut_frame, self.root)
    
    def init_fixture_tab(self):
        # 初始化治具控制分頁
        from FIXTURE.fixture13 import FixtureFrame
        self.fixture_ui = FixtureFrame(self.fixture_frame)
        self.fixture_ui.pack(fill='both', expand=True)
    
    def on_tab_changed(self, event):
        # 獲取當前選中的分頁
        current_tab = self.notebook.select()
        tab_text = self.notebook.tab(current_tab, "text")
        # 先全部設回藍底白字
        for i in range(self.notebook.index('end')):
            self.notebook.tab(i, style='TNotebook.Tab')
        # 根據分頁切換處理資源
        if tab_text == 'DUT 控制':
            self.dut_ui.activate()
        elif tab_text == '治具控制':
            self.fixture_ui.activate()
        elif tab_text == 'HANDOVER':
            self.notebook.tab(current_tab, style='Green.TNotebook.Tab')

    def get_dut_settings(self):
        # 假設 self.dut_frame 內有 SerialUI 或相關元件
        if hasattr(self, 'dut_ui') and hasattr(self.dut_ui, 'get_settings'):
            return self.dut_ui.get_settings()
        # 若無，請根據你的 DUT 分頁元件組合自行組 dict
        return {}

    def get_fixture_settings(self):
        # 假設 self.fixture_frame 內有 FixtureFrame 或相關元件
        if hasattr(self, 'fixture_ui') and hasattr(self.fixture_ui, 'get_settings'):
            return self.fixture_ui.get_settings()
        # 若無，請根據你的 FIXTURE 分頁元件組合自行組 dict
        return {}

class SerialUI:
    def __init__(self, parent, root):
        self.parent = parent
        self.root = root
        self.setup = load_setup()
        
        # 配置父容器的 grid
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        
        # 初始化基本變數
        self.serial_port = None
        self.thread = None
        self.stop_event = threading.Event()
        self.guide_window = None
        self.text_buffer = []
        self.buffer_size = 1000
        self.update_interval = 100
        self.buffer_timer = None

        # 初始化樣式
        self.init_styles()
        
        # 先初始化 handlers
        self.handlers = UIHandlers(self)
        # 再初始化 components
        self.components = UIComponents(self)
        
        # 載入指令
        self.commands_by_section = self.handlers.parse_commands_by_section()
        self.components.update_cmd_list()

        # 載入 EndStrings
        end_strings = self.setup.get('EndStrings', ["root"])
        if isinstance(end_strings, str):
            try:
                end_strings = json.loads(end_strings)
            except Exception:
                end_strings = ["root"]
        self.components.combobox_end['values'] = end_strings

    def init_styles(self):
        style = ttk.Style()
        # 設定進度條樣式
        style.configure("blue.Horizontal.TProgressbar",
                      foreground='blue',
                      background='blue')
        style.configure("gray.Horizontal.TProgressbar",
                      foreground='#d9d9d9',
                      background='#d9d9d9')
        # 設定 Frame 樣式
        style.configure("Main.TFrame",
                      background="white")
        # 設定 Label 樣式
        style.configure("Main.TLabel",
                      background="white",
                      foreground="black")
        # 設定 Labelframe 樣式
        style.configure("Main.TLabelframe",
                      background="white",
                      foreground="black")
        style.configure("Main.TLabelframe.Label",
                      background="white",
                      foreground="black")

    def activate(self):
        """當分頁被選中時調用"""
        # 更新串口列表
        self.components.update_com_ports()
        # 其他激活操作...

    def on_close(self):
        try:
            self.setup['COM'] = self.components.combobox_com.get()
            self.setup['Timeout'] = self.components.entry_timeout.get()
            self.setup['EndString'] = self.components.combobox_end.get()
            save_setup(self.setup)
            if self.stop_event:
                self.stop_event.set()
        except Exception as e:
            messagebox.showerror('錯誤', f'關閉程式時發生錯誤: {e}')

    def get_settings(self):
        # 回傳 DUT 分頁所有設定
        settings = {}
        c = self.components
        settings['COM'] = c.combobox_com.get()
        settings['Timeout'] = c.entry_timeout.get()
        settings['EndString'] = c.combobox_end.get()
        settings['UIFontSize'] = str(c.ui_font_scale.get())
        settings['ContentFontSize'] = str(c.content_font_scale.get())
        settings['Title'] = self.root.title() if hasattr(self.root, 'title') else 'VALO360 指令通'
        try:
            end_strings = list(c.combobox_end['values'])
        except Exception:
            end_strings = ["root"]
        settings['EndStrings'] = end_strings
        settings['Default_IP'] = c.entry_ip.get() if hasattr(c, 'entry_ip') else '192.168.11.143'
        settings['WinWidth'] = str(self.root.winfo_width())
        settings['WinHeight'] = str(self.root.winfo_height())
        settings['LastSection'] = c.section_var.get() if hasattr(c, 'section_var') else '全部指令'
        return settings

# 若有 FixtureFrame 也在這裡加 get_settings
from FIXTURE.fixture13 import FixtureFrame

def fixtureframe_get_settings(self):
    data = {}
    data['COM'] = self.com_port_var.get()
    data['CMD'] = self.command_var.get()
    for cat, var in self.category_vars.items():
        data[cat] = var.get()
    data['FixtureFontSize'] = str(self._fixture_font_size)
    return data
FixtureFrame.get_settings = fixtureframe_get_settings