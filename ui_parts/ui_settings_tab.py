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

        # --- DUT 控制區 ---
        dut_frame = ttk.LabelFrame(scrollable_frame, text="DUT 控制區", padding=(10, 5))
        dut_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
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


        # --- 治具控制區 ---
        fixture_frame = ttk.LabelFrame(scrollable_frame, text="治具控制區", padding=(10, 5))
        fixture_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
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

    def load_settings(self):
        for section, settings in self.setup_data.items():
            if isinstance(settings, dict):
                for key, value in settings.items():
                    var_name = f"{section}_{key}"
                    if var_name in self.vars:
                        self.vars[var_name].set(value)
        
        # Handle default display for command file path
        if not self.vars.get("DUT_Control_Command_File_Path", tk.StringVar()).get():
            self.vars["DUT_Control_Command_File_Path"].set("預設: command.txt (與EXE同目錄)")


    def save_settings(self):
        try:
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

            print(f"[DEBUG] SettingsTab: Saving setup_data: {json.dumps(self.setup_data, indent=2, ensure_ascii=False)}")
            save_setup(self.setup_data)
            messagebox.showinfo("成功", "設定已成功儲存！") # 移除重啟提示
            
            # Call the callback to update the main UI
            if self.on_save_callback:
                print("[DEBUG] Calling on_save_callback...")
                self.on_save_callback()

        except Exception as e:
            messagebox.showerror("錯誤", f"儲存設定失敗：{e}")

    def activate(self):
        """當分頁被選中時調用，重新載入設定以確保顯示最新"""
        print("[DEBUG] 設定分頁被啟動，重新載入設定。")
        self.setup_data = load_setup()
        self.load_settings() 