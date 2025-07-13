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

        # 設置兩列佈局
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)  # 讓預覽區域可以擴展

        # --- 基本設定區 ---
        basic_frame = ttk.LabelFrame(main_frame, text="基本設定", padding=(10, 5))
        basic_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 添加視窗標題設定 (優先使用頂層的 Window_Title)
        window_title = self.setup_data.get('Window_Title', self.setup_data.get('DUT_Control', {}).get('Window_Title', "VALO360 指令通"))
        self.vars["_Window_Title"] = tk.StringVar(value=window_title)
        
        ttk.Label(basic_frame, text="視窗標題", width=15).grid(row=0, column=0, sticky="w", pady=2)
        entry = ttk.Entry(basic_frame, textvariable=self.vars["_Window_Title"], width=25)
        entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(basic_frame, text="(不包含版本號)").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5))

        # --- 左側：DUT 控制區 ---
        dut_frame = ttk.LabelFrame(main_frame, text="DUT 控制區", padding=(10, 5))
        dut_frame.grid(row=1, column=0, sticky="nw", padx=5, pady=5)

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
        file_frame.grid(row=len(dut_settings)+1, column=1, sticky="w", padx=5, pady=2)

        self.vars["DUT_Control_Command_File_Path"] = tk.StringVar()
        entry = ttk.Entry(file_frame, textvariable=self.vars["DUT_Control_Command_File_Path"], width=20)
        entry.grid(row=0, column=0, sticky="w")
        
        button = ttk.Button(file_frame, text="選擇", command=lambda: self.select_command_file("DUT_Control_Command_File_Path"), width=5)
        button.grid(row=0, column=1, padx=5)

        # --- 右側：治具控制區 ---
        fixture_frame = ttk.LabelFrame(main_frame, text="治具控制區", padding=(10, 5))
        fixture_frame.grid(row=1, column=1, sticky="nw", padx=5, pady=5)

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

        # --- 區段標題預覽區域 (放在底部) ---
        preview_frame = ttk.LabelFrame(main_frame, text="區段標題預覽", padding=(10, 5))
        preview_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 使用水平佈局，左側放預覽列表，右側放說明文字
        preview_container = ttk.Frame(preview_frame)
        preview_container.pack(fill="both", expand=True, padx=5, pady=5)
        preview_container.columnconfigure(0, weight=1)
        preview_container.columnconfigure(1, weight=1)
        
        # 左側預覽列表
        listbox_frame = ttk.Frame(preview_container)
        listbox_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)
        
        self.preview_listbox = tk.Listbox(listbox_frame, height=4)
        preview_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.preview_listbox.yview)
        self.preview_listbox.configure(yscrollcommand=preview_scrollbar.set)
        
        self.preview_listbox.grid(row=0, column=0, sticky="nsew")
        preview_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 右側說明文字
        preview_label = ttk.Label(preview_container, text="選擇指令檔案後，這裡會顯示檔案中的區段標題。\n儲存設定後，這些標題將成為DUT控制頁面的按鈕。", wraplength=200)
        preview_label.grid(row=0, column=1, sticky="nsw", padx=(5, 0))

        # --- Save Button ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky="e", padx=5, pady=5)
        
        save_button = ttk.Button(button_frame, text="儲存設定", command=self.save_settings)
        save_button.pack(padx=5, pady=5)

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
        # 重新載入設定
        self.setup_data = load_setup()
        
        # 載入視窗標題 (優先使用頂層的 Window_Title)
        window_title = self.setup_data.get('Window_Title', "VALO360 指令通")
        if "_Window_Title" in self.vars:
            self.vars["_Window_Title"].set(window_title)
            print(f"[DEBUG] SettingsTab: 載入視窗標題: {window_title}")
            
            # 確保DUT_Control中的Window_Title與頂層一致
            if 'DUT_Control' in self.setup_data and self.setup_data.get('Window_Title') != self.setup_data['DUT_Control'].get('Window_Title'):
                print(f"[WARNING] SettingsTab: DUT_Control中的視窗標題與頂層不一致，頂層: {self.setup_data.get('Window_Title')}, DUT_Control: {self.setup_data['DUT_Control'].get('Window_Title')}")
                # 自動同步DUT_Control中的Window_Title與頂層
                if 'Window_Title' in self.setup_data:
                    self.setup_data['DUT_Control']['Window_Title'] = self.setup_data['Window_Title']
                    save_setup(self.setup_data)
                    print(f"[DEBUG] SettingsTab: 已自動同步DUT_Control中的視窗標題為: {self.setup_data['Window_Title']}")
        
        # 載入 DUT_Control 設定
        dut_control = self.setup_data.get('DUT_Control', {})
        for key in [
            "Serial_COM_Port", "Default_IP_Address", "Command_Timeout_Seconds", 
            "Command_End_String", "UI_Font_Size", "Content_Font_Size",
            "Auto_Execute", "Command_File_Path"
        ]:
            var_name = f"DUT_Control_{key}"
            if var_name in self.vars:
                if key in dut_control:
                    self.vars[var_name].set(dut_control[key])
                    print(f"[DEBUG] SettingsTab: 載入 DUT_Control.{key} = {dut_control[key]}")
                else:
                    print(f"[WARNING] SettingsTab: 找不到設定 DUT_Control.{key}")
        
        # 載入 Fixture_Control 設定
        fixture_control = self.setup_data.get('Fixture_Control', {})
        for key in [
            "Fixture_COM_Port", "Fixture_Font_Size", 
            "Test_Category_FUNCTION", "Test_Category_MB", "Test_Category_Original_Commands"
        ]:
            var_name = f"Fixture_Control_{key}"
            if var_name in self.vars:
                if key in fixture_control:
                    self.vars[var_name].set(fixture_control[key])
                    print(f"[DEBUG] SettingsTab: 載入 Fixture_Control.{key} = {fixture_control[key]}")
                else:
                    print(f"[WARNING] SettingsTab: 找不到設定 Fixture_Control.{key}")
        
        # 處理指令檔路徑的預設顯示
        if not self.vars.get("DUT_Control_Command_File_Path", tk.StringVar()).get():
            self.vars["DUT_Control_Command_File_Path"].set("預設: command.txt (與EXE同目錄)")
            print("[DEBUG] SettingsTab: 使用預設指令檔路徑顯示")
        else:
            # 如果已有指令檔路徑，立即讀取區段標題
            filepath = self.vars["DUT_Control_Command_File_Path"].get()
            if os.path.exists(filepath):
                print(f"[DEBUG] SettingsTab: 從指令檔路徑讀取區段標題: {filepath}")
                self.read_section_titles(filepath)

    def save_settings(self):
        try:
            # 先讀取最新的 setup.json，避免覆蓋未變動的資料
            current_setup = load_setup()
            
            # 保存視窗標題 (保存到頂層和DUT_Control)
            new_window_title = self.vars["_Window_Title"].get()
            current_setup['Window_Title'] = new_window_title
            print(f"[DEBUG] SettingsTab: 設置頂層視窗標題為: {new_window_title}")
            
            # 確保DUT_Control中也有相同的視窗標題
            if 'DUT_Control' not in current_setup:
                current_setup['DUT_Control'] = {}
            current_setup['DUT_Control']['Window_Title'] = new_window_title
            print(f"[DEBUG] SettingsTab: 同步DUT_Control中的視窗標題為: {new_window_title}")
            
            # 收集所有 DUT_Control 設定
            dut_settings = {}
            for key in [
                "Serial_COM_Port", "Default_IP_Address", "Command_Timeout_Seconds", 
                "Command_End_String", "UI_Font_Size", "Content_Font_Size",
                "Auto_Execute", "Command_File_Path"
            ]:
                var_name = f"DUT_Control_{key}"
                if var_name in self.vars:
                    value = self.vars[var_name].get()
                    # 清除指令檔路徑的預設顯示文字
                    if key == "Command_File_Path" and "預設:" in str(value):
                        dut_settings[key] = ""
                    else:
                        dut_settings[key] = value
                    print(f"[DEBUG] SettingsTab: 設置 DUT_Control.{key} = {value}")
            
            # 確保區段標題被保存
            if self.sections_preview:
                dut_settings['Section_Titles'] = self.sections_preview
                print(f"[DEBUG] SettingsTab: 設置 DUT_Control.Section_Titles = {self.sections_preview}")
            
            # 收集所有 Fixture_Control 設定
            fixture_settings = {}
            for key in [
                "Fixture_COM_Port", "Fixture_Font_Size", 
                "Test_Category_FUNCTION", "Test_Category_MB", "Test_Category_Original_Commands"
            ]:
                var_name = f"Fixture_Control_{key}"
                if var_name in self.vars:
                    value = self.vars[var_name].get()
                    fixture_settings[key] = value
                    print(f"[DEBUG] SettingsTab: 設置 Fixture_Control.{key} = {value}")
            
            # 更新設定結構，保留原有的其他欄位
            if 'DUT_Control' not in current_setup:
                current_setup['DUT_Control'] = {}
            current_setup['DUT_Control'].update(dut_settings)
            
            if 'Fixture_Control' not in current_setup:
                current_setup['Fixture_Control'] = {}
            current_setup['Fixture_Control'].update(fixture_settings)
            
            # 保存設定
            print(f"[DEBUG] SettingsTab: 即將保存的完整設定資料: {json.dumps(current_setup, indent=2, ensure_ascii=False)}")
            save_setup(current_setup)
            
            # 確認設定是否已正確保存
            try:
                saved_setup = load_setup()
                if 'Window_Title' in saved_setup and saved_setup['Window_Title'] == new_window_title:
                    print(f"[DEBUG] SettingsTab: 確認頂層視窗標題已正確保存: {saved_setup['Window_Title']}")
                else:
                    print(f"[WARNING] SettingsTab: 頂層視窗標題可能未正確保存! 期望值: {new_window_title}, 實際值: {saved_setup.get('Window_Title', '未找到')}")
                
                if 'DUT_Control' in saved_setup and 'Window_Title' in saved_setup['DUT_Control'] and saved_setup['DUT_Control']['Window_Title'] == new_window_title:
                    print(f"[DEBUG] SettingsTab: 確認DUT_Control中的視窗標題已正確保存: {saved_setup['DUT_Control']['Window_Title']}")
                else:
                    print(f"[WARNING] SettingsTab: DUT_Control中的視窗標題可能未正確保存!")
                
                # 檢查 DUT_Control 設定
                for key, value in dut_settings.items():
                    if key in saved_setup.get('DUT_Control', {}) and saved_setup['DUT_Control'][key] == value:
                        print(f"[DEBUG] SettingsTab: 確認 DUT_Control.{key} 已正確保存")
                    else:
                        print(f"[WARNING] SettingsTab: DUT_Control.{key} 可能未正確保存!")
                
                # 檢查 Fixture_Control 設定
                for key, value in fixture_settings.items():
                    if key in saved_setup.get('Fixture_Control', {}) and saved_setup['Fixture_Control'][key] == value:
                        print(f"[DEBUG] SettingsTab: 確認 Fixture_Control.{key} 已正確保存")
                    else:
                        print(f"[WARNING] SettingsTab: Fixture_Control.{key} 可能未正確保存!")
                
            except Exception as e:
                print(f"[ERROR] SettingsTab: 確認保存設定時發生錯誤: {e}")
            
            messagebox.showinfo("成功", "設定已成功儲存！")
            
            # Call the callback to update the main UI
            if self.on_save_callback:
                print("[DEBUG] SettingsTab: 呼叫 on_save_callback 更新主介面...")
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
            print(f"[DEBUG] SettingsTab: 視窗標題已立即更新為：{new_title}")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存設定失敗：{e}")
            print(f"[ERROR] SettingsTab: 儲存設定失敗：{e}")
            import traceback
            traceback.print_exc()

    def activate(self):
        """當分頁被選中時調用"""
        print("[DEBUG] SettingsTab: 設定分頁被啟動，重新載入設定。")
        
        # 重新載入所有設定
        setup = load_setup()
        self.setup_data = setup
        
        # 優先使用頂層的Window_Title
        top_window_title = setup.get('Window_Title')
        dut_window_title = setup.get('DUT_Control', {}).get('Window_Title')
        
        if top_window_title is not None:
            # 使用頂層的Window_Title更新UI
            self.vars["_Window_Title"].set(top_window_title)
            print(f"[DEBUG] SettingsTab: 使用頂層視窗標題: {top_window_title}")
            
            # 檢查是否需要同步DUT_Control中的Window_Title
            if top_window_title != dut_window_title and dut_window_title is not None:
                print(f"[DEBUG] SettingsTab: 檢測到Window_Title不一致，頂層: {top_window_title}, DUT_Control: {dut_window_title}")
                # 自動同步DUT_Control中的Window_Title與頂層
                setup['DUT_Control']['Window_Title'] = top_window_title
                save_setup(setup)
                print(f"[DEBUG] SettingsTab: 已自動同步DUT_Control中的視窗標題為: {top_window_title}")
        else:
            # 如果頂層沒有Window_Title，但DUT_Control有，則提升DUT_Control的值到頂層
            if dut_window_title is not None:
                setup['Window_Title'] = dut_window_title
                save_setup(setup)
                self.vars["_Window_Title"].set(dut_window_title)
                print(f"[DEBUG] SettingsTab: 使用 DUT_Control 中的視窗標題: {dut_window_title}")
                print(f"[DEBUG] SettingsTab: 更新視窗標題欄位: {dut_window_title} -> {dut_window_title}")
        
        # 載入其他設定
        self.load_settings()
        
        # 如果已有指令檔路徑，重新讀取區段標題
        filepath = self.vars.get("DUT_Control_Command_File_Path", tk.StringVar()).get()
        if filepath and os.path.exists(filepath) and not "預設:" in filepath:
            print(f"[DEBUG] SettingsTab: 重新讀取指令檔案中的區段標題: {filepath}")
            self.read_section_titles(filepath) 