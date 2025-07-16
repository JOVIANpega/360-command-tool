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
            self.tooltip_manager = ToolTipManager(self.root)
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
            '原始的指令': []
        }
        self.description_text = ""
        
        # 測試類別變數 (只能選一個)
        self.test_category_vars = {
            'FUNCTION': tk.BooleanVar(),
            'MB': tk.BooleanVar(),
            '原始的指令': tk.BooleanVar()
        }
        
        # 預設選擇FUNCTION
        self.test_category_vars['FUNCTION'].set(True)
        self.current_category = 'FUNCTION'
        
        # 串列設定變數  
        self.baudrate_var = tk.StringVar(value="9600")
        self.bytesize_var = tk.StringVar(value="8")
        self.stopbits_var = tk.StringVar(value="1")
        self.parity_var = tk.StringVar(value="None")
        self.timeout_var = tk.StringVar(value="1.0")

    def load_settings(self):
        """載入設定檔"""
        try:
            setup_path = resource_path("setup.json")
            if os.path.exists(setup_path):
                with open(setup_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 載入制具控制設定
                fixture_settings = settings.get('Fixture_Control', {})
                
                # 載入測試類別設定
                self.test_category_vars['FUNCTION'].set(
                    fixture_settings.get('Test_Category_FUNCTION', True))
                self.test_category_vars['MB'].set(
                    fixture_settings.get('Test_Category_MB', False))
                self.test_category_vars['原始的指令'].set(
                    fixture_settings.get('Test_Category_Original_Commands', False))
                
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
                
                # 載入字體大小設定
                self.font_size = int(settings.get('UIFontSize', 11))
                
        except Exception as e:
            print(f"載入設定時發生錯誤: {e}")
            self.font_size = 11

    def load_commands(self):
        """載入指令檔案"""
        try:
            command_file = resource_path("FIXTURE/Fixture_Command.txt")
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
                            if ' - ' in line and line.strip():
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
        
        # 第二行：指令選擇與執行
        command_frame = ttk.Frame(control_frame)
        command_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(command_frame, text="選擇指令:", font=("微軟正黑體", self.font_size)).pack(side=tk.LEFT)
        
        # 指令選擇下拉選單 (約20字元寬度)
        self.command_combobox = ttk.Combobox(
            command_frame, 
            state="readonly",
            width=20
        )
        self.command_combobox.pack(side=tk.LEFT, padx=(10, 5))
        self.command_combobox.bind('<<ComboboxSelected>>', self.on_command_selected)
        
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

    def on_command_selected(self, event=None):
        """處理指令選擇"""
        selection = self.command_combobox.get()
        if selection:
            # 提取指令代碼
            command_code = selection.split(' - ')[0]
            self.log_message(f"已選擇: {selection}")

    def on_execute_command(self):
        """執行選擇的指令"""
        selection = self.command_combobox.get()
        if not selection:
            messagebox.showwarning("警告", "請先選擇一個指令")
            return
            
        # 提取指令代碼 (只送單一字元)
        command_code = selection.split(' - ')[0]
        
        # 顯示送出的指令
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
        """發送串列指令"""
        try:
            # 獲取串列參數
            parity_map = {
                'None': serial.PARITY_NONE,
                'Even': serial.PARITY_EVEN, 
                'Odd': serial.PARITY_ODD,
                'Mark': serial.PARITY_MARK,
                'Space': serial.PARITY_SPACE
            }
            
            # 建立串列連接
            self.serial_connection = serial.Serial(
                port='COM5',  # 這應該從設定中讀取
                baudrate=int(self.baudrate_var.get()),
                bytesize=int(self.bytesize_var.get()),
                stopbits=float(self.stopbits_var.get()),
                parity=parity_map.get(self.parity_var.get(), serial.PARITY_NONE),
                timeout=float(self.timeout_var.get())
            )
            
            # 發送指令
            command_bytes = command.encode('utf-8')
            self.serial_connection.write(command_bytes)
            
            # 等待回應
            time.sleep(0.1)
            
            # 讀取回應
            response = ""
            if self.serial_connection.in_waiting > 0:
                response = self.serial_connection.read(self.serial_connection.in_waiting).decode('utf-8', errors='ignore')
            
            # 關閉連接
            self.serial_connection.close()
            self.serial_connection = None
            
            return response.strip() if response else "指令已發送 (無回應)"
            
        except Exception as e:
            if self.serial_connection:
                try:
                    self.serial_connection.close()
                except:
                    pass
                self.serial_connection = None
            
            error_msg = f"串列通訊錯誤: {e}"
            self.log_message(error_msg)
            return None

    def update_serial_info(self):
        """更新串列參數顯示"""
        info_text = (f"串列設定: COM5, {self.baudrate_var.get()} baud, "
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
            setup_path = resource_path("setup.json")
            settings = {}
            
            # 載入現有設定
            if os.path.exists(setup_path):
                with open(setup_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            # 更新制具控制設定
            if 'Fixture_Control' not in settings:
                settings['Fixture_Control'] = {}
                
            fixture_settings = settings['Fixture_Control']
            
            # 儲存測試類別設定
            fixture_settings['Test_Category_FUNCTION'] = self.test_category_vars['FUNCTION'].get()
            fixture_settings['Test_Category_MB'] = self.test_category_vars['MB'].get()
            fixture_settings['Test_Category_Original_Commands'] = self.test_category_vars['原始的指令'].get()
            
            # 儲存串列設定
            if 'Serial_Settings' not in fixture_settings:
                fixture_settings['Serial_Settings'] = {}
                
            serial_settings = fixture_settings['Serial_Settings']
            serial_settings['Baudrate'] = self.baudrate_var.get()
            serial_settings['Bytesize'] = self.bytesize_var.get()
            serial_settings['Stopbits'] = self.stopbits_var.get()
            serial_settings['Parity'] = self.parity_var.get()
            serial_settings['Timeout'] = self.timeout_var.get()
            
            # 寫入檔案
            with open(setup_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"儲存設定時發生錯誤: {e}")

    def setup_tooltips(self):
        """設定工具提示"""
        if not self.tooltip_manager:
            return
            
        tooltips = {
            self.command_combobox: "選擇要執行的制具指令",
            self.execute_btn: "執行選擇的指令",
            self.sent_command_entry: "顯示剛剛發送的指令代碼", 
            self.clear_btn: "清除執行結果區域的所有內容"
        }
        
        for widget, text in tooltips.items():
            self.tooltip_manager.add_tooltip(widget, text)

# 為主程式相容性建立 FixtureFrame 類別
class FixtureFrame(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # 建立制具控制視窗
        self.fixture_window = FixtureControlWindow(self)

def main():
    """主程式 - 獨立測試用"""
    root = tk.Tk()
    app = FixtureControlWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()

