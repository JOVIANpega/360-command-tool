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

class FixtureControlWindow:
    def __init__(self, root):
        self.root = root
        
        # 只有在根視窗是 Tk 實例時才設定視窗屬性
        if isinstance(root, tk.Tk):
            self.root.title("制具控制系統")
            self.root.geometry("800x700")
            self.root.resizable(True, True)
        
        # 設定字體大小
        self.font_size = 12
        
        # 初始化 COM 埠
        self.serial_connection = None
        self.available_ports = []
        
        # 初始化 ToolTip 管理器
        try:
            self.tooltip_manager = ToolTipManager()
        except Exception as e:
            print(f"ToolTip 管理器初始化失敗: {e}")
            # 提供一個備用的 ToolTip 管理器
            class DummyToolTipManager:
                def add_tooltip(self, widget, text):
                    pass
            self.tooltip_manager = DummyToolTipManager()
        
        # 讀取設定檔
        self.load_settings()
        
        # 初始化指令資料
        self.command_data = {}
        self.current_selected_command = ""
        
        # 載入指令檔案
        self.load_command_file()
        
        # 建立 GUI
        self.create_gui()
        
        # 更新 COM 埠列表
        self.refresh_com_ports()

    def load_settings(self):
        """載入設定檔"""
        try:
            setup_file = resource_path("setup.json")
            if os.path.exists(setup_file):
                with open(setup_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            else:
                self.settings = {}
        except Exception as e:
            print(f"載入設定檔失敗: {e}")
            self.settings = {}
        
        # 取得制具控制設定
        self.fixture_settings = self.settings.get("Fixture_Control", {})
        self.font_size = int(self.fixture_settings.get("Fixture_Font_Size", 12))
        
        # 取得串列埠設定
        self.serial_settings = self.fixture_settings.get("Serial_Settings", {})
        self.baudrate = int(self.serial_settings.get("Baudrate", "9600"))
        self.bytesize = int(self.serial_settings.get("Bytesize", "8"))
        self.stopbits = int(self.serial_settings.get("Stopbits", "1"))
        self.parity = self.serial_settings.get("Parity", "None")
        self.timeout = float(self.serial_settings.get("Timeout", "1.0"))

    def load_command_file(self):
        """載入指令檔案"""
        try:
            command_file = resource_path("FIXTURE/Fixture_Command.txt")
            if not os.path.exists(command_file):
                messagebox.showerror("錯誤", f"找不到指令檔案: {command_file}")
                return
            
            with open(command_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析檔案內容
            self.command_data = {}
            current_section = None
            
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # 檢查是否為區段標題
                if line.endswith(':'):
                    current_section = line[:-1]
                    self.command_data[current_section] = []
                elif current_section and ' - ' in line:
                    # 解析指令行 (格式: "F - 給電")
                    parts = line.split(' - ', 1)
                    if len(parts) == 2:
                        code = parts[0].strip()
                        description = parts[1].strip()
                        self.command_data[current_section].append({
                            'code': code,
                            'description': description,
                            'display': f"{code} - {description}"
                        })
            
            print(f"已載入指令資料: {list(self.command_data.keys())}")
            
        except Exception as e:
            print(f"載入指令檔案失敗: {e}")
            messagebox.showerror("錯誤", f"載入指令檔案失敗: {e}")

    def create_gui(self):
        """建立 GUI 介面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置網格權重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # ===== 說明區域 =====
        desc_frame = ttk.LabelFrame(main_frame, text="制具控制說明", padding="10")
        desc_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        desc_text = """本頁為制具控制區，目前僅支援控制 XX 廠商的自動化測試制具，請依功能選擇控制按鈕。
選擇測試類別後，可從下拉選單選擇指令，按執行按鈕送出對應代碼至 COM 埠。"""
        
        desc_label = tk.Label(desc_frame, text=desc_text, wraplength=750, 
                             justify=tk.LEFT, font=("Arial", self.font_size))
        desc_label.pack(anchor=tk.W)
        
        # ===== COM 埠設定區域 =====
        com_frame = ttk.LabelFrame(main_frame, text="COM 埠設定", padding="10")
        com_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # COM 埠選擇
        tk.Label(com_frame, text="COM 埠:", font=("Arial", self.font_size)).grid(row=0, column=0, padx=(0, 10), sticky=tk.W)
        self.com_port_var = tk.StringVar()
        self.com_port_combo = ttk.Combobox(com_frame, textvariable=self.com_port_var, 
                                          font=("Arial", self.font_size), width=15)
        self.com_port_combo.grid(row=0, column=1, padx=(0, 10), sticky=tk.W)
        
        # 重新整理按鈕
        refresh_btn = tk.Button(com_frame, text="重新整理", font=("Arial", self.font_size),
                               command=self.refresh_com_ports, bg="#4CAF50", fg="white",
                               width=10, height=1)
        refresh_btn.grid(row=0, column=2, padx=(0, 10))
        self.tooltip_manager.add_tooltip(refresh_btn, "重新取得可用的 COM 埠")
        
        # 串列埠設定顯示
        tk.Label(com_frame, text="串列參數:", font=("Arial", self.font_size)).grid(row=1, column=0, padx=(0, 10), sticky=tk.W)
        serial_params_text = f"波特率:{self.baudrate} | 資料位元:{self.bytesize} | 停止位元:{self.stopbits} | 奇偶校驗:{self.parity} | 超時:{self.timeout}s"
        serial_params_label = tk.Label(com_frame, text=serial_params_text, font=("Arial", self.font_size - 1),
                                      fg="blue", wraplength=500, justify=tk.LEFT)
        serial_params_label.grid(row=1, column=1, columnspan=2, padx=(0, 10), sticky=tk.W)
        
        # ===== 測試類別選擇區域 =====
        category_frame = ttk.LabelFrame(main_frame, text="測試類別選擇", padding="10")
        category_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 建立測試類別選項
        self.category_vars = {}
        categories = list(self.command_data.keys())
        
        for i, category in enumerate(categories):
            var = tk.BooleanVar()
            checkbox = tk.Checkbutton(category_frame, text=category, variable=var,
                                    font=("Arial", self.font_size),
                                    command=self.on_category_changed)
            checkbox.grid(row=0, column=i, padx=(0, 20), sticky=tk.W)
            self.category_vars[category] = var
            
            # 預設選擇 FUNCTION
            if category == "FUNCTION":
                var.set(True)
        
        # ===== 指令選擇區域 =====
        command_frame = ttk.LabelFrame(main_frame, text="指令選擇與執行", padding="10")
        command_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        command_frame.columnconfigure(1, weight=1)
        
        # 指令選擇下拉選單
        tk.Label(command_frame, text="選擇指令:", font=("Arial", self.font_size)).grid(row=0, column=0, padx=(0, 10), sticky=tk.W)
        self.command_var = tk.StringVar()
        self.command_combo = ttk.Combobox(command_frame, textvariable=self.command_var,
                                         font=("Arial", self.font_size), width=40, state="readonly")
        self.command_combo.grid(row=0, column=1, padx=(0, 10), sticky=(tk.W, tk.E))
        self.command_combo.bind("<<ComboboxSelected>>", self.on_command_selected)
        
        # 執行按鈕
        execute_btn = tk.Button(command_frame, text="執行指令", font=("Arial", self.font_size + 2),
                               command=self.execute_command, bg="#2196F3", fg="white",
                               width=12, height=2, relief=tk.RAISED, bd=2)
        execute_btn.grid(row=0, column=2, padx=(10, 0))
        self.tooltip_manager.add_tooltip(execute_btn, "執行所選的制具控制指令")
        
        # ===== 送出指令顯示區域 =====
        output_frame = ttk.LabelFrame(main_frame, text="送出指令顯示", padding="10")
        output_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(1, weight=1)
        
        tk.Label(output_frame, text="送出指令:", font=("Arial", self.font_size)).grid(row=0, column=0, padx=(0, 10), sticky=tk.W)
        self.sent_command_var = tk.StringVar()
        sent_command_entry = tk.Entry(output_frame, textvariable=self.sent_command_var,
                                     font=("Arial", self.font_size), state="readonly",
                                     width=20, bg="#f0f0f0")
        sent_command_entry.grid(row=0, column=1, padx=(0, 10), sticky=(tk.W, tk.E))
        
        # 清除按鈕
        clear_btn = tk.Button(output_frame, text="清除", font=("Arial", self.font_size),
                             command=self.clear_sent_command, bg="#FF5722", fg="white",
                             width=8, height=1)
        clear_btn.grid(row=0, column=2, padx=(10, 0))
        self.tooltip_manager.add_tooltip(clear_btn, "清除送出指令顯示內容")
        
        # ===== 執行結果顯示區域 =====
        result_frame = ttk.LabelFrame(main_frame, text="執行結果", padding="10")
        result_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # 結果顯示文字區域
        self.result_text = tk.Text(result_frame, height=8, width=80,
                                  font=("Consolas", self.font_size - 1),
                                  wrap=tk.WORD, bg="#f8f8f8")
        
        # 捲軸
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # ===== 字體調整區域 =====
        font_frame = ttk.Frame(main_frame)
        font_frame.grid(row=6, column=0, columnspan=2, pady=(10, 0), sticky=tk.W)
        
        tk.Label(font_frame, text="字體大小:", font=("Arial", self.font_size)).pack(side=tk.LEFT, padx=(0, 10))
        
        font_minus_btn = tk.Button(font_frame, text="-", font=("Arial", self.font_size),
                                  command=self.decrease_font_size, width=3, height=1)
        font_minus_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.tooltip_manager.add_tooltip(font_minus_btn, "減小字體大小")
        
        font_plus_btn = tk.Button(font_frame, text="+", font=("Arial", self.font_size),
                                 command=self.increase_font_size, width=3, height=1)
        font_plus_btn.pack(side=tk.LEFT, padx=(5, 0))
        self.tooltip_manager.add_tooltip(font_plus_btn, "增大字體大小")
        
        # 初始化指令選單
        self.update_command_list()

    def reload_settings(self):
        """重新載入設定"""
        try:
            self.load_settings()
            self.add_result_message("串列埠設定已重新載入")
            
            # 更新串列埠參數顯示
            self.update_serial_params_display()
            
        except Exception as e:
            self.add_result_message(f"重新載入設定失敗: {e}", "error")
    
    def update_serial_params_display(self):
        """更新串列埠參數顯示"""
        try:
            # 如果存在串列參數標籤，則更新它
            for child in self.root.winfo_children():
                if hasattr(child, 'winfo_children'):
                    for widget in child.winfo_children():
                        if hasattr(widget, 'cget') and 'serial_params_label' in str(widget):
                            serial_params_text = f"波特率:{self.baudrate} | 資料位元:{self.bytesize} | 停止位元:{self.stopbits} | 奇偶校驗:{self.parity} | 超時:{self.timeout}s"
                            widget.config(text=serial_params_text)
                            break
        except Exception as e:
            print(f"更新串列參數顯示失敗: {e}")

    def refresh_com_ports(self):
        """重新整理 COM 埠列表"""
        try:
            self.available_ports = [port.device for port in serial.tools.list_ports.comports()]
            self.com_port_combo['values'] = self.available_ports
            
            # 設定預設選擇
            if self.available_ports:
                current_port = self.fixture_settings.get("Fixture_COM_Port", "")
                if current_port in self.available_ports:
                    self.com_port_var.set(current_port)
                else:
                    self.com_port_var.set(self.available_ports[0])
            else:
                self.com_port_var.set("")
            
            self.add_result_message(f"已更新 COM 埠列表: {', '.join(self.available_ports) if self.available_ports else '無可用埠'}")
            
        except Exception as e:
            self.add_result_message(f"更新 COM 埠列表失敗: {e}", "error")

    def on_category_changed(self):
        """測試類別改變時的處理"""
        # 確保只能選擇一個類別
        selected_categories = [cat for cat, var in self.category_vars.items() if var.get()]
        
        if len(selected_categories) > 1:
            # 如果選擇了多個，只保留最後選擇的
            for cat, var in self.category_vars.items():
                if cat != selected_categories[-1]:
                    var.set(False)
        
        self.update_command_list()

    def update_command_list(self):
        """更新指令選單"""
        try:
            # 取得選擇的測試類別
            selected_category = None
            for cat, var in self.category_vars.items():
                if var.get():
                    selected_category = cat
                    break
            
            if selected_category and selected_category in self.command_data:
                commands = self.command_data[selected_category]
                command_list = [cmd['display'] for cmd in commands]
                self.command_combo['values'] = command_list
                
                # 清除當前選擇
                self.command_var.set("")
                self.current_selected_command = ""
                
                self.add_result_message(f"已載入 {selected_category} 類別，共 {len(command_list)} 個指令")
            else:
                self.command_combo['values'] = []
                self.command_var.set("")
                self.current_selected_command = ""
                
        except Exception as e:
            self.add_result_message(f"更新指令列表失敗: {e}", "error")

    def on_command_selected(self, event):
        """指令選擇時的處理"""
        try:
            selected_display = self.command_var.get()
            if not selected_display:
                return
            
            # 找到對應的指令代碼
            selected_category = None
            for cat, var in self.category_vars.items():
                if var.get():
                    selected_category = cat
                    break
            
            if selected_category and selected_category in self.command_data:
                for cmd in self.command_data[selected_category]:
                    if cmd['display'] == selected_display:
                        self.current_selected_command = cmd['code']
                        self.add_result_message(f"已選擇指令: {selected_display}")
                        break
                        
        except Exception as e:
            self.add_result_message(f"選擇指令失敗: {e}", "error")

    def execute_command(self):
        """執行選擇的指令"""
        try:
            if not self.current_selected_command:
                messagebox.showwarning("警告", "請先選擇要執行的指令")
                return
            
            if not self.com_port_var.get():
                messagebox.showwarning("警告", "請先選擇 COM 埠")
                return
            
            # 顯示送出的指令
            self.sent_command_var.set(self.current_selected_command)
            
            # 建立串列連接並送出指令
            success = self.send_serial_command(self.current_selected_command)
            
            if success:
                self.add_result_message(f"✓ 已送出指令: {self.current_selected_command}", "success")
            else:
                self.add_result_message(f"✗ 送出指令失敗: {self.current_selected_command}", "error")
                
        except Exception as e:
            self.add_result_message(f"執行指令時發生錯誤: {e}", "error")

    def send_serial_command(self, command):
        """透過串列埠送出指令"""
        try:
            port = self.com_port_var.get()
            if not port:
                return False
            
            # 處理奇偶校驗設定
            parity_map = {
                "None": serial.PARITY_NONE,
                "Even": serial.PARITY_EVEN,
                "Odd": serial.PARITY_ODD,
                "Mark": serial.PARITY_MARK,
                "Space": serial.PARITY_SPACE
            }
            parity_setting = parity_map.get(self.parity, serial.PARITY_NONE)
            
            # 建立串列連接，使用設定檔中的參數
            self.add_result_message(f"串列參數: 波特率={self.baudrate}, 資料位元={self.bytesize}, 停止位元={self.stopbits}, 奇偶校驗={self.parity}, 超時={self.timeout}秒")
            
            with serial.Serial(
                port=port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                stopbits=self.stopbits,
                parity=parity_setting,
                timeout=self.timeout
            ) as ser:
                # 送出指令
                ser.write(command.encode('utf-8'))
                time.sleep(0.1)
                
                # 嘗試讀取回應
                response = ser.read(100)
                if response:
                    self.add_result_message(f"收到回應: {response.decode('utf-8', errors='ignore')}")
                
                return True
                
        except Exception as e:
            self.add_result_message(f"串列通訊錯誤: {e}", "error")
            return False

    def clear_sent_command(self):
        """清除送出指令顯示"""
        self.sent_command_var.set("")
        self.add_result_message("已清除送出指令顯示")

    def add_result_message(self, message, msg_type="info"):
        """新增結果訊息"""
        try:
            timestamp = time.strftime("%H:%M:%S")
            
            if msg_type == "success":
                formatted_msg = f"[{timestamp}] ✓ {message}\n"
            elif msg_type == "error":
                formatted_msg = f"[{timestamp}] ✗ {message}\n"
            else:
                formatted_msg = f"[{timestamp}] {message}\n"
            
            self.result_text.insert(tk.END, formatted_msg)
            self.result_text.see(tk.END)
            
        except Exception as e:
            print(f"新增結果訊息失敗: {e}")

    def increase_font_size(self):
        """增大字體"""
        self.font_size = min(self.font_size + 1, 20)
        self.update_font_size()

    def decrease_font_size(self):
        """減小字體"""
        self.font_size = max(self.font_size - 1, 8)
        self.update_font_size()

    def update_font_size(self):
        """更新所有元件的字體大小"""
        try:
            # 這裡可以加入字體更新邏輯
            self.add_result_message(f"字體大小已調整為: {self.font_size}")
        except Exception as e:
            print(f"更新字體大小失敗: {e}")

class FixtureFrame(tk.Frame):
    """兼容主程式的制具控制框架"""
    def __init__(self, parent):
        super().__init__(parent)
        
        # 在這個框架中嵌入我們的制具控制視窗
        self.fixture_window = FixtureControlWindow(self)
        
        # 初始化一些變數以兼容主程式
        self.com_port_var = self.fixture_window.com_port_var
        self.command_var = self.fixture_window.command_var
        self.category_vars = self.fixture_window.category_vars
        self._fixture_font_size = self.fixture_window.font_size
        
        # 移除獨立視窗的標題和幾何設定
        self.fixture_window.root = parent  # 重設父容器
        
    def refresh_ports(self):
        """重新整理 COM 埠（兼容主程式）"""
        if hasattr(self.fixture_window, 'refresh_com_ports'):
            self.fixture_window.refresh_com_ports()
        
        # 重新載入串列埠設定
        self.fixture_window.load_settings()
    
    def get_settings(self):
        """取得設定（兼容主程式）"""
        data = {}
        data['COM'] = self.com_port_var.get()
        data['CMD'] = self.command_var.get()
        for cat, var in self.category_vars.items():
            data[cat] = var.get()
        data['FixtureFontSize'] = str(self._fixture_font_size)
        return data
    
    def change_fixture_font(self, delta):
        """改變字體大小（兼容主程式）"""
        if delta == 0:
            # 只套用當前大小
            self.fixture_window.update_font_size()
        else:
            # 增減字體大小
            if delta > 0:
                self.fixture_window.increase_font_size()
            else:
                self.fixture_window.decrease_font_size()

if __name__ == "__main__":
    root = tk.Tk()
    app = FixtureControlWindow(root)
    root.mainloop()

