import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
from datetime import datetime
import subprocess
import webbrowser

# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 導入配置模組
try:
    from config import load_setup, save_setup, list_com_ports, GUIDE_FILE, COMMAND_FILE, load_commands
except ImportError as e:
    print(f"導入 config 模組失敗: {e}")
    print(f"當前路徑: {sys.path}")
    sys.exit(1)

# 檢查 command.txt
try:
    commands = load_commands()
except Exception as e:
    messagebox.showerror('錯誤', str(e))
    sys.exit(1)

try:
    from serial_worker import SerialWorker
    from ui_parts.ui_components import UIComponents
    from ui_parts.ui_handlers import UIHandlers
except ImportError as e:
    print(f"導入模組失敗: {e}")
    sys.exit(1)

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
        self.handover_frame = ttk.Frame(self.notebook, style='Main.TFrame')  # 新增第三個 tab
        
        # 配置分頁的 grid
        self.dut_frame.grid_rowconfigure(0, weight=1)
        self.dut_frame.grid_columnconfigure(0, weight=1)
        self.fixture_frame.grid_rowconfigure(0, weight=1)
        self.fixture_frame.grid_columnconfigure(0, weight=1)
        self.handover_frame.grid_rowconfigure(0, weight=1)
        self.handover_frame.grid_columnconfigure(0, weight=1)
        
        # 添加分頁到 notebook
        self.notebook.add(self.dut_frame, text='DUT 控制')
        self.notebook.add(self.fixture_frame, text='治具控制')
        self.notebook.add(self.handover_frame, text='使用說明')  # 改名為使用說明
        
        # 設置分頁切換事件
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        
        # 初始化分頁內容
        self.init_dut_tab()
        self.init_fixture_tab()
        self.init_guide_tab()  # 改名為 init_guide_tab
        
        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
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
    
    def init_guide_tab(self):
        # 初始化使用說明分頁
        # 創建主框架
        guide_main_frame = ttk.LabelFrame(
            self.handover_frame, 
            text="使用說明", 
            padding=20, 
            style="Main.TLabelframe"
        )
        guide_main_frame.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        
        # 標題
        title_label = ttk.Label(
            guide_main_frame,
            text="VALO360 指令通 使用說明",
            font=('Microsoft JhengHei UI', 18, 'bold'),
            style="TLabel"
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # 說明文字
        desc_label = ttk.Label(
            guide_main_frame,
            text="點擊下方按鈕開啟詳細的使用說明文件",
            font=('Microsoft JhengHei UI', 14),
            style="TLabel"
        )
        desc_label.grid(row=1, column=0, pady=(0, 30))
        
        # 開啟使用說明按鈕
        def open_guide():
            try:
                # 獲取 EXE 目錄路徑
                if getattr(sys, 'frozen', False):
                    # 如果是打包後的 EXE
                    exe_dir = os.path.dirname(sys.executable)
                else:
                    # 如果是開發環境
                    exe_dir = os.path.dirname(os.path.abspath(__file__))
                    exe_dir = os.path.dirname(exe_dir)  # 回到上一層目錄
                
                guide_file = os.path.join(exe_dir, "VALO360 指令通使用指南.html")
                
                if not os.path.exists(guide_file):
                    messagebox.showerror("錯誤", f"找不到使用指南檔案：\n{guide_file}")
                    return
                
                # 嘗試用 Chrome 開啟
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
                ]
                
                chrome_opened = False
                for chrome_path in chrome_paths:
                    if os.path.exists(chrome_path):
                        try:
                            subprocess.Popen([chrome_path, guide_file])
                            chrome_opened = True
                            break
                        except Exception:
                            continue
                
                # 如果 Chrome 開啟失敗，嘗試用預設瀏覽器
                if not chrome_opened:
                    try:
                        webbrowser.open(f"file:///{guide_file.replace(os.sep, '/')}")
                    except Exception as e:
                        messagebox.showerror("錯誤", f"無法開啟使用指南：\n{str(e)}")
                        
            except Exception as e:
                messagebox.showerror("錯誤", f"開啟使用指南時發生錯誤：\n{str(e)}")
        
        guide_button = tk.Button(
            guide_main_frame,
            text="開啟使用說明",
            command=open_guide,
            font=('Microsoft JhengHei UI', 16, 'bold'),
            width=20,
            height=3,
            bg='#cccccc',
            fg='black',
            relief='groove',
            borderwidth=2,
            highlightthickness=0
        )
        guide_button.grid(row=2, column=0, pady=20)
        
        # 按鈕 hover 效果
        guide_button.bind("<Enter>", lambda e: guide_button.config(bg="#4caf50", fg="white"))
        guide_button.bind("<Leave>", lambda e: guide_button.config(bg="#cccccc", fg="black"))

    def on_tab_changed(self, event):
        # 獲取當前選中的分頁
        selected_tab = self.notebook.select()
        tab_text = self.notebook.tab(selected_tab, "text")
        
        # 根據分頁切換處理資源
        if tab_text == 'DUT 控制':
            if hasattr(self, 'dut_ui'):
                self.dut_ui.activate()
        elif tab_text == '治具控制':
            # 治具控制分頁的處理邏輯
            if hasattr(self, 'fixture_ui') and hasattr(self.fixture_ui, 'refresh_ports'):
                self.fixture_ui.refresh_ports()
        elif tab_text == '使用說明':
            # 使用說明分頁的處理邏輯
            pass

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

    def on_close(self):
        """TabManager 關閉事件處理"""
        try:
            # 如果有 DUT UI，先保存其設定
            if hasattr(self, 'dut_ui'):
                self.dut_ui.on_close()
            else:
                # 如果沒有 DUT UI，直接關閉
                self.root.destroy()
        except Exception as e:
            print(f'[ERROR] TabManager 關閉時發生錯誤: {e}')
            self.root.destroy()

class SerialUI:
    def __init__(self, parent, root):
        self.parent = parent
        self.root = root
        
        # 首先讀取 setup.json
        setup_data = load_setup()
        # 從 DUT_Control 分層中讀取設定
        self.setup = setup_data.get('DUT_Control', {})
        print(f"[DEBUG] 已讀取 setup.json DUT_Control 設定: {self.setup}")
        
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

        # 載入 Available_End_Strings
        end_strings = self.setup.get('Available_End_Strings', ["root"])
        if isinstance(end_strings, str):
            try:
                end_strings = json.loads(end_strings)
            except Exception:
                end_strings = ["root"]
        self.components.combobox_end['values'] = end_strings
        
        # 讀取並應用設定
        self.load_initial_settings()
        
        # 注意：不要在這裡綁定關閉事件，由 TabManager 統一處理

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
        self.handlers.refresh_com_ports()
        # 其他激活操作...

    def on_close(self):
        """程式關閉時保存所有設定"""
        try:
            print("[DEBUG] 程式關閉，正在保存設定...")
            
            # 收集當前所有設定
            current_settings = {
                'Serial_COM_Port': self.components.combobox_com.get(),
                'Command_Timeout_Seconds': self.components.entry_timeout.get(),
                'Command_End_String': self.components.combobox_end.get(),
                'UI_Font_Size': str(self.components.ui_font_scale.get()),
                'Content_Font_Size': str(self.components.content_font_scale.get()),
                'Default_IP_Address': self.components.entry_ip.get(),
                'Window_Width': str(self.root.winfo_width()),
                'Window_Height': str(self.root.winfo_height()),
                'Last_Selected_Command_Section': self.components.section_var.get()
            }
            
            # 保存 PanedWindow 分割位置
            try:
                sash_position = self.components.main_frame.sashpos(0)
                current_settings['Pane_Sash_Position'] = str(sash_position)
                print(f"[DEBUG] 保存分割位置: {sash_position}")
            except Exception as e:
                print(f"[DEBUG] 獲取分割位置失敗: {e}")
            
            # 保存 Available_End_Strings
            try:
                end_strings = list(self.components.combobox_end['values'])
                current_settings['Available_End_Strings'] = end_strings
            except Exception:
                current_settings['Available_End_Strings'] = ["root"]
            
            # 讀取完整的 setup 資料
            full_setup = load_setup()
            # 更新 DUT 分層
            full_setup['DUT_Control'].update(current_settings)
            
            # 保存到檔案
            save_setup(full_setup)
            print(f"[DEBUG] 設定已保存到 DUT_Control 分層: {current_settings}")
            
            # 停止所有執行緒
            if self.stop_event:
                self.stop_event.set()
                
            # 關閉程式
            self.root.destroy()
            
        except Exception as e:
            print(f'[ERROR] 關閉程式時發生錯誤: {e}')
            # 即使發生錯誤也要關閉程式
            self.root.destroy()

    def get_settings(self):
        # 回傳 DUT_Control 分頁所有設定
        settings = {}
        c = self.components
        settings['Serial_COM_Port'] = c.combobox_com.get()
        settings['Command_Timeout_Seconds'] = c.entry_timeout.get()
        settings['Command_End_String'] = c.combobox_end.get()
        settings['UI_Font_Size'] = str(c.ui_font_scale.get())
        settings['Content_Font_Size'] = str(c.content_font_scale.get())
        settings['Title'] = self.root.title() if hasattr(self.root, 'title') else 'VALO360 指令通'
        try:
            end_strings = list(c.combobox_end['values'])
        except Exception:
            end_strings = ["root"]
        settings['Available_End_Strings'] = end_strings
        settings['Default_IP_Address'] = c.entry_ip.get() if hasattr(c, 'entry_ip') else '192.168.11.143'
        settings['Window_Width'] = str(self.root.winfo_width())
        settings['Window_Height'] = str(self.root.winfo_height())
        settings['Last_Selected_Command_Section'] = c.section_var.get() if hasattr(c, 'section_var') else '全部指令'
        return settings

    def load_initial_settings(self):
        """程式啟動時讀取並應用設定"""
        try:
            print(f"[DEBUG] load_initial_settings 開始，self.setup = {self.setup}")
            
            # 讀取 COM 口設定
            com_port = self.setup.get('Serial_COM_Port', '')
            print(f"[DEBUG] 讀取到 COM 口設定: '{com_port}'")
            
            if com_port:
                print(f"[DEBUG] COM 口不為空，開始刷新 COM 口列表")
                # 刷新 COM 口列表
                self.handlers.refresh_com_ports()
                # 如果設定的 COM 口在列表中，則選擇它
                available_ports = self.components.combobox_com['values']
                print(f"[DEBUG] 可用的 COM 口: {available_ports}")
                if com_port in available_ports:
                    self.components.combobox_com.set(com_port)
                    print(f"[DEBUG] 已設定 COM 口為: {com_port}")
                else:
                    print(f"[DEBUG] COM 口 {com_port} 不在可用列表中")
            else:
                print(f"[DEBUG] COM 口為空，跳過設定")
            
            # 讀取超時設定
            timeout = self.setup.get('Command_Timeout_Seconds', '30')
            print(f"[DEBUG] 讀取到超時設定: {timeout}")
            self.components.entry_timeout.delete(0, tk.END)
            self.components.entry_timeout.insert(0, timeout)
            
            # 讀取結束字串設定
            end_string = self.setup.get('Command_End_String', 'root')
            print(f"[DEBUG] 讀取到結束字串設定: {end_string}")
            self.components.combobox_end.set(end_string)
            
            # 讀取 IP 地址設定
            default_ip = self.setup.get('Default_IP_Address', '192.168.11.143')
            print(f"[DEBUG] 讀取到 IP 地址設定: {default_ip}")
            self.components.entry_ip.delete(0, tk.END)
            self.components.entry_ip.insert(0, default_ip)
            
            # 讀取字體大小設定
            ui_font_size = int(self.setup.get('UI_Font_Size', '12'))
            content_font_size = int(self.setup.get('Content_Font_Size', '12'))
            print(f"[DEBUG] 讀取到字體設定: UI={ui_font_size}, Content={content_font_size}")
            self.components.ui_font_scale.set(ui_font_size)
            self.components.content_font_scale.set(content_font_size)
            
            # 應用字體設定
            self.components.update_ui_fonts(ui_font_size)
            self.components.update_content_fonts(content_font_size)
            
            # 讀取最後選擇的指令分類
            last_section = self.setup.get('Last_Selected_Command_Section', '全部指令')
            print(f"[DEBUG] 讀取到指令分類設定: {last_section}")
            self.components.section_var.set(last_section)
            self.components.update_cmd_list()
            
            print(f"[DEBUG] 已載入設定: COM={com_port}, Timeout={timeout}, EndString={end_string}")
            
        except Exception as e:
            print(f"[ERROR] 載入設定時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

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