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

        canvas = tk.Canvas(main_frame, bg='white')
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Main.TFrame')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- 基本設定區 ---
        basic_frame = ttk.LabelFrame(scrollable_frame, text="基本設定", padding=(10, 5))
        basic_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        basic_frame.columnconfigure(1, weight=1)

        # 添加視窗標題設定 (優先使用頂層的 Window_Title)
        window_title = self.setup_data.get('Window_Title', self.setup_data.get('DUT_Control', {}).get('Window_Title', "VALO360 指令通"))
        self.vars["_Window_Title"] = tk.StringVar(value=window_title)
        self.create_entry(basic_frame, "Window_Title", "視窗標題", '', 0)
        ttk.Label(basic_frame, text="(不包含版本號)").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5))

        # --- DUT 控制區 ---
        dut_frame = ttk.LabelFrame(scrollable_frame, text="DUT 控制區", padding=(10, 5))
        dut_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        dut_frame.columnconfigure(1, weight=1)

        dut_settings = [
            ("Serial_COM_Port", "序列通訊埠 (COM Port)"),
            ("Default_IP_Address", "預設 IP 位址"),
            ("Command_Timeout_Seconds", "指令超時 (秒)"),
            ("Command_End_String", "指令結束字串"),
            ("UI_Font_Size", "介面字體大小"),
            ("Content_Font_Size", "內容字體大小"),
        ]
        for i, (key, text) in enumerate(dut_settings):
            self.create_entry(dut_frame, key, text, 'DUT_Control', i)

        self.create_checkbox(dut_frame, "Auto_Execute", "啟動時自動執行指令", 'DUT_Control', len(dut_settings))
        self.create_file_picker(dut_frame, "Command_File_Path", "指令檔路徑", 'DUT_Control', len(dut_settings) + 1)
        
        # 新增：區段標題預覽區域
        preview_frame = ttk.LabelFrame(dut_frame, text="區段標題預覽", padding=(5, 5))
        preview_frame.grid(row=len(dut_settings) + 2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        preview_frame.columnconfigure(0, weight=1)
        
        self.preview_listbox = tk.Listbox(preview_frame, height=5)
        self.preview_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 預覽說明文字
        preview_label = ttk.Label(preview_frame, text="選擇指令檔案後，這裡會顯示檔案中的區段標題。\n儲存設定後，這些標題將成為DUT控制頁面的按鈕。")
        preview_label.pack(fill="x", padx=5, pady=5)

        # --- 治具控制區 ---
        fixture_frame = ttk.LabelFrame(scrollable_frame, text="治具控制區", padding=(10, 5))
        fixture_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        fixture_frame.columnconfigure(1, weight=1)

        self.create_entry(fixture_frame, "Fixture_COM_Port", "治具通訊埠 (COM Port)", 'Fixture_Control', 0)
        self.create_entry(fixture_frame, "Fixture_Font_Size", "治具字體大小", 'Fixture_Control', 1)
        
        self.create_checkbox(fixture_frame, "Test_Category_FUNCTION", "顯示 FUNCTION 測試類別", 'Fixture_Control', 2)
        self.create_checkbox(fixture_frame, "Test_Category_MB", "顯示 MB 測試類別", 'Fixture_Control', 3)
        self.create_checkbox(fixture_frame, "Test_Category_Original_Commands", "顯示原始指令測試類別", 'Fixture_Control', 4)

        # --- Save Button ---
        save_button = ttk.Button(scrollable_frame, text="儲存設定", command=self.save_settings)
        save_button.grid(row=3, column=0, sticky="e", padx=10, pady=10)

    def create_entry(self, parent, key, text, section, row):
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", pady=2)
        self.vars[f"{section}_{key}"] = tk.StringVar()
        entry = ttk.Entry(parent, textvariable=self.vars[f"{section}_{key}"])
        entry.grid(row=row, column=1, sticky="ew", padx=5, pady=2)

    def create_checkbox(self, parent, key, text, section, row):
        self.vars[f"{section}_{key}"] = tk.BooleanVar()
        cb = ttk.Checkbutton(parent, text=text, variable=self.vars[f"{section}_{key}"])
        cb.grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
        
    def create_file_picker(self, parent, key, text, section, row):
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", pady=2)
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        frame.columnconfigure(0, weight=1)

        self.vars[f"{section}_{key}"] = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=self.vars[f"{section}_{key}"])
        entry.grid(row=0, column=0, sticky="ew")
        
        button = ttk.Button(frame, text="選擇檔案", command=lambda: self.select_command_file(f"{section}_{key}"))
        button.grid(row=0, column=1, padx=5)

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
            self.setup_data.setdefault('DUT_Control', {})['Section_Titles'] = self.sections_preview
            
            print(f"[DEBUG] 從指令檔案中讀取到 {len(self.sections_preview)} 個區段標題: {self.sections_preview}")
        except Exception as e:
            messagebox.showerror("錯誤", f"讀取指令檔案失敗：{e}")
            print(f"[ERROR] 讀取指令檔案失敗：{e}")
            import traceback
            traceback.print_exc()

    def update_preview_listbox(self):
        """更新預覽列表框"""
        self.preview_listbox.delete(0, tk.END)
        for section in self.sections_preview:
            self.preview_listbox.insert(tk.END, section)
        
        if not self.sections_preview:
            self.preview_listbox.insert(tk.END, "未找到區段標題")

    def load_settings(self):
        # 載入視窗標題
        window_title = self.setup_data.get('Window_Title', "VALO360 指令通")
        if "_Window_Title" in self.vars:
            self.vars["_Window_Title"].set(window_title)
            print(f"[DEBUG] 載入視窗標題: {window_title}")
        
        # 載入其他設定
        for section, settings in self.setup_data.items():
            if isinstance(settings, dict):
                for key, value in settings.items():
                    var_name = f"{section}_{key}"
                    if var_name in self.vars:
                        self.vars[var_name].set(value)
        
        # Handle default display for command file path
        if not self.vars.get("DUT_Control_Command_File_Path", tk.StringVar()).get():
            self.vars["DUT_Control_Command_File_Path"].set("預設: command.txt (與EXE同目錄)")
        else:
            # 如果已有指令檔路徑，立即讀取區段標題
            filepath = self.vars["DUT_Control_Command_File_Path"].get()
            if os.path.exists(filepath):
                self.read_section_titles(filepath)

    def save_settings(self):
        try:
            # 保存視窗標題 (保存到頂層)
            new_window_title = self.vars["_Window_Title"].get()
            self.setup_data['Window_Title'] = new_window_title
            print(f"[DEBUG] SettingsTab: 設置頂層視窗標題為: {new_window_title}")
            
            # 保存其他設定
            for section, settings in self.setup_data.items():
                if isinstance(settings, dict):
                    for key in settings:
                        var_name = f"{section}_{key}"
                        if var_name in self.vars:
                            new_value = self.vars[var_name].get()
                            # Clear default display text before saving
                            if key == "Command_File_Path" and "預設:" in str(new_value):
                                self.setup_data[section][key] = ""
                            else:
                                self.setup_data[section][key] = new_value
            
            # 確保區段標題被保存
            if self.sections_preview:
                self.setup_data.setdefault('DUT_Control', {})['Section_Titles'] = self.sections_preview

            print(f"[DEBUG] SettingsTab: 即將保存的設定資料: {json.dumps(self.setup_data, indent=2, ensure_ascii=False)}")
            save_setup(self.setup_data)
            
            # 確認設定是否已正確保存
            try:
                saved_setup = load_setup()
                if 'Window_Title' in saved_setup:
                    print(f"[DEBUG] SettingsTab: 確認已保存的視窗標題: {saved_setup['Window_Title']}")
                else:
                    print(f"[ERROR] SettingsTab: 保存後無法找到頂層視窗標題!")
            except Exception as e:
                print(f"[ERROR] SettingsTab: 確認保存設定時發生錯誤: {e}")
            
            messagebox.showinfo("成功", "設定已成功儲存！")
            
            # Call the callback to update the main UI
            if self.on_save_callback:
                print("[DEBUG] Calling on_save_callback...")
                self.on_save_callback()
                
            # 更新當前視窗標題 (使用頂層的 Window_Title)
            # 獲取當前版本號
            current_title = self.master.master.master.title()
            version_part = ""
            if " V" in current_title:
                version_part = " " + current_title.split(" V")[-1]
            
            # 設置新標題
            new_title = f"{new_window_title}{version_part}"
            self.master.master.master.title(new_title)
            print(f"[DEBUG] 視窗標題已立即更新為：{new_title}")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存設定失敗：{e}")
            print(f"[ERROR] 儲存設定失敗：{e}")
            import traceback
            traceback.print_exc()

    def activate(self):
        """當分頁被選中時調用"""
        print("[DEBUG] 設定分頁被啟動，重新載入設定。")
        # 重新載入設定
        self.setup_data = load_setup()
        
        # 更新視窗標題欄位 (優先使用頂層的 Window_Title)
        window_title = self.setup_data.get('Window_Title', self.setup_data.get('DUT_Control', {}).get('Window_Title', "VALO360 指令通"))
        if "_Window_Title" in self.vars:
            current_title = self.vars["_Window_Title"].get()
            if current_title != window_title:
                print(f"[DEBUG] 更新視窗標題欄位: {current_title} -> {window_title}")
                self.vars["_Window_Title"].set(window_title)
        
        # 如果已有指令檔路徑，重新讀取區段標題
        filepath = self.vars.get("DUT_Control_Command_File_Path", tk.StringVar()).get()
        if filepath and os.path.exists(filepath) and not "預設:" in filepath:
            self.read_section_titles(filepath) 