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
    # 導入 ToolTip 管理器
    from ui_parts.tooltip import ToolTipManager
    from config_core import load_setup, save_setup
except ImportError as e:
    print(f"導入模組失敗: {e}")
    print(f"當前路徑: {sys.path}")
    
    # 提供一個簡單的 resource_path 函數作為備用
    def resource_path(relative_path):
        try:
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        except Exception as e:
            print(f"resource_path 錯誤: {e}")
            return relative_path
    
    # 提供一個簡單的 ToolTipManager 類別作為備用
    class ToolTipManager:
        def __init__(self, root):
            self.enabled = True
            self.root = root
        
        def add_tooltip(self, widget, text):
            pass

    # 備用的設定載入/儲存函數
    def load_setup():
        try:
            setup_path = resource_path("setup.json")
            if os.path.exists(setup_path):
                with open(setup_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"載入設定失敗: {e}")
        return {}
    
    def local_save_setup(setup):
        try:
            setup_path = resource_path("setup.json")
            with open(setup_path, 'w', encoding='utf-8') as f:
                json.dump(setup, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存設定失敗: {e}")

class FixtureControlWindow:
    def __init__(self, root):
        self.root = root
        
        # 只有在根視窗是 Tk 實例時才設定視窗屬性
        if isinstance(root, tk.Tk):
            self.root.title("制具控制測試")
            self.root.geometry("800x600")
        
        # 初始化變數
        self.setup_variables()
        
        # 載入設定
        self.load_settings()
        
        # 載入指令數據
        self.load_commands()
        
        # 建立界面
        self.create_interface()
        
        # 初始化 ToolTip
        try:
            # 使用全域 tooltip 管理器實例
            from ui_parts.tooltip import get_tooltip_manager
            self.tooltip_manager = get_tooltip_manager()
        except:
            self.tooltip_manager = None
        
        # 設定 ToolTips
        self.setup_tooltips()

    def setup_variables(self):
        """初始化變數"""
        self.serial_connection = None
        self.commands = {
            'FUNCTION': [],
            'MB': [], 
            '原始群元指令': [],
            '4CAM_stitching的指令': []
        }
        self.description_text = ""
        
        # 導入統一設定管理器
        try:
            from ui_parts.shared_config import get_shared_config
            self.shared_config = get_shared_config()
        except ImportError:
            self.shared_config = None
            print("[WARNING] 無法載入統一設定管理器，使用本地變數")
        
        # 測試類別變數 - 如果有統一管理器則使用統一變數
        if self.shared_config:
            self.test_category_vars = {
                'FUNCTION': self.shared_config.get_var('fixture_test_function'),
                'MB': self.shared_config.get_var('fixture_test_mb'),
                '原始群元指令': self.shared_config.get_var('fixture_test_original'),
                '4CAM_stitching的指令': tk.BooleanVar()  # 新增4CAM_stitching的指令變數
            }
        else:
            self.test_category_vars = {
                'FUNCTION': tk.BooleanVar(),
                'MB': tk.BooleanVar(),
                '原始群元指令': tk.BooleanVar(),
                '4CAM_stitching的指令': tk.BooleanVar()  # 新增4CAM_stitching的指令變數
            }
            # 預設選擇FUNCTION
            self.test_category_vars['FUNCTION'].set(True)
        
        # 確定當前選擇的類別
        self.current_category = 'FUNCTION'
        for category, var in self.test_category_vars.items():
            if var.get():
                self.current_category = category
                break
        
        # COM Port 變數 - 使用統一管理器的變數
        if self.shared_config:
            self.com_port_var = self.shared_config.get_var('fixture_com_port')
        else:
            self.com_port_var = tk.StringVar(value="COM5")
        
        # 串列設定變數 - 使用統一管理器的變數
        if self.shared_config:
            self.baudrate_var = self.shared_config.get_var('fixture_baudrate')
            self.bytesize_var = self.shared_config.get_var('fixture_bytesize')
            self.stopbits_var = self.shared_config.get_var('fixture_stopbits')
            self.parity_var = self.shared_config.get_var('fixture_parity')
            self.timeout_var = self.shared_config.get_var('fixture_timeout')
        else:
            self.baudrate_var = tk.StringVar(value="9600")
            self.bytesize_var = tk.StringVar(value="8")
            self.stopbits_var = tk.StringVar(value="1")
            self.parity_var = tk.StringVar(value="None")
            self.timeout_var = tk.StringVar(value="1.0")

    def load_settings(self):
        """載入設定檔"""
        try:
            settings = load_setup()
            
            # 載入制具控制設定
            fixture_settings = settings.get('Fixture_Control', {})
            
            # 載入 COM Port 設定
            self.com_port_var.set(fixture_settings.get('Fixture_COM_Port', 'COM5'))
            
            # 載入測試類別設定
            self.test_category_vars['FUNCTION'].set(
                fixture_settings.get('Test_Category_FUNCTION', True))
            self.test_category_vars['MB'].set(
                fixture_settings.get('Test_Category_MB', False))
            self.test_category_vars['原始群元指令'].set(
                fixture_settings.get('Test_Category_Original_Commands', False))
            self.test_category_vars['4CAM_stitching的指令'].set(
                fixture_settings.get('Test_Category_4CAM_stitching', False))
            
            # 確定當前選擇的類別
            for category, var in self.test_category_vars.items():
                if var.get():
                    self.current_category = category
                    break
            
            # 載入串列設定
            serial_settings = fixture_settings.get('Serial_Settings', {})
            self.baudrate_var.set(serial_settings.get('Baudrate', '9600'))
            self.bytesize_var.set(serial_settings.get('Bytesize', '8'))
            self.stopbits_var.set(serial_settings.get('Stopbits', '1'))
            self.parity_var.set(serial_settings.get('Parity', 'None'))
            self.timeout_var.set(serial_settings.get('Timeout', '1.0'))
            
            # 載入字體大小設定 - 與DUT控制TAB聯動
            dut_settings = settings.get('DUT_Control', {})
            ui_font_size = dut_settings.get('UI_Font_Size', '12')
            try:
                self.font_size = int(ui_font_size)
            except (ValueError, TypeError):
                self.font_size = 12
            
            print(f"[DEBUG] 治具控制TAB載入字體大小: {self.font_size} (來自DUT控制TAB的UI_Font_Size)")
            
        except Exception as e:
            print(f"載入設定時發生錯誤: {e}")
            self.font_size = 12

    def load_commands(self):
        """載入指令檔案"""
        try:
            command_file = resource_path("Command_TABLE/Fixture_Command.txt")
            if not os.path.exists(command_file):
                messagebox.showerror("錯誤", f"找不到指令檔案: {command_file}")
                return
                
            with open(command_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 解析說明文字
            lines = content.split('\n')
            for line in lines:
                if line.startswith('說明文='):
                    self.description_text = line[3:].strip()  # 移除 '說明文=' 
                    break
                    
            # 解析各個區段
            sections = content.split('\n\n')
            current_section = None
            
            for section in sections:
                lines = section.strip().split('\n')
                if not lines:
                    continue
                    
                if lines[0].endswith(':'):
                    current_section = lines[0][:-1]  # 移除冒號
                    if current_section in self.commands:
                        # 解析指令行
                        for line in lines[1:]:
                            if line.strip():
                                # 所有指令都使用標準格式 (指令 - 描述)
                                if ' - ' in line:
                                    code, desc = line.split(' - ', 1)
                                    self.commands[current_section].append({
                                        'code': code.strip(),
                                        'description': desc.strip()
                                    })
                                
        except Exception as e:
            messagebox.showerror("錯誤", f"載入指令檔案時發生錯誤: {e}")

    def create_interface(self):
        """建立使用者界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 說明區域 (置頂)
        self.create_description_area(main_frame)
        
        # 控制區域 (整合測試類別選擇與指令操作)
        self.create_control_area(main_frame)
        
        # 串列參數顯示區域
        self.create_serial_info_area(main_frame)
        
        # 執行結果區域  
        self.create_result_area(main_frame)

    def create_description_area(self, parent):
        """建立說明區域"""
        desc_frame = ttk.LabelFrame(parent, text="制具說明", padding="5")
        desc_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 說明文字標籤 (不可編輯)
        self.desc_label = tk.Label(
            desc_frame, 
            text=self.description_text if self.description_text else "載入說明文字中...",
            font=("微軟正黑體", self.font_size),
            justify=tk.LEFT,
            anchor='w',
            wraplength=750,
            bg='#f8f9fa',
            relief=tk.SUNKEN,
            bd=1,
            padx=10,
            pady=5
        )
        self.desc_label.pack(fill=tk.X)

    def create_control_area(self, parent):
        """建立控制區域 (整合測試類別與指令選擇)"""
        control_frame = ttk.LabelFrame(parent, text="指令控制", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第一行：測試類別選擇
        category_frame = ttk.Frame(control_frame)
        category_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(category_frame, text="測試類別:", font=("微軟正黑體", self.font_size)).pack(side=tk.LEFT)
        
        # 建立類別勾選框 (具有單選邏輯)
        for i, (category, var) in enumerate(self.test_category_vars.items()):
            checkbox = ttk.Checkbutton(
                category_frame, 
                text=category,
                variable=var,
                command=lambda cat=category: self.on_category_changed(cat)
            )
            checkbox.pack(side=tk.LEFT, padx=(10, 0))
        
        # 添加重新載入按鈕
        self.reload_btn = ttk.Button(
            category_frame,
            text="重新載入指令",
            command=self.reload_commands,
            style="Accent.TButton"
        )
        self.reload_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 第二行：COM Port 與指令選擇
        command_frame = ttk.Frame(control_frame)
        command_frame.pack(fill=tk.X, pady=(0, 10))
        
        # COM Port 選擇
        tk.Label(command_frame, text="COM埠:", font=("微軟正黑體", self.font_size)).pack(side=tk.LEFT)
        
        # 取得可用的 COM 埠
        available_ports = self.get_available_com_ports()
        self.com_combobox = ttk.Combobox(
            command_frame,
            textvariable=self.com_port_var,
            values=available_ports,
            state="readonly",
            width=10
        )
        self.com_combobox.pack(side=tk.LEFT, padx=(10, 20))
        self.com_combobox.bind('<<ComboboxSelected>>', self.on_com_port_changed)
        
        # 指令選擇
        tk.Label(command_frame, text="選擇指令:", font=("微軟正黑體", self.font_size)).pack(side=tk.LEFT)
        
        # 指令選擇下拉選單 (約20字元寬度)
        self.command_combobox = ttk.Combobox(
            command_frame, 
            state="readonly",
            width=20
        )
        self.command_combobox.pack(side=tk.LEFT, padx=(10, 5))
        self.command_combobox.bind('<<ComboboxSelected>>', self.on_command_selected)
        
        # 第三行：治具設定區塊 (從設定頁面移入)
        self.create_fixture_settings_area(control_frame)
        
        # 執行指令按鈕 (緊接著Combobox)
        self.execute_btn = ttk.Button(
            command_frame,
            text="執行指令",
            command=self.on_execute_command,
            style="Accent.TButton"
        )
        self.execute_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # 第三行：送出指令顯示與清除
        output_frame = ttk.Frame(control_frame)
        output_frame.pack(fill=tk.X)
        
        tk.Label(output_frame, text="送出指令:", font=("微軟正黑體", self.font_size)).pack(side=tk.LEFT)
        
        # 送出指令顯示欄位 (約20字元寬度)
        self.sent_command_var = tk.StringVar()
        self.sent_command_entry = ttk.Entry(
            output_frame,
            textvariable=self.sent_command_var,
            state="readonly",
            width=20
        )
        self.sent_command_entry.pack(side=tk.LEFT, padx=(10, 5))
        
        # 清除結果按鈕 (緊接著Entry)
        self.clear_btn = ttk.Button(
            output_frame,
            text="清除結果",
            command=self.on_clear_results
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # 更新指令列表
        self.update_command_list()

    def create_fixture_settings_area(self, parent):
        """建立治具設定區塊 (從設定頁面移入)"""
        settings_frame = ttk.LabelFrame(parent, text="治具設定", padding="5")
        settings_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 建立左右兩欄的容器
        content_frame = ttk.Frame(settings_frame)
        content_frame.pack(fill=tk.X)
        
        # 左欄：基本設定
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 字體大小
        font_frame = ttk.Frame(left_frame)
        font_frame.pack(fill=tk.X, pady=2)
        tk.Label(font_frame, text="字體大小:", font=("微軟正黑體", 12)).pack(side=tk.LEFT, padx=(0, 5))
        self.fixture_font_var = tk.StringVar()
        self.fixture_font_spinbox = ttk.Spinbox(
            font_frame, 
            textvariable=self.fixture_font_var,
            from_=8, to=24, width=8,
            command=self.on_fixture_font_changed
        )
        self.fixture_font_spinbox.pack(side=tk.LEFT)
        self.fixture_font_spinbox.bind('<Return>', self.on_fixture_font_changed)
        self.fixture_font_spinbox.bind('<FocusOut>', self.on_fixture_font_changed)
        
        # 右欄：串列設定
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 串列設定標題
        tk.Label(right_frame, text="串列埠設定:", font=("微軟正黑體", 12, "bold")).pack(anchor='w', pady=(0, 5))
        
        # 建立2x3的網格來放置串列設定
        serial_grid = ttk.Frame(right_frame)
        serial_grid.pack(fill=tk.X)
        
        # 第一行：波特率和資料位元
        row1_frame = ttk.Frame(serial_grid)
        row1_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(row1_frame, text="波特率:", font=("微軟正黑體", 12)).pack(side=tk.LEFT)
        self.baudrate_combo = ttk.Combobox(
            row1_frame,
            textvariable=self.baudrate_var,
            values=["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"],
            width=8, state="readonly"
        )
        self.baudrate_combo.pack(side=tk.LEFT, padx=(5, 15))
        
        tk.Label(row1_frame, text="資料位元:", font=("微軟正黑體", 12)).pack(side=tk.LEFT)
        self.bytesize_combo = ttk.Combobox(
            row1_frame,
            textvariable=self.bytesize_var,
            values=["5", "6", "7", "8"],
            width=6, state="readonly"
        )
        self.bytesize_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 第二行：停止位元和奇偶校驗
        row2_frame = ttk.Frame(serial_grid)
        row2_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(row2_frame, text="停止位元:", font=("微軟正黑體", 12)).pack(side=tk.LEFT)
        self.stopbits_combo = ttk.Combobox(
            row2_frame,
            textvariable=self.stopbits_var,
            values=["1", "1.5", "2"],
            width=6, state="readonly"
        )
        self.stopbits_combo.pack(side=tk.LEFT, padx=(5, 15))
        
        tk.Label(row2_frame, text="奇偶校驗:", font=("微軟正黑體", 12)).pack(side=tk.LEFT)
        self.parity_combo = ttk.Combobox(
            row2_frame,
            textvariable=self.parity_var,
            values=["None", "Even", "Odd", "Mark", "Space"],
            width=8, state="readonly"
        )
        self.parity_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 第三行：超時時間
        row3_frame = ttk.Frame(serial_grid)
        row3_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(row3_frame, text="超時時間(秒):", font=("微軟正黑體", 12)).pack(side=tk.LEFT)
        self.timeout_entry = ttk.Entry(
            row3_frame,
            textvariable=self.timeout_var,
            width=8
        )
        self.timeout_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # 綁定變更事件
        for combo in [self.baudrate_combo, self.bytesize_combo, self.stopbits_combo, self.parity_combo]:
            combo.bind('<<ComboboxSelected>>', self.on_serial_setting_changed)
        self.timeout_entry.bind('<FocusOut>', self.on_serial_setting_changed)
        self.timeout_entry.bind('<Return>', self.on_serial_setting_changed)
        
        # 初始化設定值
        self.load_settings_to_fixtures()

    def load_settings_to_fixtures(self):
        """將設定載入到治具設定區塊"""
        try:
            settings = load_setup()
            fixture_settings = settings.get('Fixture_Control', {})
            
            # 載入字體大小
            font_size = '12'
            self.fixture_font_var.set(font_size)
            
            # 載入串列設定
            serial_settings = fixture_settings.get('Serial_Settings', {})
            self.baudrate_var.set(serial_settings.get('Baudrate', '9600'))
            self.bytesize_var.set(serial_settings.get('Bytesize', '8'))
            self.stopbits_var.set(serial_settings.get('Stopbits', '1'))
            self.parity_var.set(serial_settings.get('Parity', 'None'))
            self.timeout_var.set(serial_settings.get('Timeout', '1.0'))
            
        except Exception as e:
            print(f"載入治具設定時發生錯誤: {e}")

    def on_fixture_font_changed(self, event=None):
        """治具字體大小變更時處理"""
        try:
            new_size = int(self.fixture_font_var.get())
            if 8 <= new_size <= 24:
                self.font_size = new_size
                # 更新所有元件的字體
                self.update_all_fonts(new_size)
                # 儲存設定
                self.save_settings()
        except ValueError:
            pass  # 忽略無效輸入
    
    def on_serial_setting_changed(self, event=None):
        """串列設定變更時處理"""
        self.save_settings()
        self.update_serial_info()
        
    def update_all_fonts(self, font_size):
        """更新所有字體"""
        # 這裡可以加入更新字體的邏輯
        pass

    def get_available_com_ports(self):
        """取得可用的 COM 埠列表"""
        try:
            ports = [port.device for port in serial.tools.list_ports.comports()]
            return ports if ports else ['COM5']  # 預設提供 COM5 作為選項
        except Exception as e:
            print(f"取得 COM 埠時發生錯誤: {e}")
            return ['COM5']

    def on_com_port_changed(self, event=None):
        """當 COM 埠變更時儲存設定"""
        try:
            selected_com = self.com_port_var.get()
            self.save_settings()
            self.update_serial_info()
            self.log_message(f"COM埠已變更為: {selected_com}")
        except Exception as e:
            print(f"變更 COM 埠時發生錯誤: {e}")

    def create_serial_info_area(self, parent):
        """建立串列參數顯示區域"""
        serial_frame = ttk.LabelFrame(parent, text="串列參數", padding="5")
        serial_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 串列參數顯示
        self.serial_info_label = tk.Label(
            serial_frame,
            text="",
            font=("微軟正黑體", self.font_size),
            justify=tk.LEFT,
            anchor='w'
        )
        self.serial_info_label.pack(fill=tk.X)
        
        self.update_serial_info()

    def create_result_area(self, parent):
        """建立執行結果區域"""
        result_frame = ttk.LabelFrame(parent, text="執行結果", padding="5")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 建立文字框架和滾動條
        text_frame = ttk.Frame(result_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # 結果顯示文字方塊
        self.result_text = tk.Text(
            text_frame,
            height=10,
            font=("Consolas", self.font_size),
            wrap=tk.WORD
        )
        
        # 垂直滾動條
        v_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=v_scrollbar.set)
        
        # 包裝
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def on_category_changed(self, selected_category):
        """處理測試類別變更 (單選邏輯)"""
        # 取消其他類別的勾選
        for category, var in self.test_category_vars.items():
            if category != selected_category:
                var.set(False)
        
        # 確保至少有一個被選中
        if not self.test_category_vars[selected_category].get():
            # 如果用戶試圖取消當前選擇，重新勾選
            self.test_category_vars[selected_category].set(True)
        
        self.current_category = selected_category
        self.update_command_list()
        self.save_settings()

    def update_command_list(self):
        """更新指令列表"""
        if self.current_category in self.commands:
            command_list = []
            for cmd in self.commands[self.current_category]:
                command_list.append(f"{cmd['code']} - {cmd['description']}")
            self.command_combobox['values'] = command_list
            
            # 清除當前選擇
            self.command_combobox.set('')

    def reload_commands(self):
        """重新載入指令檔案"""
        try:
            # 清空現有指令
            for category in self.commands:
                self.commands[category] = []
            
            # 重新載入指令檔案
            self.load_commands()
            
            # 更新指令列表
            self.update_command_list()
            
            # 記錄成功訊息
            self.log_message("指令檔案已重新載入")
            messagebox.showinfo("成功", "指令檔案已重新載入！")
            
        except Exception as e:
            error_msg = f"重新載入指令檔案時發生錯誤: {e}"
            self.log_message(error_msg)
            messagebox.showerror("錯誤", error_msg)

    def on_command_selected(self, event=None):
        """處理指令選擇"""
        selection = self.command_combobox.get()
        if selection:
            self.log_message(f"已選擇: {selection}")

    def on_execute_command(self):
        """執行選擇的指令"""
        selection = self.command_combobox.get()
        if not selection:
            messagebox.showwarning("警告", "請先選擇一個指令")
            return
            
        # 提取指令代碼 (只發送指令部分，不包含描述)
        if ' - ' in selection:
            command_code = selection.split(' - ')[0]
        else:
            command_code = selection
        
        # 顯示送出的指令 (只顯示指令代碼)
        self.sent_command_var.set(command_code)
        
        # 執行串列指令
        result = self.send_serial_command(command_code)
        
        if result:
            self.log_message(f"指令 '{command_code}' 執行成功")
            self.log_message(f"回應: {result}")
        else:
            self.log_message(f"指令 '{command_code}' 執行失敗")

    def on_clear_results(self):
        """清除執行結果"""
        self.result_text.delete(1.0, tk.END)
        self.log_message("執行結果已清除")

    def send_serial_command(self, command):
        """發送串列指令 - 改進版本"""
        try:
            # 检查COM口是否选择
            com_port = self.com_port_var.get()
            if not com_port:
                self.log_message("錯誤：未選擇COM口")
                return None
            
            # 检查COM口是否可用
            available_ports = self.get_available_com_ports()
            if com_port not in available_ports:
                self.log_message(f"錯誤：COM口 {com_port} 不可用")
                return None
            
            # 獲取串列參數
            parity_map = {
                'None': serial.PARITY_NONE,
                'Even': serial.PARITY_EVEN, 
                'Odd': serial.PARITY_ODD,
                'Mark': serial.PARITY_MARK,
                'Space': serial.PARITY_SPACE
            }
            
            # 建立串列連接 (使用選擇的 COM 埠)
            self.serial_connection = serial.Serial(
                port=com_port,
                baudrate=int(self.baudrate_var.get()),
                bytesize=int(self.bytesize_var.get()),
                stopbits=float(self.stopbits_var.get()),
                parity=parity_map.get(self.parity_var.get(), serial.PARITY_NONE),
                timeout=float(self.timeout_var.get())
            )
            
            # 等待连接稳定
            time.sleep(0.2)
            
            # 發送指令
            command_bytes = command.encode('utf-8')
            self.serial_connection.write(command_bytes)
            
            # 等待回應 - 增加等待时间
            time.sleep(0.5)
            
            # 讀取回應
            response = ""
            if self.serial_connection.in_waiting > 0:
                response = self.serial_connection.read(self.serial_connection.in_waiting).decode('utf-8', errors='ignore')
            
            return response.strip() if response else "指令已發送 (無回應)"
            
        except serial.SerialException as e:
            error_msg = f"串列通訊錯誤: {e}"
            self.log_message(error_msg)
            return None
        except Exception as e:
            error_msg = f"其他錯誤: {e}"
            self.log_message(error_msg)
            return None
        finally:
            # 确保连接被关闭
            if self.serial_connection and self.serial_connection.is_open:
                try:
                    self.serial_connection.close()
                except:
                    pass
                self.serial_connection = None

    def update_serial_info(self):
        """更新串列參數顯示"""
        com_port = self.com_port_var.get()
        info_text = (f"串列設定: {com_port}, {self.baudrate_var.get()} baud, "
                    f"{self.bytesize_var.get()} bits, {self.stopbits_var.get()} stop, "
                    f"{self.parity_var.get()} parity, {self.timeout_var.get()}s timeout")
        self.serial_info_label.config(text=info_text)

    def log_message(self, message):
        """記錄訊息到結果區域"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.result_text.insert(tk.END, log_entry)
        self.result_text.see(tk.END)

    def save_settings(self):
        """儲存設定"""
        try:
            settings = load_setup()
            
            # 更新制具控制設定
            if 'Fixture_Control' not in settings:
                settings['Fixture_Control'] = {}
                
            fixture_settings = settings['Fixture_Control']
            
            # 儲存 COM Port 設定
            fixture_settings['Fixture_COM_Port'] = self.com_port_var.get()
            
            # 儲存測試類別設定
            fixture_settings['Test_Category_FUNCTION'] = self.test_category_vars['FUNCTION'].get()
            fixture_settings['Test_Category_MB'] = self.test_category_vars['MB'].get()
            fixture_settings['Test_Category_Original_Commands'] = self.test_category_vars['原始群元指令'].get()
            fixture_settings['Test_Category_4CAM_stitching'] = self.test_category_vars['4CAM_stitching的指令'].get()
            
            # 儲存串列設定
            if 'Serial_Settings' not in fixture_settings:
                fixture_settings['Serial_Settings'] = {}
                
            serial_settings = fixture_settings['Serial_Settings']
            serial_settings['Baudrate'] = self.baudrate_var.get()
            serial_settings['Bytesize'] = self.bytesize_var.get()
            serial_settings['Stopbits'] = self.stopbits_var.get()
            serial_settings['Parity'] = self.parity_var.get()
            serial_settings['Timeout'] = self.timeout_var.get()
            
            # 儲存設定
            from config_core import save_setup
            save_setup(settings)
                
        except Exception as e:
            print(f"儲存設定時發生錯誤: {e}")

    def update_font_size(self, new_font_size):
        """更新字體大小 (由外部調用)"""
        try:
            self.font_size = int(new_font_size)
            
            # 更新所有 UI 元件的字體
            if hasattr(self, 'desc_label'):
                self.desc_label.config(font=("微軟正黑體", self.font_size))
            
            # 更新所有標籤的字體
            self.update_widget_fonts(self.root)
            
            # 更新結果文字區域的字體
            if hasattr(self, 'result_text'):
                self.result_text.config(font=("Consolas", self.font_size))
            
            # 更新串列資訊標籤
            if hasattr(self, 'serial_info_label'):
                self.serial_info_label.config(font=("微軟正黑體", self.font_size))
                
        except Exception as e:
            print(f"更新字體大小時發生錯誤: {e}")

    def update_widget_fonts(self, widget):
        """遞迴更新所有 widget 的字體"""
        try:
            # 針對特定類型的 widget 更新字體
            if isinstance(widget, tk.Label):
                widget.config(font=("微軟正黑體", self.font_size))
            elif isinstance(widget, (tk.Button, ttk.Button)):
                try:
                    widget.config(font=("微軟正黑體", self.font_size))
                except:
                    pass  # ttk 按鈕可能不支援 font 參數
            
            # 遞迴處理子 widget
            for child in widget.winfo_children():
                self.update_widget_fonts(child)
        except Exception as e:
            pass  # 忽略字體更新錯誤

    def setup_tooltips(self):
        """設定工具提示 - 為治具頁面每個欄位提供詳細中文說明"""
        if not self.tooltip_manager:
            return
        
        tt = self.tooltip_manager.add_tooltip_with_text
        
        # 指令控制區
        tt(self.com_combobox, "選擇治具連接的 COM 通訊埠\n與 DUT 分頁的 COM Port 獨立")
        tt(self.command_combobox, "選擇要執行的治具指令\n指令會依據選擇的測試類別而不同")
        tt(self.execute_btn, "將選取的治具指令透過 COM 埠送出執行")
        tt(self.sent_command_entry, "顯示最近一次送出的指令代碼\n（唯讀，僅供參考）")
        tt(self.clear_btn, "清空下方的執行結果區域")
        tt(self.reload_btn, "重新載入 Fixture_Command.txt 指令檔案\n適用於新增或修改指令後刷新清單")
        
        # 說明區域
        if hasattr(self, 'desc_label'):
            tt(self.desc_label, "此區域顯示治具指令檔案中定義的說明文字\n由 Fixture_Command.txt 中的「說明文=」欄位控制")
        
        # 串列設定區
        if hasattr(self, 'baudrate_combo'):
            tt(self.baudrate_combo, "串列埠通訊速率（每秒位元數）\n治具常用值：9600\n修改後會自動儲存")
        if hasattr(self, 'bytesize_combo'):
            tt(self.bytesize_combo, "每個資料封包的位元數\n預設為 8，通常不需要修改")
        if hasattr(self, 'stopbits_combo'):
            tt(self.stopbits_combo, "停止位元數，用於標記資料封包結束\n預設為 1，通常不需要修改")
        if hasattr(self, 'parity_combo'):
            tt(self.parity_combo, "奇偶校驗模式，用於檢測傳輸錯誤\nNone：不使用校驗（最常見）\nEven/Odd：偶校驗/奇校驗")
        if hasattr(self, 'timeout_entry'):
            tt(self.timeout_entry, "串列埠等待回應的超時時間（秒）\n超過此時間未收到資料則視為超時\n建議值：0.5~5 秒")
        
        # 字體設定
        if hasattr(self, 'fixture_font_spinbox'):
            tt(self.fixture_font_spinbox, "調整治具頁面的字體大小\n範圍 8~24，修改後即時生效")
        
        # 串列參數顯示
        if hasattr(self, 'serial_info_label'):
            tt(self.serial_info_label, "顯示目前串列埠的完整參數設定\n包含 COM 埠、波特率、資料位元等")
        
        # 執行結果
        if hasattr(self, 'result_text'):
            tt(self.result_text, "顯示治具指令的執行記錄與回應結果\n每條記錄都帶有時間戳記")

    def refresh_ports(self):
        """刷新 COM 埠列表 (由外部調用)"""
        try:
            available_ports = self.get_available_com_ports()
            if hasattr(self, 'com_combobox'):
                current_selection = self.com_port_var.get()
                self.com_combobox['values'] = available_ports
                
                # 如果目前選擇的埠仍然可用，保持選擇
                if current_selection in available_ports:
                    self.com_combobox.set(current_selection)
                elif available_ports:
                    self.com_combobox.set(available_ports[0])
                    self.com_port_var.set(available_ports[0])
                    self.save_settings()
        except Exception as e:
            print(f"刷新 COM 埠時發生錯誤: {e}")

# 為主程式相容性建立 FixtureFrame 類別
class FixtureFrame(ttk.Frame):
    def __init__(self, parent, tooltip_manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent_frame = self  # 設置parent_frame屬性供字體更新使用
        self.tooltip_manager = tooltip_manager

        # 建立制具控制視窗
        self.fixture_window = FixtureControlWindow(self)
    
    def update_font_size(self, new_font_size):
        """更新字體大小的外部介面"""
        if hasattr(self, 'fixture_window'):
            self.fixture_window.update_font_size(new_font_size)
    
    def refresh_ports(self):
        """刷新 COM 埠的外部介面"""
        if hasattr(self, 'fixture_window'):
            self.fixture_window.refresh_ports()

def main():
    """主程式 - 獨立測試用"""
    root = tk.Tk()
    app = FixtureControlWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()

