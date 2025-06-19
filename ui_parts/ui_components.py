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
        self.last_size = (0, 0)
        self.led_blinking = False
        self.main_frame = None
        self.radiobutton_frame = None
        self.section_radiobuttons = []
        # 控制下拉列表最大顯示項目數
        self.max_dropdown_items = 20  # 將下拉菜單最大顯示項目數從10改為20
        # 下拉列表字典
        self.dropdown_boxes = {}
        # 獲取高亮關鍵字
        self.highlight_keywords = getattr(parent, 'highlight_keywords', {})
        print(f"[DEBUG] 載入了 {len(self.highlight_keywords)} 個高亮關鍵字到 UIComponents")
        self.init_ui()
        # 讀取 setup.txt 的寬高
        width = int(self.parent.setup.get('Window_Width', 800))
        height = int(self.parent.setup.get('Window_Height', 600))
        # 視窗最大化
        try:
            self.parent.root.state('zoomed')  # Windows
        except Exception:
            self.parent.root.attributes('-zoomed', True)  # Linux
        self.last_size = (width, height)
        self.parent.root.bind('<Configure>', self.on_window_resize)
        # 綁定 Enter 鍵執行指令
        self.parent.root.bind('<Return>', lambda e: self.parent.handlers.on_execute())
        
    def center_window(self, width, height):
        self.parent.root.update_idletasks()
        screen_width = self.parent.root.winfo_screenwidth()
        screen_height = self.parent.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.parent.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def init_ui(self):
        # 建立主框架
        self.main_frame = ttk.PanedWindow(self.parent.parent, orient='horizontal', style="Main.TFrame")
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        # 配置主框架的 grid
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=2)
        
        # --- 左側控制面板 ---
        # 直接使用 Frame 而非滾動區域，因為我們已經優化佈局使其不需要滾動
        self.left_panel = ttk.LabelFrame(self.main_frame, text='控制面板', padding=5, style="Main.TLabelframe")
        
        # 建立右側面板
        self.right_panel = ttk.LabelFrame(self.main_frame, text='回應內容', padding=5, style="Main.TLabelframe")
        
        # 將左右面板加入 PanedWindow
        self.main_frame.add(self.left_panel, weight=1)
        self.main_frame.add(self.right_panel, weight=2)
        
        # 綁定 PanedWindow 分割位置變更事件
        self.main_frame.bind('<ButtonRelease-1>', self.on_pane_position_changed)
        
        # 初始化各個元件
        self.init_com_components()
        self.init_cmd_components()
        self.init_ping_components()
        self.init_settings_components()
        self.init_output_components()
        self.init_progress_components()
        
        # 強化 left_panel 內所有 Entry/Combobox 的 <Return> 綁定
        for widget in [self.combobox_cmd, self.entry_timeout, self.combobox_end, self.entry_ip, self.combobox_com]:
            widget.bind('<Return>', lambda e: self.parent.handlers.on_execute())
            
        # 將執行按鈕移回 left_panel 最下方，並用 grid 固定
        self.init_exec_button_left_panel()
        # 統一所有 left_panel 內 tk.Button hover 為藍底白字
        for widget in self.left_panel.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, tk.Button):
                    child.bind("<Enter>", lambda e, b=child: b.config(bg="#2196f3", fg="white"))
                    child.bind("<Leave>", lambda e, b=child: b.config(bg="white", fg="black"))
        
        # 恢復 PanedWindow 分割位置（延遲執行，確保視窗已完全載入）
        self.parent.root.after(200, self.restore_pane_position)
        
        # 顯示版本信息
        self.parent.root.after(500, lambda: self.show_notification("VALO360 指令通 V1.12 已啟動", "blue", 5000))
        
        # 顯示歡迎訊息
        welcome_message = "歡迎使用 VALO360 指令通！點擊「使用說明」按鈕查看詳細操作指南。"
        self.parent.root.after(6000, lambda: self.show_notification(welcome_message, "green", 8000))
        
        # 顯示系統狀態
        self.parent.root.after(15000, self.show_system_status)
        
        # 顯示基本操作提示
        basic_tips = "基本操作：選擇COM口和指令後點擊「執行指令」按鈕。通知區域可使用 +/- 調整文字大小。"
        self.parent.root.after(25000, lambda: self.show_notification(basic_tips, "blue", 10000))

    def init_com_components(self):
        com_frame = ttk.Frame(self.left_panel, style="TFrame")
        com_frame.grid(row=0, column=0, sticky='ew', pady=3)  # 減少間距
        com_frame.columnconfigure(0, weight=0)  # 標籤不需要擴展
        com_frame.columnconfigure(1, weight=1)  # 下拉選單擴展
        com_frame.columnconfigure(2, weight=0)  # 按鈕不需要擴展
        com_frame.columnconfigure(3, weight=0)  # LED不需要擴展
        
        self.label_com = ttk.Label(com_frame, text='COM口:', style="TLabel")
        self.label_com.grid(row=0, column=0, sticky='w')
        
        # 獲取可用的 COM 口列表
        com_values = list_com_ports()
        
        # 創建 COM 口下拉選單
        self.combobox_com = ttk.Combobox(com_frame, values=com_values, state='readonly', width=15)
        self.combobox_com.grid(row=0, column=1, padx=5, sticky='ew')
        
        # 注意：不在這裡設定預設值，由 load_initial_settings 統一處理
        print(f"[DEBUG] init_com_components: 已創建 COM 口選單，可用 COM 口: {com_values}")
        
        # 確保 parent.handlers 存在
        refresh_command = None
        if hasattr(self.parent, 'handlers') and hasattr(self.parent.handlers, 'refresh_com_ports'):
            refresh_command = self.parent.handlers.refresh_com_ports
        else:
            # 如果 handlers 不存在，提供一個臨時的空函數
            refresh_command = lambda: None
            print("[WARNING] handlers 不存在或沒有 refresh_com_ports 方法")
        
        self.btn_refresh = tk.Button(com_frame, text='刷新', command=refresh_command,
                                   bg='#e0e0e0', fg='black', activebackground='#2196f3', activeforeground='black')
        self.btn_refresh.grid(row=0, column=2, padx=3)  # 減少間距
        
        # 增大 LED 指示燈
        self.status_canvas = tk.Canvas(com_frame, width=40, height=40, bg='white', highlightthickness=0)  # 增大尺寸
        self.status_canvas.grid(row=0, column=3, padx=3)  # 減少間距
        self.status_light = self.status_canvas.create_oval(5, 5, 35, 35, fill='black')  # 調整橢圓位置和大小
        self.led_blinking = False

    def init_cmd_components(self):
        section_frame = ttk.Frame(self.left_panel, style="TFrame")
        section_frame.grid(row=1, column=0, sticky='ew', pady=5)
        section_frame.columnconfigure(0, weight=1)
        self.section_var = tk.StringVar()
        
        # 從 command.txt 動態讀取分類
        self.sections = []  # 移除預設的 '全部指令'
        try:
            with open(COMMAND_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('==') and line.endswith('=='):
                        section_name = line.strip('=')
                        if section_name and section_name not in self.sections:
                            self.sections.append(section_name)
        except Exception as e:
            print(f"[ERROR] 讀取分類時發生錯誤: {e}")
            
        # 如果沒有讀取到任何分類，添加一個預設分類
        if not self.sections:
            self.sections = ['全部指令']
            
        # 設定預設選中的分類
        if self.sections:
            self.section_var.set(self.sections[0])
        
        # 限制每行最多顯示4個按鈕
        max_buttons_per_row = 4
        self.section_radiobuttons = []
        
        for i, sec in enumerate(self.sections):
            # 計算行和列位置
            row = i // max_buttons_per_row
            col = i % max_buttons_per_row
            
            rb = tk.Radiobutton(
                section_frame, text=sec, variable=self.section_var, value=sec, 
                command=self.update_cmd_list,
                bg='#d9d9d9', fg='black', selectcolor='#d9d9d9', 
                activebackground='#2196f3', activeforeground='white',
                indicatoron=0, relief='flat', borderwidth=1, width=8, height=1,
                font=('Microsoft JhengHei UI', int(self.parent.setup.get('UI_Font_Size', '12')))
            )
            rb.grid(row=row, column=col, padx=1, pady=1, sticky='ew')
            rb.bind("<Enter>", lambda e, b=rb: b.config(bg="#2196f3", fg='white'))
            rb.bind("<Leave>", lambda e, b=rb: self.update_radio_bg())
            self.section_radiobuttons.append(rb)
            
            # 設置列的權重，使按鈕平均分配空間
            section_frame.columnconfigure(col, weight=1)
        
        self.update_radio_bg()

        # 添加說明文字（減少高度）
        self.section_description = ttk.Label(
            section_frame, 
            text=self.get_section_description(self.section_var.get()),
            style="TLabel",
            wraplength=300
        )
        # 將說明文字放在按鈕下方的新行
        last_row = (len(self.sections) - 1) // max_buttons_per_row + 1
        self.section_description.grid(row=last_row, column=0, columnspan=max_buttons_per_row, pady=2, sticky='w')
        
        cmd_frame = ttk.Frame(self.left_panel, style="TFrame")
        cmd_frame.grid(row=2, column=0, sticky='ew', pady=3)  # 減少間距
        cmd_frame.columnconfigure(1, weight=1)
        self.label_cmd = ttk.Label(cmd_frame, text='指令:', style="TLabel")
        self.label_cmd.grid(row=0, column=0, sticky='w')
        
        # 改進下拉選單的樣式設置
        font_size = int(self.parent.setup.get('UI_Font_Size', '12'))
        style = ttk.Style()
        style.configure('Custom.TCombobox', font=('Microsoft JhengHei UI', font_size))
        
        self.combobox_cmd = ttk.Combobox(cmd_frame, state='readonly', width=25, style='Custom.TCombobox')
        self.combobox_cmd.grid(row=0, column=1, padx=5, sticky='ew')
        
        # 設置combobox樣式與事件綁定
        self.combobox_cmd.bind("<<ComboboxSelected>>", lambda e: self.on_cmd_selected())
        
        # 初始化顏色映射字典
        self.cmd_colors = {}
        
        # 添加打開下拉列表時的回調，用於限制高度
        self.combobox_cmd.bind("<<ComboboxOpened>>", self.limit_dropdown_height)

    def get_section_description(self, section):
        # 預設描述
        default_descriptions = {
            '全部指令': '顯示所有可用的指令',
            '單板指令': '用於單板測試的指令集',
            '整機指令': '用於整機測試的指令集',
            '驗證喇叭': '用於驗證喇叭的指令集',
            '出貨指令': '用於出貨測試的指令集'
        }
        
        # 如果有預設描述，則使用預設描述
        if section in default_descriptions:
            return default_descriptions[section]
        
        # 否則生成一個通用描述
        return f'用於{section}的指令集'

    def init_ping_components(self):
        print('[DEBUG] handlers in init_ping_components:', self.parent.handlers)
        ping_frame = ttk.LabelFrame(self.left_panel, text='Ping 檢查', padding=5, style="TLabelframe")
        ping_frame.grid(row=3, column=0, sticky='ew', pady=5)  # 減少間距
        ip_frame = ttk.Frame(ping_frame, style="TFrame")
        ip_frame.grid(row=0, column=0, sticky='ew', pady=1)  # 減少間距
        ip_frame.columnconfigure(1, weight=1)
        self.label_ip = ttk.Label(ip_frame, text='IP地址:', style="TLabel")
        self.label_ip.grid(row=0, column=0, sticky='w')
        self.entry_ip = ttk.Entry(ip_frame, width=15)
        self.entry_ip.grid(row=0, column=1, padx=5, sticky='ew')
        default_ip = self.parent.setup.get('Default_IP_Address', '192.168.11.143')
        self.entry_ip.delete(0, tk.END)
        self.entry_ip.insert(0, default_ip)
        self.btn_ping = tk.Button(ip_frame, text='Ping', command=lambda: self.parent.handlers.check_ping(), bg='white', fg='black')
        self.btn_ping.grid(row=0, column=2, padx=5)
        self.btn_ping.bind("<Enter>", lambda e: self.btn_ping.config(bg="#ff9999"))
        self.btn_ping.bind("<Leave>", lambda e: self.btn_ping.config(bg="white"))

    def init_settings_components(self):
        settings_frame = ttk.LabelFrame(self.left_panel, text='設定', padding=5, style="TLabelframe")
        settings_frame.grid(row=4, column=0, sticky='ew', pady=5)  # 減少間距
        
        # 結束字串設定
        end_frame = ttk.Frame(settings_frame, style="TFrame")
        end_frame.grid(row=0, column=0, sticky='ew', pady=2)  # 減少間距
        self.label_end = ttk.Label(end_frame, text='結束字串:', style="TLabel")
        self.label_end.grid(row=0, column=0, sticky='w')
        self.combobox_end = ttk.Combobox(end_frame, width=15)
        self.combobox_end.grid(row=0, column=1, padx=5, sticky='ew')
        self.update_end_strings()
        self.combobox_end.set(self.parent.setup.get('Command_End_String', 'root'))
        # 加入刪除按鈕
        self.btn_remove_end = tk.Button(end_frame, text='-', command=self.parent.handlers.remove_end_string, width=2, bg='#ffcccc', fg='black')
        self.btn_remove_end.grid(row=0, column=2, padx=2)
        
        # 超時設定
        timeout_frame = ttk.Frame(settings_frame, style="TFrame")
        timeout_frame.grid(row=1, column=0, sticky='ew', pady=2)  # 減少間距
        self.label_timeout = ttk.Label(timeout_frame, text='超時(秒):', style="TLabel")
        self.label_timeout.grid(row=0, column=0, sticky='w')
        self.entry_timeout = ttk.Entry(timeout_frame, width=8)
        self.entry_timeout.grid(row=0, column=1, padx=5, sticky='ew')
        self.entry_timeout.insert(0, self.parent.setup.get('Command_Timeout_Seconds', '30'))
        
        # 添加自動執行勾選框
        auto_exec_frame = ttk.Frame(settings_frame, style="TFrame")
        auto_exec_frame.grid(row=2, column=0, sticky='ew', pady=2)  # 減少間距
        self.auto_exec_var = tk.BooleanVar(value=self.parent.setup.get('Auto_Execute', False))
        self.auto_exec_checkbox = tk.Checkbutton(
            auto_exec_frame, 
            text='啟動時自動執行指令',
            variable=self.auto_exec_var,
            command=self.on_auto_exec_changed,
            bg='white',
            activebackground='white',
            highlightthickness=0,
            font=('Microsoft JhengHei UI', int(self.parent.setup.get('UI_Font_Size', '12')))
        )
        self.auto_exec_checkbox.grid(row=0, column=0, sticky='w', padx=5)
        
        # 字體大小設定 - 將兩個字體設定合併到一行
        font_frame = ttk.Frame(settings_frame, style="TFrame")
        font_frame.grid(row=3, column=0, sticky='ew', pady=2)  # 減少間距
        font_frame.columnconfigure(1, weight=1)
        font_frame.columnconfigure(3, weight=1)
        
        # UI字體大小設定
        self.label_ui_font = ttk.Label(font_frame, text='介面字體:', style="TLabel")
        self.label_ui_font.grid(row=0, column=0, sticky='w', padx=(0,2))
        
        font_controls_frame = ttk.Frame(font_frame, style="TFrame")
        font_controls_frame.grid(row=0, column=1, sticky='ew')
        
        self.btn_ui_font_minus = tk.Button(font_controls_frame, text='－', width=2, command=lambda: self.ui_font_scale.set(self.ui_font_scale.get()-1))
        self.btn_ui_font_minus.grid(row=0, column=0, padx=1)
        
        self.ui_font_scale = tk.Scale(font_controls_frame, from_=8, to=20, orient='horizontal', 
                                    command=self.parent.handlers.change_ui_font_size, length=80, bg='white', fg='black', 
                                    highlightthickness=0)
        self.ui_font_scale.grid(row=0, column=1, padx=1)
        self.ui_font_scale.set(int(self.parent.setup.get('UI_Font_Size', '12')))
        
        self.btn_ui_font_plus = tk.Button(font_controls_frame, text='＋', width=2, command=lambda: self.ui_font_scale.set(self.ui_font_scale.get()+1))
        self.btn_ui_font_plus.grid(row=0, column=2, padx=1)
        
        # 內容字體大小設定
        self.label_content_font = ttk.Label(font_frame, text='內容字體:', style="TLabel")
        self.label_content_font.grid(row=0, column=2, sticky='w', padx=(10,2))
        
        # 添加內容字體的控制框架
        content_font_controls_frame = ttk.Frame(font_frame, style="TFrame")
        content_font_controls_frame.grid(row=0, column=3, sticky='ew')
        
        # 添加減號按鈕
        self.btn_content_font_minus = tk.Button(content_font_controls_frame, text='－', width=2, 
                                              command=lambda: self.content_font_scale.set(self.content_font_scale.get()-1))
        self.btn_content_font_minus.grid(row=0, column=0, padx=1)
        
        self.content_font_scale = tk.Scale(content_font_controls_frame, from_=8, to=20, orient='horizontal', 
                                         command=self.parent.handlers.change_content_font_size, length=80, bg='white', fg='black', 
                                         highlightthickness=0)
        self.content_font_scale.grid(row=0, column=1, padx=1)
        self.content_font_scale.set(int(self.parent.setup.get('Content_Font_Size', '12')))
        
        # 添加加號按鈕
        self.btn_content_font_plus = tk.Button(content_font_controls_frame, text='＋', width=2, 
                                             command=lambda: self.content_font_scale.set(self.content_font_scale.get()+1))
        self.btn_content_font_plus.grid(row=0, column=2, padx=1)
        
        # 按鈕區 - 改為水平排列
        btn_frame = ttk.Frame(self.left_panel, style="TFrame")
        btn_frame.grid(row=5, column=0, sticky='ew', pady=5)  # 減少間距
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)
        
        self.btn_clear = ttk.Button(btn_frame, text='清空回應', command=self.parent.handlers.clear_output, style='Blue.TButton')
        self.btn_clear.grid(row=0, column=0, padx=2, sticky='ew')
        
        self.btn_backup = ttk.Button(btn_frame, text='備份Log', command=self.parent.handlers.backup_output, style='Blue.TButton')
        self.btn_backup.grid(row=0, column=1, padx=2, sticky='ew')
        
        self.btn_guide = ttk.Button(btn_frame, text='使用說明', command=self.parent.handlers.toggle_guide, style='Blue.TButton')
        self.btn_guide.grid(row=0, column=2, padx=2, sticky='ew')
        
        # 將 ui_font_scale 的 command 綁定為 handlers.change_ui_font_size，避免 lambda 導致無法正確更新
        self.ui_font_scale.config(command=self.parent.handlers.change_ui_font_size)

    def init_output_components(self):
        try:
            # 建立輸出區域
            self.text_output = scrolledtext.ScrolledText(
                self.right_panel,
                wrap=tk.WORD,
                width=50,
                height=20,
                font=('Microsoft JhengHei UI', int(self.parent.setup.get('Content_Font_Size', '12')))
            )
            self.text_output.grid(row=0, column=0, sticky='nsew')
            self.right_panel.grid_rowconfigure(0, weight=1)
            self.right_panel.grid_columnconfigure(0, weight=1)
            
            # 設定 tag
            self.text_output.tag_configure("send", foreground="blue")
            self.text_output.tag_configure("end", foreground="green")  # 收到結束字串為綠色
            self.text_output.tag_configure("timeout", foreground="red")  # 超時為紅色
            self.text_output.tag_configure("purple", foreground="#800080")  # 紫色
            self.text_output.tag_configure("guide_title", foreground="#006400", font=('Microsoft JhengHei UI', int(self.parent.setup.get('Content_Font_Size', '12')) + 2, 'bold'))  # 使用說明標題
            self.text_output.tag_configure("error", foreground="red")  # 錯誤訊息為紅色
            self.text_output.tag_configure("success", foreground="green")  # 成功訊息為綠色
            self.text_output.tag_configure("warning", foreground="orange")  # 警告訊息為橙色
            
            # 為高亮關鍵字定義標籤
            print(f"[DEBUG] 初始化關鍵字高亮標籤，parent={self.parent}")
            if hasattr(self.parent, 'highlight_keywords'):
                print(f"[DEBUG] highlight_keywords={self.parent.highlight_keywords}")
                for keyword, color in self.parent.highlight_keywords.items():
                    print(f"[DEBUG] 創建關鍵字標籤: {keyword} -> {color}")
                    self.text_output.tag_configure(color, foreground=color)
            else:
                print(f"[WARNING] parent 沒有 highlight_keywords 屬性")
            
            # 設定唯讀
            self.text_output.config(state='disabled')
            
            # 添加右鍵菜單
            self.output_context_menu = tk.Menu(self.text_output, tearoff=0)
            self.output_context_menu.add_command(label="複製", command=self.copy_selected_text)
            self.output_context_menu.add_command(label="全選", command=self.select_all_text)
            self.output_context_menu.add_separator()
            self.output_context_menu.add_command(label="清空", command=self.parent.handlers.clear_output)
            self.text_output.bind("<Button-3>", self.show_output_context_menu)
            
        except Exception as e:
            print(f"Error in init_output_components: {e}")
            import traceback
            traceback.print_exc()
            raise

    def init_exec_button_left_panel(self):
        # 執行指令大圓角按鈕（預設灰色，hover 綠色），用 grid 固定在 left_panel 最下方
        exec_frame = ttk.Frame(self.left_panel, style="TFrame")
        exec_frame.grid(row=999, column=0, sticky='ew', pady=5)  # 減少間距
        exec_frame.columnconfigure(0, weight=1)
        self.btn_exec = tk.Button(exec_frame, text='執行指令',
            command=self.parent.handlers.on_execute,
                                 bg='#cccccc', fg='black',
                                 activebackground='#4caf50', activeforeground='white',
                                 font=('Microsoft JhengHei UI', 18, 'bold'),  # 稍微減小字體
                                 relief='flat', borderwidth=0, highlightthickness=0)
        self.btn_exec.grid(row=0, column=0, sticky='ew', padx=4, pady=4)  # 減少間距
        self.btn_exec.bind("<Enter>", lambda e: self.btn_exec.config(bg="#4caf50", fg='white'))
        self.btn_exec.bind("<Leave>", lambda e: self.btn_exec.config(bg="#cccccc", fg='black'))
        
        # 增加間距，將倒數計時/通知區域與執行按鈕分開
        ttk.Separator(exec_frame, orient='horizontal').grid(row=1, column=0, sticky='ew', pady=10)
        
        # 倒數計時標籤 - 移到執行指令按鈕下方
        countdown_frame = ttk.Frame(exec_frame, style="TFrame")
        countdown_frame.grid(row=2, column=0, sticky='ew', pady=2)  # 減少間距
        countdown_frame.columnconfigure(0, weight=1)
        
        # 通知區域控制框架 - 添加文字大小調整按鈕
        notification_control_frame = ttk.Frame(countdown_frame)
        notification_control_frame.grid(row=0, column=0, sticky='ew')
        notification_control_frame.columnconfigure(1, weight=1)
        
        # 添加減小字體按鈕
        self.btn_notification_font_minus = tk.Button(
            notification_control_frame, 
            text='－', 
            width=2, 
            command=lambda: self.change_notification_font_size(-1),
            bg='#e0e0e0', fg='black'
        )
        self.btn_notification_font_minus.grid(row=0, column=0, padx=1)
        
        # 通知區域標題
        notification_title = ttk.Label(notification_control_frame, text="通知區域", style="TLabel")
        notification_title.grid(row=0, column=1)
        
        # 添加增大字體按鈕
        self.btn_notification_font_plus = tk.Button(
            notification_control_frame, 
            text='＋', 
            width=2, 
            command=lambda: self.change_notification_font_size(1),
            bg='#e0e0e0', fg='black'
        )
        self.btn_notification_font_plus.grid(row=0, column=2, padx=1)
        
        # 倒數計時/通知標籤 - 使用更大的字體和明顯的顏色，並增加高度，添加黑色邊框
        self.notification_font_size = int(self.parent.setup.get('Notification_Font_Size', '14'))
        self.label_countdown = tk.Label(
            countdown_frame, 
            text='', 
            font=('Microsoft JhengHei UI', self.notification_font_size, 'bold'),
            fg='red',  # 紅色文字
            bg='white',  # 白色背景
            anchor='center',
            height=3,  # 增加高度以容納更多文字
            wraplength=300,  # 設置文字換行寬度
            relief='solid',  # 添加實線邊框
            borderwidth=1,  # 邊框寬度
        )
        self.label_countdown.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
        
        # 讓 left_panel 最下方 row 有 weight，確保按鈕永遠可見
        self.left_panel.grid_rowconfigure(999, weight=0)  # 改為 weight=0，避免執行按鈕佔用太多空間

    def init_progress_components(self):
        """初始化進度條組件"""
        self.progress = ttk.Progressbar(
            self.right_panel,
            mode='determinate',
            style="gray.Horizontal.TProgressbar",
            length=200
        )
        self.progress.grid(row=1, column=0, sticky='ew', pady=5)
        self.progress['value'] = 0
        # 確保進度條始終顯示
        self.progress.grid_remove()  # 初始隱藏
        self.right_panel.rowconfigure(1, weight=0)  # 進度條行不擴展

    def show_progress(self, show=True):
        """控制進度條顯示/隱藏"""
        print(f"[DEBUG] show_progress: show={show}")
        if show:
            self.progress.grid()
        else:
            self.progress.grid_remove()

    def update_progress(self, value, style="blue.Horizontal.TProgressbar"):
        """更新進度條值和樣式"""
        print(f"[DEBUG] update_progress: value={value}, style={style}")
        self.progress.config(style=style, value=value)
        self.progress.grid()  # 確保進度條顯示

    def reset_progress(self):
        """重置進度條並隱藏"""
        try:
            print("[DEBUG] reset_progress: set progress to 0 and hide")
            self.progress['value'] = 0
            self.show_progress(False)  # 隱藏進度條
            
            # 取消所有與進度條相關的定時器
            if hasattr(self.parent, 'root'):
                # 檢查是否有標記的進度條更新任務
                if hasattr(self.parent.handlers, '_progress_update_job') and self.parent.handlers._progress_update_job:
                    try:
                        self.parent.root.after_cancel(self.parent.handlers._progress_update_job)
                        self.parent.handlers._progress_update_job = None
                        print("[DEBUG] 已取消進度條更新任務")
                    except Exception as e:
                        print(f"[ERROR] 取消進度條更新任務時發生錯誤: {e}")
        except Exception as e:
            print(f"[ERROR] 重置進度條時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def update_radio_bg(self):
        selected = self.section_var.get()
        for rb, sec in zip(self.section_radiobuttons, self.sections):
            if rb['state'] == 'disabled':
                rb.config(bg="#e0e0e0", fg="#b0b0b0", activebackground="#e0e0e0", activeforeground="#b0b0b0")
            elif selected == sec:
                rb.config(bg="#2196f3", fg="white", activebackground="#2196f3", activeforeground="white")
            else:
                rb.config(bg="#d9d9d9", fg="black", activebackground="#d9d9d9", activeforeground="black")

    def update_cmd_list(self):
        self.update_radio_bg()
        section = self.section_var.get()
        # 更新說明文字
        self.section_description.config(text=self.get_section_description(section))
        # 重新讀取 command.txt
        self.parent.commands_by_section = self.parent.handlers.parse_commands_by_section()
        cmds = self.parent.commands_by_section.get(section, {})
        if not cmds and section != '全部指令':  # 如果沒有找到對應分類的指令，使用全部指令
            cmds = self.parent.commands_by_section.get('全部指令', {})
        self.combobox_cmd['values'] = list(cmds.keys())
        # 自動選中第一個指令
        if cmds:
            first_cmd = list(cmds.keys())[0]
            self.combobox_cmd.set(first_cmd)
        else:
            self.combobox_cmd.set('')

    def update_end_strings(self):
        try:
            end_strings = json.loads(self.parent.setup.get('Available_End_Strings', '["root"]'))
        except Exception:
            end_strings = ['root']
        self.combobox_end['values'] = end_strings

    def add_to_buffer(self, text, tag=None):
        # 如果正在顯示使用說明，則不添加內容
        if hasattr(self.parent, 'showing_guide') and self.parent.showing_guide:
            return
            
        # 設為可編輯狀態
        self.text_output.configure(state='normal')
        
        # 若是 [送出] 開頭自動用 send tag
        if text.startswith('[發送]'):
            self.text_output.insert(tk.END, text, "send")
        # 若是 [結束] 開頭自動用 end tag
        elif text.startswith('[結束]'):
            self.text_output.insert(tk.END, text, "end")
        # 若是包含 inserted 的行，使用 purple tag
        elif "inserted" in text:
            self.text_output.insert(tk.END, text, "purple")
        # 其他情況使用指定的 tag
        elif tag:
            self.text_output.insert(tk.END, text, tag)
        else:
            # 檢查是否包含關鍵字，如果有則只高亮關鍵字部分
            if hasattr(self.parent, 'highlight_keywords') and self.parent.highlight_keywords:
                # 先插入文字
                start_pos = self.text_output.index(tk.END)
                self.text_output.insert(tk.END, text)
                
                # 檢查關鍵字並應用標籤
                for keyword, color in self.parent.highlight_keywords.items():
                    if keyword in text:
                        # 找出所有關鍵字出現的位置
                        start = start_pos
                        while True:
                            # 從當前位置開始搜索關鍵字
                            pos = self.text_output.search(keyword, start, tk.END)
                            if not pos:
                                break
                                
                            # 計算關鍵字結束位置
                            end_pos = f"{pos}+{len(keyword)}c"
                            
                            # 應用標籤 - 只對關鍵字本身應用
                            try:
                                self.text_output.tag_add(color, pos, end_pos)
                            except Exception as e:
                                print(f"[ERROR] 應用標籤時發生錯誤: {e}")
                            
                            # 更新搜索起點
                            start = end_pos
            else:
                # 如果沒有關鍵字，直接插入文字
                self.text_output.insert(tk.END, text)
                
        # 自動捲到最底
        self.text_output.see(tk.END)
        # 設回唯讀狀態
        self.text_output.configure(state='disabled')

    def flush_buffer(self):
        """將緩衝區的文字一次性添加到輸出區域"""
        if not hasattr(self.parent, 'text_buffer') or not self.parent.text_buffer:
            return
            
        if not hasattr(self, 'text_output'):
            print("[ERROR] text_output 不存在，無法刷新緩衝區")
            return
            
        try:
            self.text_output.configure(state='normal')
            for text, tag in self.parent.text_buffer:
                if tag:
                    self.text_output.insert(tk.END, text, tag)
                else:
                    self.text_output.insert(tk.END, text)
            self.text_output.see(tk.END)  # 自動捲到最底
            self.text_output.configure(state='disabled')  # 設回唯讀狀態
            self.parent.text_buffer = []
        except Exception as e:
            print(f"[ERROR] 刷新緩衝區時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def update_ui_fonts(self, size=None):
        try:
            if size is None:
                size = int(self.ui_font_scale.get())
            font = ('Microsoft JhengHei UI', size)
            # 更新所有標籤和按鈕
            widgets = [
                self.label_com, self.label_cmd, self.label_end, self.label_timeout,
                self.label_ui_font, self.label_content_font, self.btn_refresh,
                self.btn_clear, self.btn_backup, self.btn_guide, self.label_ip, self.btn_ping
            ]
            for w in widgets:
                if w.winfo_exists():
                    try:
                        w.configure(font=font)
                    except Exception:
                        # 如果設定字體失敗，嘗試使用其他方式
                        try:
                            w['font'] = font
                        except Exception:
                            pass
            # 更新 section_radiobuttons 字體
            for rb in getattr(self, 'section_radiobuttons', []):
                if rb.winfo_exists():
                    try:
                        rb.configure(font=font)
                    except Exception:
                        try:
                            rb['font'] = font
                        except Exception:
                            pass
            # 更新輸入框和下拉選單
            for widget in [self.combobox_com, self.combobox_cmd, self.combobox_end, 
                         self.entry_timeout, self.entry_ip]:
                if widget.winfo_exists():
                    try:
                        widget.configure(font=('Consolas', size))
                    except Exception:
                        try:
                            widget['font'] = ('Consolas', size)
                        except Exception:
                            pass
            # 更新 ttk 樣式
            try:
                style = ttk.Style()
                style.configure("TLabelframe.Label", font=font)
                style.configure("TLabelframe", font=font)
                style.configure("TLabel", font=font)
            except Exception:
                pass
            # 強制更新 UI
            self.parent.root.update_idletasks()
        except Exception as e:
            print(f"[DEBUG] 更新介面字體時發生錯誤: {e}")
            # 不要讓錯誤影響程式運行

    def update_content_fonts(self, size=None):
        try:
            if size is None:
                size = int(self.content_font_scale.get())
            content_font = ('Consolas', size)
            # 更新文字輸出區域
            if self.text_output.winfo_exists():
                try:
                    self.text_output.configure(font=content_font)
                except Exception:
                    try:
                        self.text_output['font'] = content_font
                    except Exception:
                        pass
            # 更新所有下拉選單與輸入框
            for widget in [self.combobox_com, self.combobox_cmd, self.combobox_end, self.entry_timeout, self.entry_ip]:
                if widget.winfo_exists():
                    try:
                        widget.configure(font=content_font)
                    except Exception:
                        try:
                            widget['font'] = content_font
                        except Exception:
                            pass
            # 根據字體大小自動調整 combobox_cmd 寬度
            min_width = 25
            width = max(min_width, int(size * 2.2))
            try:
                self.combobox_cmd.config(width=width)
            except Exception:
                pass
            # 強制 combobox 下拉選單選項字體同步
            try:
                self.parent.root.option_add('*TCombobox*Listbox.font', content_font)
            except Exception as e:
                print(f'[DEBUG] Combobox Listbox 字體設置失敗: {e}')
            # 更新使用說明視窗
            if self.parent.guide_window and self.parent.guide_window.winfo_exists():
                for widget in self.parent.guide_window.winfo_children():
                    if isinstance(widget, scrolledtext.ScrolledText) and widget.winfo_exists():
                        try:
                            widget.configure(font=content_font)
                        except Exception:
                            try:
                                widget['font'] = content_font
                            except Exception:
                                pass
            self.parent.root.update_idletasks()
        except Exception as e:
            print(f"[DEBUG] 更新內容字體時發生錯誤: {e}")
            # 不要讓錯誤影響程式運行

    def on_window_resize(self, event):
        # 只在主視窗且尺寸真的有變時記錄
        if event.widget == self.parent.root:
            w, h = event.width, event.height
            if (w, h) != self.last_size and w > 200 and h > 200:
                self.last_size = (w, h)
                # 更新當前設定
                self.parent.setup['Window_Width'] = str(w)
                self.parent.setup['Window_Height'] = str(h)
                # 保存完整的設定結構
                from config import load_setup, save_setup
                full_setup = load_setup()
                full_setup['DUT_Control'].update({
                    'Window_Width': str(w),
                    'Window_Height': str(h)
                })
                save_setup(full_setup)
                print(f"[DEBUG] 視窗大小已保存: {w}x{h}")
        # 不再自動縮放字體

    def start_led_blink(self):
        self.led_blinking = True
        self._blink_led()

    def _blink_led(self):
        if not self.led_blinking:
            return
        current_color = self.status_canvas.itemcget(self.status_light, 'fill')
        next_color = 'lime' if current_color == 'red' else 'red'
        self.status_canvas.itemconfig(self.status_light, fill=next_color)
        self.status_canvas.after(300, self._blink_led)

    def stop_led_blink(self):
        self.led_blinking = False
        # 恢復為黑色，表示待命狀態
        self.status_canvas.itemconfig(self.status_light, fill='black')

    def on_pane_drag_start(self, event):
        self.main_frame.start_x = event.x
        self.main_frame.start_y = event.y

    def on_pane_drag_end(self, event):
        dx = event.x - self.main_frame.start_x
        dy = event.y - self.main_frame.start_y
        self.main_frame.move(dx, dy)

    def on_pane_position_changed(self, event):
        """當 PanedWindow 分割位置改變時保存位置"""
        try:
            # 獲取當前分割位置
            sash_position = self.main_frame.sashpos(0)  # 第一個分割線的位置
            print(f"[DEBUG] PanedWindow 分割位置變更: {sash_position}")
            
            # 保存到設定中
            self.parent.setup['Pane_Sash_Position'] = str(sash_position)
            
            # 保存完整的設定結構
            from config import load_setup, save_setup
            full_setup = load_setup()
            full_setup['DUT_Control']['Pane_Sash_Position'] = str(sash_position)
            save_setup(full_setup)
            
        except Exception as e:
            print(f"[DEBUG] 保存分割位置時發生錯誤: {e}")

    def restore_pane_position(self):
        """恢復 PanedWindow 分割位置"""
        try:
            # 從設定中讀取分割位置
            sash_position = self.parent.setup.get('Pane_Sash_Position', '')
            if sash_position:
                position = int(sash_position)
                # 確保位置在合理範圍內
                window_width = self.parent.root.winfo_width()
                if 100 <= position <= window_width - 100:
                    self.main_frame.sashpos(0, position)
                    print(f"[DEBUG] 已恢復 PanedWindow 分割位置: {position}")
                else:
                    print(f"[DEBUG] 分割位置 {position} 超出範圍，使用預設位置")
            else:
                print(f"[DEBUG] 沒有保存的分割位置，使用預設位置")
        except Exception as e:
            print(f"[DEBUG] 恢復分割位置時發生錯誤: {e}")

    def limit_dropdown_height(self, event=None):
        """限制下拉列表的高度，最多顯示指定行數"""
        try:
            # 獲取下拉列表
            combo = self.combobox_cmd
            popup = combo.tk.call("ttk::combobox::PopdownWindow", combo)
            listbox = combo.tk.nametowidget(popup).winfo_children()[0]
            
            # 獲取項目總數和設置的最大顯示數
            total_items = len(combo['values'])
            max_items = min(total_items, self.max_dropdown_items)
            
            # 計算單個項目的高度（以像素為單位）
            item_height = 20  # 預設值，可能需要根據字體大小調整
            
            # 設置列表框的高度
            if max_items > 0:
                listbox.configure(height=max_items)
                print(f"[DEBUG] 限制下拉列表高度為 {max_items} 行")
            
        except Exception as e:
            print(f"[ERROR] 限制下拉列表高度時發生錯誤：{e}")
            import traceback
            traceback.print_exc()

    def on_auto_exec_changed(self):
        """當自動執行勾選框狀態變更時，保存設置"""
        try:
            # 獲取當前勾選狀態
            auto_exec = self.auto_exec_var.get()
            print(f"[DEBUG] 自動執行設置已變更為: {auto_exec}")
            
            # 更新設置
            self.parent.setup['Auto_Execute'] = auto_exec
            
            # 保存完整的設定結構
            from config import load_setup, save_setup
            full_setup = load_setup()
            full_setup['DUT_Control']['Auto_Execute'] = auto_exec
            save_setup(full_setup)
            
            print(f"[DEBUG] 自動執行設置已保存: {auto_exec}")
        except Exception as e:
            print(f"[ERROR] 保存自動執行設置時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def show_notification(self, message, color="red", duration=5000, callback=None):
        """
        在倒數計時標籤顯示通知消息
        
        參數:
            message: 要顯示的消息
            color: 文字顏色，默認為紅色
            duration: 顯示時間(毫秒)，默認5秒，0表示不自動清除
            callback: 通知結束後要調用的回調函數
        """
        # 保存當前顏色以便恢復
        original_fg = self.label_countdown.cget("fg")
        
        # 設置新消息和顏色
        self.label_countdown.config(text=message, fg=color)
        
        # 如果設置了持續時間，則在指定時間後清除消息
        if duration > 0:
            self.parent.root.after(duration, lambda: self._restore_after_notification(original_fg, callback))

    def _restore_after_notification(self, original_fg, callback=None):
        """通知結束後恢復"""
        self.label_countdown.config(text="", fg=original_fg)
        # 如果有回調函數，則執行
        if callback:
            callback()

    def on_cmd_selected(self):
        """當選擇指令時的回調函數"""
        cmd_key = self.combobox_cmd.get()
        if cmd_key:
            section = self.section_var.get()
            cmd = self.parent.commands_by_section.get(section, {}).get(cmd_key, "")
            if not cmd:
                cmd = self.parent.commands_by_section.get("全部指令", {}).get(cmd_key, "")
            
            # 顯示選擇的指令內容
            self.show_notification(f"已選擇: {cmd_key}", "blue", 3000)
            
            # 如果是特殊指令，顯示提示
            if cmd.startswith("DELAY:"):
                delay_time = cmd.split(":")[1]
                self.show_notification(f"延遲指令: {delay_time}秒", "purple", 3000)
            elif cmd.startswith("SHOW:"):
                message = cmd.split(":")[1]
                self.show_notification(f"顯示訊息: {message}", "green", 3000)

    def show_system_status(self):
        """顯示系統狀態信息"""
        try:
            # 獲取 COM 口
            com = self.combobox_com.get() or "未選擇"
            
            # 獲取當前選擇的分類
            section = self.section_var.get()
            
            # 獲取指令數量
            cmd_count = len(self.parent.commands_by_section.get(section, {}))
            
            # 獲取超時設定
            timeout = self.entry_timeout.get() or "30"
            
            # 顯示系統狀態
            status_msg = f"COM口: {com} | 分類: {section} ({cmd_count}個指令) | 超時: {timeout}秒"
            self.show_notification(status_msg, "blue", 5000)
        except Exception as e:
            print(f"[ERROR] 顯示系統狀態時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def change_notification_font_size(self, delta):
        """修改通知區域字體大小"""
        try:
            # 更新字體大小
            self.notification_font_size = max(10, min(20, self.notification_font_size + delta))
            
            # 更新標籤字體
            self.label_countdown.config(font=('Microsoft JhengHei UI', self.notification_font_size, 'bold'))
            
            # 保存設置
            self.parent.setup['Notification_Font_Size'] = str(self.notification_font_size)
            from config import save_setup
            full_setup = self.parent.setup
            if 'DUT_Control' not in full_setup:
                full_setup['DUT_Control'] = {}
            full_setup['DUT_Control']['Notification_Font_Size'] = str(self.notification_font_size)
            save_setup(full_setup)
            
            # 顯示通知
            self.show_notification(f"通知字體大小: {self.notification_font_size}", "blue", 2000)
        except Exception as e:
            print(f"[ERROR] 修改通知區域字體大小時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def copy_selected_text(self):
        # 實現複製選中文字的功能
        try:
            selected_text = self.text_output.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.parent.root.clipboard_clear()
                self.parent.root.clipboard_append(selected_text)
                self.show_notification("已複製選中文字", "green", 2000)
        except tk.TclError:
            # 如果沒有選中文字，會拋出 TclError
            self.show_notification("未選中任何文字", "orange", 2000)

    def select_all_text(self):
        # 實現全選文字的功能
        self.text_output.tag_add(tk.SEL, "1.0", tk.END)
        self.show_notification("已全選文字", "green", 2000)

    def show_output_context_menu(self, event):
        """顯示輸出區域的右鍵菜單"""
        try:
            self.output_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"[ERROR] 顯示右鍵菜單時發生錯誤: {e}")
            import traceback
            traceback.print_exc()