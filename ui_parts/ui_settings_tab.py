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

    def create_widgets(self):
        # Main frame with scrollbar
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 設置兩列佈局，讓左側列可以擴展以容納長路徑
        main_frame.columnconfigure(0, weight=2)  # 左側列權重更大
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)  # 讓預覽區域可以擴展
        
        # --- 儲存按鈕置頂 ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=0, columnspan=2, sticky="e", padx=5, pady=5)
        
        save_button = ttk.Button(button_frame, text="儲存設定", command=self.save_settings, 
                               style="Accent.TButton", width=15)
        save_button.pack(padx=5, pady=5)
        
        # 自定義按鈕樣式
        style = ttk.Style()
        style.configure("Accent.TButton", font=('Microsoft JhengHei UI', 12, 'bold'), 
                      background="#2196f3", foreground="white", padding=10)
        style.map("Accent.TButton",
                background=[("active", "#0d47a1"), ("!active", "#2196f3")],
                foreground=[("active", "white"), ("!active", "white")])

        # --- 基本設定區 ---
        basic_frame = ttk.LabelFrame(main_frame, text="基本設定", padding=(10, 5))
        basic_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 添加視窗標題設定 (優先使用頂層的 Window_Title)
        window_title = self.setup_data.get('Window_Title', self.setup_data.get('DUT_Control', {}).get('Window_Title', "VALO360 指令通"))
        self.vars["_Window_Title"] = tk.StringVar(value=window_title)
        
        ttk.Label(basic_frame, text="視窗標題", width=15).grid(row=0, column=0, sticky="w", pady=2)
        entry = ttk.Entry(basic_frame, textvariable=self.vars["_Window_Title"], width=25)
        entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(basic_frame, text="(不包含版本號)").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5))

        # --- 標籤頁名稱設定區 ---
        tab_frame = ttk.LabelFrame(main_frame, text="標籤頁名稱設定", padding=(10, 5))
        tab_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5, rowspan=1)
        tab_frame.grid_remove()  # 先隱藏，後面再插入到正確位置
        
        # 獲取當前的標籤頁名稱
        tab_names = self.setup_data.get('tab_names', {})
        default_tab_names = ['DUT 控制', '治具控制', '使用說明', '設定']
        
        # 創建標籤頁名稱輸入框
        for i in range(4):
            tab_key = f'tab{i}'
            tab_name = tab_names.get(tab_key, default_tab_names[i])
            ttk.Label(tab_frame, text=f"標籤頁 {i+1}", width=15).grid(row=i, column=0, sticky="w", pady=2)
            self.vars[f"tab_names_{tab_key}"] = tk.StringVar(value=tab_name)
            entry = ttk.Entry(tab_frame, textvariable=self.vars[f"tab_names_{tab_key}"], width=25)
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=2)
        
        # 將標籤頁設定插入到基本設定之後
        basic_frame.grid_remove()
        basic_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        tab_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # --- 左側：DUT 控制區 ---
        dut_frame = ttk.LabelFrame(main_frame, text="DUT 控制區", padding=(10, 5))
        dut_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)  # 行號變為2
        
        # 設定DUT框架的列配置，讓輸入框列可以擴展
        dut_frame.columnconfigure(1, weight=1)

        # 設定項目列表 (key, 顯示文字, 輸入框寬度)
        dut_settings = [
            ("Serial_COM_Port", "序列通訊埠", 10),
            ("Default_IP_Address", "預設 IP 位址", 15),
            ("Command_Timeout_Seconds", "指令超時 (秒)", 5),
            ("Command_End_String", "指令結束字串", 10),
            ("UI_Font_Size", "介面字體大小", 5),
            ("Content_Font_Size", "內容字體大小", 5),
        ]
        
        # 使用統一的標籤寬度
        for i, (key, text, width) in enumerate(dut_settings):
            ttk.Label(dut_frame, text=text, width=15).grid(row=i, column=0, sticky="w", pady=2)
            self.vars[f"DUT_Control_{key}"] = tk.StringVar()
            entry = ttk.Entry(dut_frame, textvariable=self.vars[f"DUT_Control_{key}"], width=width)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=2)

        # 自動執行勾選框
        self.vars["DUT_Control_Auto_Execute"] = tk.BooleanVar()
        cb = ttk.Checkbutton(dut_frame, text="啟動時自動執行指令", variable=self.vars["DUT_Control_Auto_Execute"])
        cb.grid(row=len(dut_settings), column=0, columnspan=2, sticky="w", pady=2)
        
        # 指令檔路徑選擇器
        ttk.Label(dut_frame, text="指令檔路徑", width=15).grid(row=len(dut_settings)+1, column=0, sticky="w", pady=2)
        file_frame = ttk.Frame(dut_frame)
        file_frame.grid(row=len(dut_settings)+1, column=1, sticky="ew", padx=5, pady=2)  # 使用ew而不是w，讓框架可以水平擴展
        
        # 設定file_frame的列配置，讓輸入框可以擴展
        file_frame.columnconfigure(0, weight=1)

        self.vars["DUT_Control_Command_File_Path"] = tk.StringVar()
        entry = ttk.Entry(file_frame, textvariable=self.vars["DUT_Control_Command_File_Path"], width=60)
        entry.grid(row=0, column=0, sticky="ew")  # 使用ew而不是w，讓輸入框可以水平擴展
        
        button = ttk.Button(file_frame, text="選擇", command=lambda: self.select_command_file("DUT_Control_Command_File_Path"), width=5)
        button.grid(row=0, column=1, padx=5)

        # --- 右側：治具控制區 ---
        fixture_frame = ttk.LabelFrame(main_frame, text="治具控制區", padding=(10, 5))
        fixture_frame.grid(row=2, column=1, sticky="nw", padx=5, pady=5)

        # 治具設定項目
        ttk.Label(fixture_frame, text="治具通訊埠", width=15).grid(row=0, column=0, sticky="w", pady=2)
        self.vars["Fixture_Control_Fixture_COM_Port"] = tk.StringVar()
        entry = ttk.Entry(fixture_frame, textvariable=self.vars["Fixture_Control_Fixture_COM_Port"], width=10)
        entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(fixture_frame, text="治具字體大小", width=15).grid(row=1, column=0, sticky="w", pady=2)
        self.vars["Fixture_Control_Fixture_Font_Size"] = tk.StringVar()
        entry = ttk.Entry(fixture_frame, textvariable=self.vars["Fixture_Control_Fixture_Font_Size"], width=5)
        entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # 測試類別勾選框
        self.vars["Fixture_Control_Test_Category_FUNCTION"] = tk.BooleanVar()
        cb1 = ttk.Checkbutton(fixture_frame, text="FUNCTION", variable=self.vars["Fixture_Control_Test_Category_FUNCTION"])
        cb1.grid(row=2, column=0, columnspan=2, sticky="w", pady=2)
        
        self.vars["Fixture_Control_Test_Category_MB"] = tk.BooleanVar()
        cb2 = ttk.Checkbutton(fixture_frame, text="MB", variable=self.vars["Fixture_Control_Test_Category_MB"])
        cb2.grid(row=3, column=0, columnspan=2, sticky="w", pady=2)
        
        self.vars["Fixture_Control_Test_Category_Original_Commands"] = tk.BooleanVar()
        cb3 = ttk.Checkbutton(fixture_frame, text="原始指令", variable=self.vars["Fixture_Control_Test_Category_Original_Commands"])
        cb3.grid(row=4, column=0, columnspan=2, sticky="w", pady=2)

        # --- 新增：介面佈局設定區 ---
        layout_frame = ttk.LabelFrame(main_frame, text="介面佈局設定", padding=(10, 5))
        layout_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 分割位置設定
        ttk.Label(layout_frame, text="左右分割位置", width=15).grid(row=0, column=0, sticky="w", pady=2)
        self.vars["DUT_Control_Pane_Sash_Position"] = tk.StringVar()
        entry = ttk.Entry(layout_frame, textvariable=self.vars["DUT_Control_Pane_Sash_Position"], width=5)
        entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(layout_frame, text="(數值越大，左側越寬)", font=('Microsoft JhengHei UI', 8)).grid(row=0, column=2, sticky="w")
        
        # 視窗大小設定
        ttk.Label(layout_frame, text="視窗寬度", width=15).grid(row=1, column=0, sticky="w", pady=2)
        self.vars["DUT_Control_Window_Width"] = tk.StringVar()
        entry = ttk.Entry(layout_frame, textvariable=self.vars["DUT_Control_Window_Width"], width=5)
        entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(layout_frame, text="視窗高度", width=15).grid(row=2, column=0, sticky="w", pady=2)
        self.vars["DUT_Control_Window_Height"] = tk.StringVar()
        entry = ttk.Entry(layout_frame, textvariable=self.vars["DUT_Control_Window_Height"], width=5)
        entry.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # 通知區域字體大小
        ttk.Label(layout_frame, text="通知字體大小", width=15).grid(row=3, column=0, sticky="w", pady=2)
        self.vars["DUT_Control_Notification_Font_Size"] = tk.StringVar()
        entry = ttk.Entry(layout_frame, textvariable=self.vars["DUT_Control_Notification_Font_Size"], width=5)
        entry.grid(row=3, column=1, sticky="w", padx=5, pady=2)

        # --- 區段標題預覽區域 (放在底部) ---
        preview_frame = ttk.LabelFrame(main_frame, text="區段標題預覽", padding=(10, 5))
        preview_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 使用簡單的水平佈局，減少嵌套層級
        preview_container = ttk.Frame(preview_frame)
        preview_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 創建左側容器，用於放置列表框和滾動條
        list_container = ttk.Frame(preview_container)
        list_container.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 10))
        
        # 左側預覽列表 - 佔40%寬度
        self.preview_listbox = tk.Listbox(list_container, height=4)
        self.preview_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        
        # 為預覽列表添加滾動條 - 正確放置在與Listbox同級的容器中
        preview_scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.preview_listbox.yview)
        preview_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.preview_listbox.configure(yscrollcommand=preview_scrollbar.set)
        
        # 右側說明文字 - 佔60%寬度，使用基本的tk.Label確保文字顯示
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

        # --- Save Button (移除，因為已經移到頂部) ---
        # button_frame = ttk.Frame(main_frame)
        # button_frame.grid(row=5, column=0, columnspan=2, sticky="e", padx=5, pady=5)
        
        # save_button = ttk.Button(button_frame, text="儲存設定", command=self.save_settings)
        # save_button.pack(padx=5, pady=5)

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