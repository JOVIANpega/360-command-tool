import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from config_core import load_setup, save_setup
import json

class SettingsTab(ttk.Frame):
    def __init__(self, parent, on_save_callback=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.pack(fill="both", expand=True)
        self.on_save_callback = on_save_callback

        self.setup_data = load_setup()
        self.vars = {}
        self.sections_preview = []  # 存儲從指令檔案中讀取的區段標題

        self.create_widgets()
        self.load_settings()
        
        # 绑定窗口大小变化事件
        self.bind("<Configure>", self._on_frame_configure)
        
    def _on_frame_configure(self, event=None):
        """当窗口大小改变时，更新Canvas的滚动区域"""
        # 更新Canvas的滚动区域以匹配内容框架的大小
        if hasattr(self, 'canvas'):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            # 设置Canvas宽度以适应容器宽度
            self.canvas.config(width=self.winfo_width()-20)  # 减去滚动条宽度

    def create_widgets(self):
        # 创建带滚动条的主框架
        # 外层容器框架
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        
        # 创建Canvas和滚动条
        self.canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        # 配置Canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # 放置Canvas和滚动条
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 创建内容框架，将所有内容放在这个框架内
        main_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        # 绑定鼠标滚轮事件
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # 设置两列布局，让左侧列可以扩展以容纳长路径
        main_frame.columnconfigure(0, weight=2)  # 左侧列权重更大
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)  # 让预览区域可以扩展
        
        # --- 储存按钮置顶 ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=0, columnspan=2, sticky="e", padx=5, pady=5)
        
        # 添加设置选项卡字体大小控制
        settings_font_frame = ttk.Frame(button_frame)
        settings_font_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(settings_font_frame, text="設定頁字體大小:").pack(side=tk.LEFT, padx=(0, 5))
        
        # 设置选项卡字体大小默认值为11
        self.settings_font_size = tk.StringVar(value="11")
        
        # 减小按钮
        minus_btn = ttk.Button(settings_font_frame, text="-", width=2, 
                              command=lambda: self.adjust_settings_font_size(-1))
        minus_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # 输入框
        entry = ttk.Entry(settings_font_frame, textvariable=self.settings_font_size, width=3)
        entry.pack(side=tk.LEFT)
        
        # 增大按钮
        plus_btn = ttk.Button(settings_font_frame, text="+", width=2, 
                             command=lambda: self.adjust_settings_font_size(1))
        plus_btn.pack(side=tk.LEFT, padx=(2, 0))
        
        save_button = ttk.Button(button_frame, text="儲存設定", command=self.save_settings, 
                               style="Accent.TButton", width=15)
        save_button.pack(padx=5, pady=5)
        
        # 自定义按钮样式
        style = ttk.Style()
        style.configure("Accent.TButton", font=('Microsoft JhengHei UI', 12, 'bold'), 
                      background="#2196f3", foreground="white", padding=10)
        style.map("Accent.TButton",
                background=[("active", "#0d47a1"), ("!active", "#2196f3")],
                foreground=[("active", "white"), ("!active", "white")])

        # --- 基本设定区 ---
        basic_frame = ttk.LabelFrame(main_frame, text="基本設定", padding=(10, 5))
        basic_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 添加视窗标题设定 (优先使用顶层的 Window_Title)
        window_title = self.setup_data.get('Window_Title', self.setup_data.get('DUT_Control', {}).get('Window_Title', "VALO360 指令通"))
        self.vars["_Window_Title"] = tk.StringVar(value=window_title)
        
        ttk.Label(basic_frame, text="視窗標題", width=15).grid(row=0, column=0, sticky="w", pady=2)
        entry = ttk.Entry(basic_frame, textvariable=self.vars["_Window_Title"], width=25)
        entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(basic_frame, text="(不包含版本號)").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5))

        # --- 标签页名称设定区 ---
        tab_frame = ttk.LabelFrame(main_frame, text="標籤頁名稱設定", padding=(10, 5))
        tab_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5, rowspan=1)
        tab_frame.grid_remove()  # 先隐藏，后面再插入到正确位置
        
        # 获取当前的标签页名称
        tab_names = self.setup_data.get('tab_names', {})
        default_tab_names = ['DUT 控制', '治具控制', '使用說明', '設定']
        
        # 创建标签页名称输入框
        for i in range(4):
            tab_key = f'tab{i}'
            tab_name = tab_names.get(tab_key, default_tab_names[i])
            ttk.Label(tab_frame, text=f"標籤頁 {i+1}", width=15).grid(row=i, column=0, sticky="w", pady=2)
            self.vars[f"tab_names_{tab_key}"] = tk.StringVar(value=tab_name)
            entry = ttk.Entry(tab_frame, textvariable=self.vars[f"tab_names_{tab_key}"], width=25)
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=2)
        
        # 将标签页设定插入到基本设定之后
        basic_frame.grid_remove()
        basic_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        tab_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # --- 左侧：DUT 控制区 ---
        dut_frame = ttk.LabelFrame(main_frame, text="DUT 控制區", padding=(10, 5))
        dut_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)  # 行号变为2
        
        # 设定DUT框架的列配置，让输入框列可以扩展
        dut_frame.columnconfigure(1, weight=1)

        # 设定项目列表 (key, 显示文字, 输入框宽度)
        dut_settings = [
            ("Serial_COM_Port", "序列通訊埠", 10),
            ("Default_IP_Address", "預設 IP 位址", 15),
            ("Command_Timeout_Seconds", "指令超時 (秒)", 5),
            ("Command_End_String", "指令結束字串", 10),
            ("UI_Font_Size", "介面字體大小", 5),
            ("Content_Font_Size", "內容字體大小", 5),
        ]
        
        # 使用统一的标签宽度
        for i, (key, text, width) in enumerate(dut_settings):
            ttk.Label(dut_frame, text=text, width=15).grid(row=i, column=0, sticky="w", pady=2)
            # 对于字体大小相关的设置，设置默认值为11
            if key in ["UI_Font_Size", "Content_Font_Size"]:
                self.vars[f"DUT_Control_{key}"] = tk.StringVar(value="11")
                # 创建一个包含输入框和加减按钮的容器
                font_frame = ttk.Frame(dut_frame)
                font_frame.grid(row=i, column=1, sticky="w", padx=5, pady=2)
                
                # 减小按钮
                minus_btn = ttk.Button(font_frame, text="-", width=2, 
                                      command=lambda k=key: self.adjust_font_size(f"DUT_Control_{k}", -1))
                minus_btn.pack(side=tk.LEFT, padx=(0, 2))
                
                # 输入框
                entry = ttk.Entry(font_frame, textvariable=self.vars[f"DUT_Control_{key}"], width=3)
                entry.pack(side=tk.LEFT)
                
                # 增大按钮
                plus_btn = ttk.Button(font_frame, text="+", width=2, 
                                     command=lambda k=key: self.adjust_font_size(f"DUT_Control_{k}", 1))
                plus_btn.pack(side=tk.LEFT, padx=(2, 0))
            else:
                self.vars[f"DUT_Control_{key}"] = tk.StringVar()
                entry = ttk.Entry(dut_frame, textvariable=self.vars[f"DUT_Control_{key}"], width=width)
                entry.grid(row=i, column=1, sticky="w", padx=5, pady=2)

        # 自动执行勾选框
        self.vars["DUT_Control_Auto_Execute"] = tk.BooleanVar()
        cb = ttk.Checkbutton(dut_frame, text="啟動時自動執行指令", variable=self.vars["DUT_Control_Auto_Execute"])
        cb.grid(row=len(dut_settings), column=0, columnspan=2, sticky="w", pady=2)
        
        # 指令档路径选择器
        ttk.Label(dut_frame, text="指令檔路徑", width=15).grid(row=len(dut_settings)+1, column=0, sticky="w", pady=2)
        file_frame = ttk.Frame(dut_frame)
        file_frame.grid(row=len(dut_settings)+1, column=1, sticky="ew", padx=5, pady=2)  # 使用ew而不是w，让框架可以水平扩展
        
        # 设定file_frame的列配置，让输入框可以扩展
        file_frame.columnconfigure(0, weight=1)

        self.vars["DUT_Control_Command_File_Path"] = tk.StringVar()
        entry = ttk.Entry(file_frame, textvariable=self.vars["DUT_Control_Command_File_Path"], width=60)
        entry.grid(row=0, column=0, sticky="ew")  # 使用ew而不是w，让输入框可以水平扩展
        
        button = ttk.Button(file_frame, text="選擇", command=lambda: self.select_command_file("DUT_Control_Command_File_Path"), width=5)
        button.grid(row=0, column=1, padx=5)
        
        # --- 界面布局设定（作为DUT控制区的一部分） ---
        layout_separator = ttk.Separator(dut_frame, orient="horizontal")
        layout_separator.grid(row=len(dut_settings)+2, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Label(dut_frame, text="介面佈局設定", font=('Microsoft JhengHei UI', 10, 'bold')).grid(row=len(dut_settings)+3, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        # 分割位置设定
        ttk.Label(dut_frame, text="左右分割位置", width=15).grid(row=len(dut_settings)+4, column=0, sticky="w", pady=2)
        self.vars["DUT_Control_Pane_Sash_Position"] = tk.StringVar()
        entry = ttk.Entry(dut_frame, textvariable=self.vars["DUT_Control_Pane_Sash_Position"], width=5)
        entry.grid(row=len(dut_settings)+4, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(dut_frame, text="(數值越大，左側越寬)", font=('Microsoft JhengHei UI', 8)).grid(row=len(dut_settings)+4, column=1, sticky="w", padx=(50, 0))
        
        # 视窗大小设定
        ttk.Label(dut_frame, text="視窗寬度", width=15).grid(row=len(dut_settings)+5, column=0, sticky="w", pady=2)
        self.vars["DUT_Control_Window_Width"] = tk.StringVar()
        entry = ttk.Entry(dut_frame, textvariable=self.vars["DUT_Control_Window_Width"], width=5)
        entry.grid(row=len(dut_settings)+5, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(dut_frame, text="視窗高度", width=15).grid(row=len(dut_settings)+6, column=0, sticky="w", pady=2)
        self.vars["DUT_Control_Window_Height"] = tk.StringVar()
        entry = ttk.Entry(dut_frame, textvariable=self.vars["DUT_Control_Window_Height"], width=5)
        entry.grid(row=len(dut_settings)+6, column=1, sticky="w", padx=5, pady=2)
        
        # 通知区域字体大小
        ttk.Label(dut_frame, text="通知字體大小", width=15).grid(row=len(dut_settings)+7, column=0, sticky="w", pady=2)
        # 设置通知字体大小默认值为11
        self.vars["DUT_Control_Notification_Font_Size"] = tk.StringVar(value="11")
        
        # 创建一个包含输入框和加减按钮的容器
        notification_font_frame = ttk.Frame(dut_frame)
        notification_font_frame.grid(row=len(dut_settings)+7, column=1, sticky="w", padx=5, pady=2)
        
        # 减小按钮
        minus_btn = ttk.Button(notification_font_frame, text="-", width=2, 
                              command=lambda: self.adjust_font_size("DUT_Control_Notification_Font_Size", -1))
        minus_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # 输入框
        entry = ttk.Entry(notification_font_frame, textvariable=self.vars["DUT_Control_Notification_Font_Size"], width=3)
        entry.pack(side=tk.LEFT)
        
        # 增大按钮
        plus_btn = ttk.Button(notification_font_frame, text="+", width=2, 
                             command=lambda: self.adjust_font_size("DUT_Control_Notification_Font_Size", 1))
        plus_btn.pack(side=tk.LEFT, padx=(2, 0))

        # --- 右侧：治具控制区 ---
        fixture_frame = ttk.LabelFrame(main_frame, text="治具控制區", padding=(10, 5))
        fixture_frame.grid(row=2, column=1, sticky="nw", padx=5, pady=5)

        # 治具设定项目
        ttk.Label(fixture_frame, text="治具通訊埠", width=15).grid(row=0, column=0, sticky="w", pady=2)
        self.vars["Fixture_Control_Fixture_COM_Port"] = tk.StringVar()
        entry = ttk.Entry(fixture_frame, textvariable=self.vars["Fixture_Control_Fixture_COM_Port"], width=10)
        entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(fixture_frame, text="治具字體大小", width=15).grid(row=1, column=0, sticky="w", pady=2)
        # 设置治具字体大小默认值为11
        self.vars["Fixture_Control_Fixture_Font_Size"] = tk.StringVar(value="11")
        
        # 创建一个包含输入框和加减按钮的容器
        fixture_font_frame = ttk.Frame(fixture_frame)
        fixture_font_frame.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # 减小按钮
        minus_btn = ttk.Button(fixture_font_frame, text="-", width=2, 
                              command=lambda: self.adjust_font_size("Fixture_Control_Fixture_Font_Size", -1))
        minus_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # 输入框
        entry = ttk.Entry(fixture_font_frame, textvariable=self.vars["Fixture_Control_Fixture_Font_Size"], width=3)
        entry.pack(side=tk.LEFT)
        
        # 增大按钮
        plus_btn = ttk.Button(fixture_font_frame, text="+", width=2, 
                             command=lambda: self.adjust_font_size("Fixture_Control_Fixture_Font_Size", 1))
        plus_btn.pack(side=tk.LEFT, padx=(2, 0))
        
        # 测试类别勾选框
        self.vars["Fixture_Control_Test_Category_FUNCTION"] = tk.BooleanVar()
        cb1 = ttk.Checkbutton(fixture_frame, text="FUNCTION", variable=self.vars["Fixture_Control_Test_Category_FUNCTION"])
        cb1.grid(row=2, column=0, columnspan=2, sticky="w", pady=2)
        
        self.vars["Fixture_Control_Test_Category_MB"] = tk.BooleanVar()
        cb2 = ttk.Checkbutton(fixture_frame, text="MB", variable=self.vars["Fixture_Control_Test_Category_MB"])
        cb2.grid(row=3, column=0, columnspan=2, sticky="w", pady=2)
        
        self.vars["Fixture_Control_Test_Category_Original_Commands"] = tk.BooleanVar()
        cb3 = ttk.Checkbutton(fixture_frame, text="原始指令", variable=self.vars["Fixture_Control_Test_Category_Original_Commands"])
        cb3.grid(row=4, column=0, columnspan=2, sticky="w", pady=2)

        # --- 区段标题预览区域 (放在底部) ---
        preview_frame = ttk.LabelFrame(main_frame, text="區段標題預覽", padding=(10, 5))
        preview_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 使用简单的水平布局，减少嵌套级别
        preview_container = ttk.Frame(preview_frame)
        preview_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建左侧容器，用于放置列表框和滚动条
        list_container = ttk.Frame(preview_container)
        list_container.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 10))
        
        # 左侧预览列表 - 占40%宽度
        self.preview_listbox = tk.Listbox(list_container, height=4)
        self.preview_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        
        # 为预览列表添加滚动条 - 正确放置在与Listbox同级的容器中
        preview_scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.preview_listbox.yview)
        preview_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.preview_listbox.configure(yscrollcommand=preview_scrollbar.set)
        
        # 右侧说明文字 - 占60%宽度，使用基本的tk.Label确保文字显示
        preview_text = "選擇指令檔案後，這裡會顯示檔案中的區段標題。\n儲存設定後，這些標題將成為DUT控制頁面的按鈕。"
        preview_label = tk.Label(
            preview_container, 
            text=preview_text,
            wraplength=250,
            bg="#f0f0f0",  # 背景色
            font=('Microsoft JhengHei UI', 10),
            anchor="w",
            justify="left"
        )
        preview_label.pack(side=tk.RIGHT, fill="both", expand=True)

    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        # Windows系统下的鼠标滚轮事件处理
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")

    def create_entry(self, parent, key, text, section, row, width=None):
        # 這個方法已不再使用，因為我們在 create_widgets 中直接創建了所有控件
        pass

    def create_checkbox(self, parent, key, text, section, row):
        # 這個方法已不再使用，因為我們在 create_widgets 中直接創建了所有控件
        pass
        
    def create_file_picker(self, parent, key, text, section, row, width=None):
        # 這個方法已不再使用，因為我們在 create_widgets 中直接創建了所有控件
        pass

    def select_command_file(self, var_key):
        filepath = filedialog.askopenfilename(
            title="選擇指令檔",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if filepath:
            self.vars[var_key].set(filepath)
            # 選擇檔案後立即讀取區段標題並更新預覽
            self.read_section_titles(filepath)

    def read_section_titles(self, filepath):
        """讀取指令檔案中的區段標題"""
        self.sections_preview = []
        try:
            print(f"[DEBUG] SettingsTab: 開始從檔案讀取區段標題: {filepath}")
            with open(filepath, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if line.startswith("==") and line.endswith("=="):
                        section_name = line.strip("=").strip()
                        if section_name and section_name not in self.sections_preview:
                            self.sections_preview.append(section_name)
            
            # 更新預覽列表
            self.update_preview_listbox()
            
            # 將讀取到的區段標題存儲到設置中，以便保存時使用
            if not 'DUT_Control' in self.setup_data:
                self.setup_data['DUT_Control'] = {}
            self.setup_data['DUT_Control']['Section_Titles'] = self.sections_preview
            
            print(f"[DEBUG] SettingsTab: 從指令檔案中讀取到 {len(self.sections_preview)} 個區段標題: {self.sections_preview}")
        except Exception as e:
            messagebox.showerror("錯誤", f"讀取指令檔案失敗：{e}")
            print(f"[ERROR] SettingsTab: 讀取指令檔案失敗：{e}")
            import traceback
            traceback.print_exc()

    def update_preview_listbox(self):
        """更新預覽列表框"""
        self.preview_listbox.delete(0, tk.END)
        
        if self.sections_preview:
            print(f"[DEBUG] SettingsTab: 更新預覽列表，顯示 {len(self.sections_preview)} 個區段標題")
            for section in self.sections_preview:
                self.preview_listbox.insert(tk.END, section)
        else:
            print("[DEBUG] SettingsTab: 未找到區段標題，顯示預設訊息")
            self.preview_listbox.insert(tk.END, "未找到區段標題")

    def load_settings(self):
        """從設定中載入值到 UI 控件"""
        try:
            # 重新載入設定
            self.setup_data = load_setup()
            dut_control = self.setup_data.get('DUT_Control', {})
            fixture_control = self.setup_data.get('Fixture_Control', {})
            
            print(f"[DEBUG] SettingsTab.load_settings: 載入設定 - {json.dumps(self.setup_data, ensure_ascii=False)[:200]}...")
            
            # 载入设置选项卡字体大小
            settings_font_size = self.setup_data.get('Settings_Font_Size', '11')
            self.settings_font_size.set(settings_font_size)
            
            # 載入基本設定 - 優先使用頂層的 Window_Title
            self.vars["_Window_Title"].set(self.setup_data.get('Window_Title', dut_control.get('Window_Title', '')))
            
            # 載入標籤頁名稱
            tab_names = self.setup_data.get('tab_names', {})
            for i in range(4):
                tab_key = f'tab{i}'
                if f"tab_names_{tab_key}" in self.vars:
                    self.vars[f"tab_names_{tab_key}"].set(tab_names.get(tab_key, f"標籤頁 {i+1}"))
            
            # 載入 DUT 控制設定 - 確保所有字段都被處理
            dut_fields = [
                "Serial_COM_Port", "Default_IP_Address", "Command_Timeout_Seconds", 
                "Command_End_String", "UI_Font_Size", "Content_Font_Size", "Command_File_Path",
                "Notification_Font_Size", "Pane_Sash_Position", "Window_Width", "Window_Height"
            ]
            
            for key in dut_fields:
                var_key = f"DUT_Control_{key}"
                if var_key in self.vars:
                    value = dut_control.get(key, '')
                    self.vars[var_key].set(value)
                    print(f"[DEBUG] SettingsTab.load_settings: 設置 {var_key} = {value}")
            
            # 載入自動執行設定
            auto_execute = dut_control.get('Auto_Execute', False)
            self.vars["DUT_Control_Auto_Execute"].set(auto_execute)
            print(f"[DEBUG] SettingsTab.load_settings: 設置 Auto_Execute = {auto_execute}")
            
            # 載入治具控制設定
            fixture_fields = {
                "Fixture_COM_Port": "Fixture_Control_Fixture_COM_Port",
                "Fixture_Font_Size": "Fixture_Control_Fixture_Font_Size",
                "Test_Category_FUNCTION": "Fixture_Control_Test_Category_FUNCTION",
                "Test_Category_MB": "Fixture_Control_Test_Category_MB",
                "Test_Category_Original_Commands": "Fixture_Control_Test_Category_Original_Commands"
            }
            
            for field, var_key in fixture_fields.items():
                if var_key in self.vars:
                    if field.startswith("Test_Category"):
                        # 布尔值处理
                        value = fixture_control.get(field, False)
                    else:
                        # 字符串处理
                        value = fixture_control.get(field, '')
                    self.vars[var_key].set(value)
                    print(f"[DEBUG] SettingsTab.load_settings: 設置 {var_key} = {value}")
            
            # 如果有指令檔案路徑，嘗試讀取區段標題
            cmd_file_path = dut_control.get('Command_File_Path', '')
            if cmd_file_path and os.path.exists(cmd_file_path):
                try:
                    self.read_section_titles(cmd_file_path)
                except Exception as e:
                    print(f"[ERROR] SettingsTab.load_settings: 讀取區段標題失敗: {e}")
                    # 從設定中讀取區段標題作為備用
                    self.sections_preview = dut_control.get('Section_Titles', [])
                    self.update_preview_listbox()
            else:
                # 如果沒有檔案路徑或檔案不存在，則從設定中讀取區段標題
                self.sections_preview = dut_control.get('Section_Titles', [])
                self.update_preview_listbox()
            
        except Exception as e:
            print(f"[ERROR] SettingsTab: 載入設定失敗：{e}")
            import traceback
            traceback.print_exc()
            # 不要彈出錯誤對話框，這可能會導致更多問題
            # messagebox.showerror("錯誤", f"載入設定失敗：{e}")
            # 使用空的設定數據
            self.setup_data = {}

    def save_settings(self):
        try:
            # 從UI取得設定值
            settings = self.setup_data.copy()
            
            # 保存设置选项卡字体大小
            settings['Settings_Font_Size'] = self.settings_font_size.get()
            
            # 儲存視窗標題到頂層
            settings['Window_Title'] = self.vars["_Window_Title"].get()
            
            # 儲存標籤頁名稱
            tab_names = {}
            for i in range(4):
                tab_key = f'tab{i}'
                if f"tab_names_{tab_key}" in self.vars:
                    tab_names[tab_key] = self.vars[f"tab_names_{tab_key}"].get()
            settings['tab_names'] = tab_names
            
            # 更新 DUT_Control 設定
            if 'DUT_Control' not in settings:
                settings['DUT_Control'] = {}
            
            # 複製 DUT_Control 設定
            for key in self.vars:
                if key.startswith("DUT_Control_"):
                    setting_key = key.replace("DUT_Control_", "")
                    
                    # 根據控件類型取值
                    var = self.vars[key]
                    if isinstance(var, tk.BooleanVar):
                        value = var.get()
                    else:
                        value = var.get()
                        
                    settings['DUT_Control'][setting_key] = value
                    
            # 確保 Window_Title 同時更新到 DUT_Control
            settings['DUT_Control']['Window_Title'] = settings['Window_Title']
            
            # 更新 Fixture_Control 設定
            if 'Fixture_Control' not in settings:
                settings['Fixture_Control'] = {}
                
            # 複製 Fixture_Control 設定
            for key in self.vars:
                if key.startswith("Fixture_Control_"):
                    setting_key = key.replace("Fixture_Control_", "")
                    
                    # 根據控件類型取值
                    var = self.vars[key]
                    if isinstance(var, tk.BooleanVar):
                        value = var.get()
                    else:
                        value = var.get()
                        
                    settings['Fixture_Control'][setting_key] = value
            
            # 儲存視窗大小到頂層
            settings['Window_Width'] = settings['DUT_Control']['Window_Width']
            settings['Window_Height'] = settings['DUT_Control']['Window_Height']
            settings['UIFontSize'] = settings['DUT_Control']['UI_Font_Size']
            settings['ContentFontSize'] = settings['DUT_Control']['Content_Font_Size']
            
            # 如果有Section_Titles，確保它們被保留
            if 'Section_Titles' in settings['DUT_Control']:
                pass  # 保留現有的 Section_Titles
            elif self.sections_preview:
                settings['DUT_Control']['Section_Titles'] = self.sections_preview
            
            # 儲存到檔案
            save_setup(settings)
            
            # 顯示成功消息
            messagebox.showinfo("成功", "設定已儲存！標籤頁名稱已更新。")
            
            # 更新此設定檔實例中的數據，確保下次讀取時是最新的
            self.setup_data = settings.copy()
            
            # 執行回調函數 - 通知所有需要更新的UI元素
            if self.on_save_callback:
                self.on_save_callback()
                
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存設定時發生錯誤：{e}")
            import traceback
            traceback.print_exc()

    def activate(self):
        """當分頁被選中時調用"""
        # 重新載入設定
        self.load_settings() 
        
        # 更新Canvas的滚动区域
        if hasattr(self, 'canvas'):
            self.canvas.update_idletasks()  # 确保所有控件都已正确布局
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            # 滚动到顶部
            self.canvas.yview_moveto(0)
            
        # 应用设置选项卡字体大小
        self.apply_settings_font_size()
        
    def apply_settings_font_size(self):
        """应用设置选项卡字体大小到所有控件"""
        try:
            font_size = int(self.settings_font_size.get())
            font = ('Microsoft JhengHei UI', font_size)
            
            # 获取所有标签和输入框
            widgets = self.get_all_widgets(self)
            
            # 更新所有控件的字体
            for widget in widgets:
                if isinstance(widget, (ttk.Label, ttk.Button, ttk.Checkbutton, tk.Label, tk.Button, tk.Checkbutton)):
                    try:
                        widget.configure(font=font)
                    except Exception as e:
                        print(f"[DEBUG] 更新控件字体失败: {e}")
                elif isinstance(widget, (ttk.Entry, ttk.Combobox, tk.Entry, tk.Listbox)):
                    try:
                        widget.configure(font=('Consolas', font_size))
                    except Exception as e:
                        print(f"[DEBUG] 更新输入控件字体失败: {e}")
            
            # 更新标题字体
            style = ttk.Style()
            style.configure("TLabelframe.Label", font=('Microsoft JhengHei UI', font_size, 'bold'))
            
            print(f"[DEBUG] 已应用设置选项卡字体大小: {font_size}")
        except Exception as e:
            print(f"[ERROR] 应用设置选项卡字体大小时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def get_all_widgets(self, parent):
        """递归获取所有子控件"""
        widgets = []
        for widget in parent.winfo_children():
            widgets.append(widget)
            if widget.winfo_children():
                widgets.extend(self.get_all_widgets(widget))
        return widgets

    def adjust_font_size(self, var_key, delta):
        """調整字體大小"""
        current_value = self.vars[var_key].get()
        try:
            new_value = int(current_value) + delta
            if new_value < 8: # 最小字體大小
                new_value = 8
            elif new_value > 20: # 最大字體大小
                new_value = 20
            self.vars[var_key].set(str(new_value))
            print(f"[DEBUG] SettingsTab: 調整字體大小 {var_key} 從 {current_value} 到 {new_value}")
        except ValueError:
            print(f"[DEBUG] SettingsTab: {var_key} 不是有效的數字，無法調整字體大小。") 

    def adjust_settings_font_size(self, delta):
        """調整設定頁字體大小"""
        current_value = self.settings_font_size.get()
        try:
            new_value = int(current_value) + delta
            if new_value < 8: # 最小字體大小
                new_value = 8
            elif new_value > 20: # 最大字體大小
                new_value = 20
            self.settings_font_size.set(str(new_value))
            print(f"[DEBUG] SettingsTab: 調整設定頁字體大小 從 {current_value} 到 {new_value}")
            
            # 立即应用字体大小更改
            self.apply_settings_font_size()
        except ValueError:
            print(f"[DEBUG] SettingsTab: 設定頁字體大小 不是有效的數字，無法調整。") 