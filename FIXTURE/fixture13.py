# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import time
import os
import json
import sys

# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 導入配置模組
try:
    from config_utils import resource_path
except ImportError as e:
    print(f"導入 config_utils 模組失敗: {e}")
    print(f"當前路徑: {sys.path}")
    
    # 提供一個簡單的 resource_path 函數作為備用
    def resource_path(relative_path):
        try:
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        except Exception:
            return os.path.join(os.path.abspath("."), relative_path)

SETUP_FILE = resource_path('setup.json')

def load_fixture_setup():
    if os.path.exists(SETUP_FILE):
        with open(SETUP_FILE, 'r', encoding='utf-8') as f:
            try:
                setup = json.load(f)
                return setup.get('Fixture_Control', {})
            except Exception:
                return {}
    return {}

def save_fixture_setup(data):
    # 讀取整個 setup.json，僅更新 Fixture_Control 區塊
    setup = {}
    if os.path.exists(SETUP_FILE):
        try:
            with open(SETUP_FILE, 'r', encoding='utf-8') as f:
                setup = json.load(f)
        except Exception:
            setup = {}
    setup['Fixture_Control'] = data
    with open(SETUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(setup, f, ensure_ascii=False, indent=2)

class FixtureFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setup = load_fixture_setup()
        # 初始化字體大小，預設12，若setup有記錄則用setup
        self._fixture_font_size = int(self.setup.get('Fixture_Font_Size', 12))
        self.init_vars()
        self.init_ui()
        self.refresh_ports()
        self.bind_all('<Destroy>', self.on_close, add='+')
        # 讓 main_frame 撐滿分頁
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        # 初始化後立即套用字體大小
        self.change_fixture_font(0)

    def init_vars(self):
        self.com_port_var = tk.StringVar()
        self.command_var = tk.StringVar()
        self.category_vars = {}
        self.test_items = self.load_test_items()
        # 預設 MB 打勾，若 setup 有記錄則依 setup
        for cat in self.test_items.keys():
            if cat == 'MB':
                self.category_vars[cat] = tk.BooleanVar(value=self.setup.get('Test_Category_MB', True))
            elif cat == 'FUNCTION':
                self.category_vars[cat] = tk.BooleanVar(value=self.setup.get('Test_Category_FUNCTION', False))
            elif cat == '原始的指令':
                self.category_vars[cat] = tk.BooleanVar(value=self.setup.get('Test_Category_Original_Commands', False))
            else:
                self.category_vars[cat] = tk.BooleanVar(value=self.setup.get(cat, False))

    def list_serial_ports(self):
        """列出可用的串口"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def find_default_port(self):
        """尋找包含 CH340 的 COM Port，若無則選擇第一個可用的"""
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "CH340" in port.description:
                return port.device
        return ports[0].device if ports else ""

    def load_test_items(self, filename="Fixture_Command.txt"):
        """從 Fixture_Command.txt 讀取測試項目，返回分類對應的選單內容"""
        # 檢查檔案是否在 FIXTURE 目錄中
        if not os.path.exists(filename):
            fixture_path = os.path.join("FIXTURE", filename)
            if os.path.exists(fixture_path):
                filename = fixture_path
            else:
                messagebox.showerror("錯誤", f"找不到 {filename} 檔案！")
                return {}
        
        categories = {}
        current_category = None
        
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line.endswith(":"):
                    current_category = line[:-1]
                    categories[current_category] = []
                elif current_category and line:
                    # 移除 strip('\"') 因為檔案中已經沒有引號
                    categories[current_category].append(line)
        
        print(f"[DEBUG] 載入的測試類別: {list(categories.keys())}")
        return categories

    def refresh_ports(self):
        """刷新可用的串口列表，並優先還原setup中的COM、CMD等設定"""
        available_ports = self.list_serial_ports()
        self.com_port_dropdown["values"] = available_ports
        # 優先還原 setup 裡的 COM
        setup_com = self.setup.get('Fixture_COM_Port')
        if setup_com in available_ports:
            self.com_port_var.set(setup_com)
            self.fixture_port_label.config(text=f"Fixture Com port : {setup_com}")
        elif available_ports:
            default_port = self.find_default_port()
            self.com_port_var.set(default_port)
            self.fixture_port_label.config(text=f"Fixture Com port : {default_port}")
        # 優先還原 setup 裡的 CMD
        setup_cmd = self.setup.get('Current_Command')
        if setup_cmd and hasattr(self, 'command_dropdown'):
            values = self.command_dropdown["values"]
            if setup_cmd in values:
                self.command_var.set(setup_cmd)
                self.command_dropdown.set(setup_cmd)

    def send_command(self):
        """發送指令到串口"""
        selected_port = self.com_port_var.get()
        selected_command = self.command_var.get()

        if not selected_port:
            messagebox.showerror("錯誤", "請選擇或輸入串口！")
            return

        if not selected_command:
            messagebox.showerror("錯誤", "請選擇指令！")
            return

        try:
            with serial.Serial(selected_port, baudrate=9600, timeout=1) as ser:
                ser.write((selected_command.split(" - ")[0] + '\r\n').encode())
                self.flash_led()
        except serial.SerialException as e:
            messagebox.showerror("錯誤", f"無法打開串口: {e}")

    def flash_led(self):
        """閃爍 LED 燈"""
        self.led_canvas.itemconfig(self.led_indicator, fill="green")
        self.update()
        time.sleep(0.5)
        self.led_canvas.itemconfig(self.led_indicator, fill="black")
        self.update()

    def update_commands(self, selected_category):
        """根據選擇的分類更新指令選單"""
        for cat, var in self.category_vars.items():
            if cat != selected_category:
                var.set(False)
        
        self.command_dropdown["values"] = self.test_items.get(selected_category, [])
        self.command_dropdown.set("")

    def on_category_checked(self, category):
        self.update_commands(category)
        # 若該類別被打勾，combobox自動顯示第一筆
        if self.category_vars[category].get():
            cmds = self.test_items.get(category, [])
            if cmds:
                self.command_dropdown.set(cmds[0])

    def on_close(self, event=None):
        # 儲存所有設定
        data = {}
        data['Fixture_COM_Port'] = self.com_port_var.get()
        data['Current_Command'] = self.command_var.get()
        for cat, var in self.category_vars.items():
            if cat == 'MB':
                data['Test_Category_MB'] = var.get()
            elif cat == 'FUNCTION':
                data['Test_Category_FUNCTION'] = var.get()
            elif cat == '原始的指令':
                data['Test_Category_Original_Commands'] = var.get()
            else:
                data[cat] = var.get()
        # 儲存字體大小
        data['Fixture_Font_Size'] = str(self._fixture_font_size)
        save_fixture_setup(data)

    def init_ui(self):
        # 外框（由 Frame 改為 Labelframe，名稱為治具控制區）
        outer_frame = ttk.LabelFrame(self, text="治具控制區", padding=16, style="Main.TLabelframe")
        outer_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        outer_frame.grid_rowconfigure(2, weight=1)
        outer_frame.grid_columnconfigure(0, weight=1)
        # ====== 標題與說明 ======
        title_label = tk.Label(outer_frame, text="治具操作區", font=("Microsoft JhengHei UI", 15, "bold"), fg="#222", bg='white', anchor='w')
        title_label.grid(row=0, column=0, sticky='w', padx=(0, 0), pady=(0, 2))
        import json
        try:
            with open('setup.json', 'r', encoding='utf-8') as f:
                setup = json.load(f)
            desc = setup.get('fixture_description', '此分頁為制具控制')
        except Exception:
            desc = '此分頁為制具控制'
        desc_label = tk.Label(
            outer_frame,
            text=desc,
            fg='black',
            font=("Microsoft JhengHei UI", 12),
            wraplength=700,
            anchor='w',
            justify='left',
            bg='#ffe066'  # 黃底
        )
        desc_label.grid(row=1, column=0, sticky='ew', padx=(0, 0), pady=(0, 10))
        # ====== 字體縮放控制 ======
        font_ctrl_frame = tk.Frame(outer_frame, bg='white')
        font_ctrl_frame.grid(row=0, column=1, sticky="ne", padx=(0, 0), pady=(0, 0))
        btn_minus = tk.Button(font_ctrl_frame, text="－", width=2, command=lambda: self.change_fixture_font(-1))
        btn_minus.pack(side="left", padx=2)
        btn_plus = tk.Button(font_ctrl_frame, text="＋", width=2, command=lambda: self.change_fixture_font(1))
        btn_plus.pack(side="left", padx=2)
        # ====== 主框架 ======
        main_frame = tk.Frame(outer_frame, bg='white')
        main_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=0)
        main_frame.grid_columnconfigure(1, weight=0)
        main_frame.grid_columnconfigure(2, weight=0)
        main_frame.grid_columnconfigure(3, weight=0)
        # 第0行: 測試類別（橫向排列，放在最上方）
        category_label = tk.Label(main_frame, text="選擇測試類別:", font=("Microsoft JhengHei UI", 12), fg="#222", bg='white')
        category_label.grid(row=0, column=0, sticky="w", pady=(0, 4))
        category_frame = tk.Frame(main_frame, bg='white')
        category_frame.grid(row=0, column=1, columnspan=4, sticky="w", pady=(0, 10))
        for i, category in enumerate(self.test_items.keys()):
            chk = tk.Checkbutton(category_frame, text=category, variable=self.category_vars[category], command=lambda c=category: self.on_category_checked(c), font=("Microsoft JhengHei UI", 12), bg='white')
            chk.grid(row=0, column=i, padx=8, sticky="w")
        # 第一行: 串口、刷新、LED、選擇指令
        com_port_label = tk.Label(main_frame, text="選擇或輸入治具串口:", font=("Microsoft JhengHei UI", 12), fg="#222", bg='white')
        com_port_label.grid(row=1, column=0, sticky="w", pady=(0, 6))
        self.com_port_dropdown = ttk.Combobox(main_frame, textvariable=self.com_port_var, font=("Microsoft JhengHei UI", 12), width=18)
        self.com_port_dropdown.grid(row=1, column=1, sticky="w", pady=(0, 6), padx=(0, 4))
        refresh_led_frame = tk.Frame(main_frame, bg='white')
        refresh_led_frame.grid(row=1, column=2, padx=2, sticky="w")
        refresh_button = tk.Button(refresh_led_frame, text="刷新", command=self.refresh_ports, font=("Microsoft JhengHei UI", 12), width=7)
        refresh_button.pack(side="left")
        self.led_canvas = tk.Canvas(refresh_led_frame, width=36, height=36, bg="white", highlightthickness=0)
        self.led_canvas.pack(side="left", padx=(8, 0))
        self.led_indicator = self.led_canvas.create_oval(6, 6, 30, 30, fill="black")
        command_label = tk.Label(main_frame, text="選擇指令:", font=("Microsoft JhengHei UI", 12), fg="#222", bg='white')
        command_label.grid(row=1, column=3, sticky="w", padx=(16, 0), pady=(0, 6))
        self.command_dropdown = ttk.Combobox(main_frame, textvariable=self.command_var, state="readonly", font=("Microsoft JhengHei UI", 13), width=22)
        self.command_dropdown.grid(row=1, column=4, sticky="w", pady=(0, 6), padx=(0, 4))
        # 第二行: Fixture port label
        self.fixture_port_label = tk.Label(main_frame, text=f"Fixture Com port : {self.find_default_port()}", font=("Microsoft JhengHei UI", 12, "bold"), fg="#0056d6", bg='white')
        self.fixture_port_label.grid(row=2, column=0, columnspan=5, sticky="w", pady=(0, 10))
        # 發送指令按鈕置中
        button_frame = tk.Frame(main_frame, bg='white')
        button_frame.grid(row=3, column=0, columnspan=5, pady=(10, 0), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        self.send_button = tk.Button(
            button_frame, text="發送治具控制指令", command=self.send_command,
            font=("Microsoft JhengHei UI", 16, "bold"), width=30, height=2,
            bg="#cccccc", fg="black", relief="groove", borderwidth=2, highlightthickness=0
        )
        self.send_button.grid(row=0, column=0, sticky="ew")
        self.send_button.bind("<Enter>", lambda e: self.send_button.config(bg="#4caf50", fg="white"))
        self.send_button.bind("<Leave>", lambda e: self.send_button.config(bg="#cccccc", fg="black"))
        main_frame.grid_rowconfigure(4, weight=1)

    def change_fixture_font(self, delta):
        # 控制治具控制區所有元件字體大小
        min_size, max_size = 8, 20
        self._fixture_font_size = max(min(self._fixture_font_size + delta, max_size), min_size)
        font = ("Microsoft JhengHei UI", self._fixture_font_size)
        # 遍歷所有元件
        def update_font(widget):
            try:
                widget.configure(font=font)
            except Exception:
                pass
            for child in widget.winfo_children():
                update_font(child)
        update_font(self)
        # 讀取最新設定，確保不會覆蓋其他欄位
        latest = load_fixture_setup()
        latest.update(self.setup)
        latest['Fixture_Font_Size'] = str(self._fixture_font_size)
        self.setup = latest
        save_fixture_setup(self.setup)
