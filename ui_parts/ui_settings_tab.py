# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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
        # 創建主容器，不使用Canvas滾動，直接使用緊湊佈局
        main_container = ttk.Frame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 設置主容器的列配置
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        
        current_row = 0
        
        # --- 頂部控制區域 ---
        control_frame = ttk.Frame(main_container)
        control_frame.grid(row=current_row, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        current_row += 1
        
        # 設定頁字體大小控制
        font_control_frame = ttk.LabelFrame(control_frame, text="設定頁控制", padding=(10, 4))
        font_control_frame.pack(side=tk.LEFT, fill='y', padx=(0, 10))
        
        ttk.Label(font_control_frame, text="字體大小:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.settings_font_size = tk.StringVar(value="11")
        font_spinbox = ttk.Spinbox(font_control_frame, from_=8, to=16, width=5, textvariable=self.settings_font_size)
        font_spinbox.grid(row=0, column=1, sticky="w", padx=5)
        font_spinbox.bind('<Return>', lambda e: self.apply_font_size())
        
        ttk.Button(font_control_frame, text="套用字體", command=self.apply_font_size).grid(row=0, column=2, padx=5)
        
        # 儲存按鈕
        save_frame = ttk.Frame(control_frame)
        save_frame.pack(side=tk.RIGHT)
        
        ttk.Button(save_frame, text="儲存設定", command=self.save_settings, style="Accent.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(save_frame, text="重新載入", command=self.reload_settings).pack(side=tk.RIGHT, padx=5)
        
        # --- 第一排：應用程式基本設定 + 標籤頁名稱設定 ---
        # 左側：應用程式基本設定
        basic_frame = ttk.LabelFrame(main_container, text="應用程式基本設定", padding=(10, 4))
        basic_frame.grid(row=current_row, column=0, sticky="nsew", padx=(0, 5), pady=(0, 8))
        basic_frame.columnconfigure(1, weight=1)
        
        # 應用程式版本
        ttk.Label(basic_frame, text="應用程式版本:").grid(row=0, column=0, sticky="w", pady=4)
        self.vars["version"] = tk.StringVar(value=self.setup_data.get("version", "V1.5.0.1"))
        ttk.Entry(basic_frame, textvariable=self.vars["version"], width=30).grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)
        
        # 視窗標題
        ttk.Label(basic_frame, text="視窗標題:").grid(row=1, column=0, sticky="w", pady=4)
        self.vars["Window_Title"] = tk.StringVar(value=self.setup_data.get("Window_Title", "VALO360 指令通"))
        ttk.Entry(basic_frame, textvariable=self.vars["Window_Title"], width=30).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=4)
        
        # 視窗大小 - 使用水平排版
        size_frame = ttk.Frame(basic_frame)
        size_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=4)
        size_frame.columnconfigure(1, weight=1)
        size_frame.columnconfigure(3, weight=1)
        
        ttk.Label(size_frame, text="視窗寬度:").grid(row=0, column=0, sticky="w")
        self.vars["Window_Width"] = tk.StringVar(value=self.setup_data.get("Window_Width", "1536"))
        ttk.Entry(size_frame, textvariable=self.vars["Window_Width"], width=8).grid(row=0, column=1, sticky="ew", padx=(5, 10))
        
        ttk.Label(size_frame, text="高度:").grid(row=0, column=2, sticky="w")
        self.vars["Window_Height"] = tk.StringVar(value=self.setup_data.get("Window_Height", "793"))
        ttk.Entry(size_frame, textvariable=self.vars["Window_Height"], width=8).grid(row=0, column=3, sticky="ew", padx=(5, 0))
        
        # 右側：標籤頁名稱設定
        tab_frame = ttk.LabelFrame(main_container, text="標籤頁名稱設定", padding=(10, 4))
        tab_frame.grid(row=current_row, column=1, sticky="nsew", padx=(5, 0), pady=(0, 8))
        tab_frame.columnconfigure(1, weight=1)
        current_row += 1
        
        # 獲取當前的標籤頁名稱
        tab_names = self.setup_data.get('tab_names', {})
        default_tab_names = ['DUT 控制', '治具控制', '使用說明', '設定']
        
        # 創建標籤頁名稱輸入框
        for i in range(4):
            tab_key = f'tab{i}'
            tab_name = tab_names.get(tab_key, default_tab_names[i])
            ttk.Label(tab_frame, text=f"標籤頁 {i+1}:").grid(row=i, column=0, sticky="w", pady=4)
            self.vars[f"tab_names_{tab_key}"] = tk.StringVar(value=tab_name)
            ttk.Entry(tab_frame, textvariable=self.vars[f"tab_names_{tab_key}"], width=25).grid(row=i, column=1, sticky="ew", padx=(10, 0), pady=4)
        
        # --- 第二排：DUT 控制設定 + 治具控制設定 ---
        # 左側：DUT 控制設定
        dut_frame = ttk.LabelFrame(main_container, text="DUT 控制設定", padding=(10, 4))
        dut_frame.grid(row=current_row, column=0, sticky="nsew", padx=(0, 5), pady=(0, 8))
        dut_frame.columnconfigure(1, weight=1)
        
        dut_settings = self.setup_data.get('DUT_Control', {})
        dut_row = 0
        
        # 串口設定
        ttk.Label(dut_frame, text="串口:").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Serial_COM_Port"] = tk.StringVar(value=dut_settings.get("Serial_COM_Port", "COM5"))
        ttk.Entry(dut_frame, textvariable=self.vars["DUT_Serial_COM_Port"], width=25).grid(row=dut_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        dut_row += 1
        
        # 指令超時
        ttk.Label(dut_frame, text="指令超時(秒):").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Command_Timeout_Seconds"] = tk.StringVar(value=dut_settings.get("Command_Timeout_Seconds", "30"))
        ttk.Entry(dut_frame, textvariable=self.vars["DUT_Command_Timeout_Seconds"], width=25).grid(row=dut_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        dut_row += 1
        
        # 指令結束字串
        ttk.Label(dut_frame, text="指令結束字串:").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Command_End_String"] = tk.StringVar(value=dut_settings.get("Command_End_String", "root"))
        ttk.Entry(dut_frame, textvariable=self.vars["DUT_Command_End_String"], width=25).grid(row=dut_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        dut_row += 1
        
        # 預設IP地址
        ttk.Label(dut_frame, text="預設IP地址:").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Default_IP_Address"] = tk.StringVar(value=dut_settings.get("Default_IP_Address", "192.168.11.143"))
        ttk.Entry(dut_frame, textvariable=self.vars["DUT_Default_IP_Address"], width=25).grid(row=dut_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        dut_row += 1
        
        # 字體設定 - 水平排版
        font_frame = ttk.Frame(dut_frame)
        font_frame.grid(row=dut_row, column=0, columnspan=2, sticky="ew", pady=4)
        font_frame.columnconfigure(1, weight=1)
        font_frame.columnconfigure(3, weight=1)
        
        ttk.Label(font_frame, text="UI字體:").grid(row=0, column=0, sticky="w")
        self.vars["DUT_UI_Font_Size"] = tk.StringVar(value=dut_settings.get("UI_Font_Size", "14"))
        ttk.Entry(font_frame, textvariable=self.vars["DUT_UI_Font_Size"], width=6).grid(row=0, column=1, sticky="ew", padx=(5, 10))
        
        ttk.Label(font_frame, text="內容字體:").grid(row=0, column=2, sticky="w")
        self.vars["DUT_Content_Font_Size"] = tk.StringVar(value=dut_settings.get("Content_Font_Size", "11"))
        ttk.Entry(font_frame, textvariable=self.vars["DUT_Content_Font_Size"], width=6).grid(row=0, column=3, sticky="ew", padx=(5, 0))
        dut_row += 1
        
        # 通知字體大小和分割位置 - 水平排版
        misc_frame = ttk.Frame(dut_frame)
        misc_frame.grid(row=dut_row, column=0, columnspan=2, sticky="ew", pady=4)
        misc_frame.columnconfigure(1, weight=1)
        misc_frame.columnconfigure(3, weight=1)
        
        ttk.Label(misc_frame, text="通知字體:").grid(row=0, column=0, sticky="w")
        self.vars["DUT_Notification_Font_Size"] = tk.StringVar(value=dut_settings.get("Notification_Font_Size", "14"))
        ttk.Entry(misc_frame, textvariable=self.vars["DUT_Notification_Font_Size"], width=6).grid(row=0, column=1, sticky="ew", padx=(5, 10))
        
        ttk.Label(misc_frame, text="分割位置:").grid(row=0, column=2, sticky="w")
        self.vars["DUT_Pane_Sash_Position"] = tk.StringVar(value=dut_settings.get("Pane_Sash_Position", "506"))
        ttk.Entry(misc_frame, textvariable=self.vars["DUT_Pane_Sash_Position"], width=6).grid(row=0, column=3, sticky="ew", padx=(5, 0))
        dut_row += 1
        
        # 自動執行
        self.vars["DUT_Auto_Execute"] = tk.BooleanVar(value=dut_settings.get("Auto_Execute", False))
        ttk.Checkbutton(dut_frame, text="啟動後自動執行", variable=self.vars["DUT_Auto_Execute"]).grid(row=dut_row, column=0, columnspan=2, sticky="w", pady=4)
        dut_row += 1
        
        # 指令檔案路徑
        ttk.Label(dut_frame, text="指令檔案路徑:").grid(row=dut_row, column=0, sticky="w", pady=4)
        path_frame = ttk.Frame(dut_frame)
        path_frame.grid(row=dut_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        path_frame.columnconfigure(0, weight=1)
        self.vars["DUT_Command_File_Path"] = tk.StringVar(value=dut_settings.get("Command_File_Path", ""))
        ttk.Entry(path_frame, textvariable=self.vars["DUT_Command_File_Path"]).grid(row=0, column=0, sticky="ew")
        ttk.Button(path_frame, text="瀏覽", command=lambda: self.browse_file("DUT_Command_File_Path")).grid(row=0, column=1, padx=(5,0))
        dut_row += 1
        
        # 右側：治具控制設定
        fixture_frame = ttk.LabelFrame(main_container, text="治具控制設定", padding=(10, 4))
        fixture_frame.grid(row=current_row, column=1, sticky="nsew", padx=(5, 0), pady=(0, 8))
        fixture_frame.columnconfigure(1, weight=1)
        current_row += 1
        
        fixture_settings = self.setup_data.get('Fixture_Control', {})
        fixture_row = 0
        
        # 治具串口
        ttk.Label(fixture_frame, text="治具串口:").grid(row=fixture_row, column=0, sticky="w", pady=4)
        self.vars["Fixture_COM_Port"] = tk.StringVar(value=fixture_settings.get("Fixture_COM_Port", "COM5"))
        ttk.Entry(fixture_frame, textvariable=self.vars["Fixture_COM_Port"], width=25).grid(row=fixture_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        fixture_row += 1
        
        # 治具字體大小
        ttk.Label(fixture_frame, text="治具字體大小:").grid(row=fixture_row, column=0, sticky="w", pady=4)
        self.vars["Fixture_Font_Size"] = tk.StringVar(value=fixture_settings.get("Fixture_Font_Size", "13"))
        ttk.Entry(fixture_frame, textvariable=self.vars["Fixture_Font_Size"], width=25).grid(row=fixture_row, column=1, sticky="ew", padx=(10, 0), pady=4)
        fixture_row += 1
        
        # 測試類別
        ttk.Label(fixture_frame, text="測試類別:", font=('Microsoft JhengHei UI', 10, 'bold')).grid(row=fixture_row, column=0, columnspan=2, sticky="w", pady=(10,4))
        fixture_row += 1
        
        self.vars["Fixture_Test_Category_FUNCTION"] = tk.BooleanVar(value=fixture_settings.get("Test_Category_FUNCTION", True))
        ttk.Checkbutton(fixture_frame, text="FUNCTION測試", variable=self.vars["Fixture_Test_Category_FUNCTION"]).grid(row=fixture_row, column=0, columnspan=2, sticky="w", pady=4)
        fixture_row += 1
        
        self.vars["Fixture_Test_Category_MB"] = tk.BooleanVar(value=fixture_settings.get("Test_Category_MB", True))
        ttk.Checkbutton(fixture_frame, text="MB測試", variable=self.vars["Fixture_Test_Category_MB"]).grid(row=fixture_row, column=0, columnspan=2, sticky="w", pady=4)
        fixture_row += 1
        
        self.vars["Fixture_Test_Category_Original_Commands"] = tk.BooleanVar(value=fixture_settings.get("Test_Category_Original_Commands", True))
        ttk.Checkbutton(fixture_frame, text="原始指令測試", variable=self.vars["Fixture_Test_Category_Original_Commands"]).grid(row=fixture_row, column=0, columnspan=2, sticky="w", pady=4)

    def apply_font_size(self):
        """套用字體大小到所有控件"""
        try:
            size = int(self.settings_font_size.get())
            self.update_all_fonts(size)
        except ValueError:
            messagebox.showerror("錯誤", "字體大小必須是數字")

    def update_all_fonts(self, size):
        """更新所有控件的字體大小"""
        def update_widget_font(widget):
            try:
                if isinstance(widget, (ttk.Label, ttk.Button, ttk.Entry, ttk.Checkbutton)):
                    widget.configure(font=('Microsoft JhengHei UI', size))
            except:
                pass
            
            for child in widget.winfo_children():
                update_widget_font(child)
        
        update_widget_font(self)

    def browse_file(self, var_name):
        """瀏覽檔案"""
        filename = filedialog.askopenfilename(
            title="選取指令檔案",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.vars[var_name].set(filename)
            # 立即保存到setup.json
            try:
                setup = load_setup()
                setup["DUT_Control"]["Command_File_Path"] = filename
                save_setup(setup)
                print(f"[INFO] 指令檔案路徑已更新: {filename}")
            except Exception as e:
                print(f"[ERROR] 保存指令檔案路徑失敗: {e}")
                messagebox.showerror("錯誤", f"保存檔案路徑失敗：{str(e)}")

    def generate_settings_dict(self):
        """根據當前設定生成字典 - 保持現有設定不丟失"""
        # 首先載入現有的完整設定
        current_setup = load_setup()
        
        # 更新基本設定
        current_setup["version"] = self.vars["version"].get()
        current_setup["Window_Title"] = self.vars["Window_Title"].get()
        current_setup["Window_Width"] = self.vars["Window_Width"].get()
        current_setup["Window_Height"] = self.vars["Window_Height"].get()
        
        # 更新標籤頁名稱
        if "tab_names" not in current_setup:
            current_setup["tab_names"] = {}
        current_setup["tab_names"]["tab0"] = self.vars["tab_names_tab0"].get()
        current_setup["tab_names"]["tab1"] = self.vars["tab_names_tab1"].get()
        current_setup["tab_names"]["tab2"] = self.vars["tab_names_tab2"].get()
        current_setup["tab_names"]["tab3"] = self.vars["tab_names_tab3"].get()
        
        # 更新DUT_Control設定
        if "DUT_Control" not in current_setup:
            current_setup["DUT_Control"] = {}
        
        current_setup["DUT_Control"]["Serial_COM_Port"] = self.vars["DUT_Serial_COM_Port"].get()
        current_setup["DUT_Control"]["Command_Timeout_Seconds"] = self.vars["DUT_Command_Timeout_Seconds"].get()
        current_setup["DUT_Control"]["Command_End_String"] = self.vars["DUT_Command_End_String"].get()
        current_setup["DUT_Control"]["Default_IP_Address"] = self.vars["DUT_Default_IP_Address"].get()
        current_setup["DUT_Control"]["UI_Font_Size"] = self.vars["DUT_UI_Font_Size"].get()
        current_setup["DUT_Control"]["Content_Font_Size"] = self.vars["DUT_Content_Font_Size"].get()
        current_setup["DUT_Control"]["Notification_Font_Size"] = self.vars["DUT_Notification_Font_Size"].get()
        current_setup["DUT_Control"]["Pane_Sash_Position"] = self.vars["DUT_Pane_Sash_Position"].get()
        current_setup["DUT_Control"]["Auto_Execute"] = self.vars["DUT_Auto_Execute"].get()
        current_setup["DUT_Control"]["Command_File_Path"] = self.vars["DUT_Command_File_Path"].get()
        
        # 更新Fixture_Control設定
        if "Fixture_Control" not in current_setup:
            current_setup["Fixture_Control"] = {}
            
        current_setup["Fixture_Control"]["Fixture_COM_Port"] = self.vars["Fixture_COM_Port"].get()
        current_setup["Fixture_Control"]["Fixture_Font_Size"] = self.vars["Fixture_Font_Size"].get()
        current_setup["Fixture_Control"]["Test_Category_FUNCTION"] = self.vars["Fixture_Test_Category_FUNCTION"].get()
        current_setup["Fixture_Control"]["Test_Category_MB"] = self.vars["Fixture_Test_Category_MB"].get()
        current_setup["Fixture_Control"]["Test_Category_Original_Commands"] = self.vars["Fixture_Test_Category_Original_Commands"].get()
        
        return current_setup

    def load_settings(self):
        """載入設定到界面"""
        try:
            # 設定已在create_widgets中載入
            pass
        except Exception as e:
            print(f"[ERROR] 載入設定時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"載入設定失敗：{str(e)}")

    def reload_settings(self):
        """重新載入設定"""
        try:
            self.setup_data = load_setup()
            # 更新所有變量
            for var_name, var in self.vars.items():
                if var_name == "version":
                    var.set(self.setup_data.get("version", "V1.5.0.1"))
                elif var_name == "Window_Title":
                    var.set(self.setup_data.get("Window_Title", "VALO360 指令通"))
                elif var_name == "Window_Width":
                    var.set(self.setup_data.get("Window_Width", "1536"))
                elif var_name == "Window_Height":
                    var.set(self.setup_data.get("Window_Height", "793"))
                elif var_name.startswith("tab_names_"):
                    tab_key = var_name.replace("tab_names_", "")
                    tab_names = self.setup_data.get('tab_names', {})
                    var.set(tab_names.get(tab_key, ""))
                elif var_name.startswith("DUT_"):
                    key = var_name.replace("DUT_", "")
                    dut_settings = self.setup_data.get('DUT_Control', {})
                    var.set(dut_settings.get(key, ""))
                elif var_name.startswith("Fixture_"):
                    key = var_name.replace("Fixture_", "")
                    fixture_settings = self.setup_data.get('Fixture_Control', {})
                    if isinstance(var, tk.BooleanVar):
                        var.set(fixture_settings.get(key, False))
                    else:
                        var.set(fixture_settings.get(key, ""))
            
            messagebox.showinfo("成功", "設定已重新載入")
        except Exception as e:
            messagebox.showerror("錯誤", f"重新載入設定失敗：{str(e)}")

    def save_settings(self):
        """儲存設定"""
        try:
            # 生成完整的設定字典（保持現有設定）
            updated_settings = self.generate_settings_dict()
            
            # 保存設定
            save_setup(updated_settings)
            
            # 更新內部設定資料
            self.setup_data = updated_settings
            
            # 顯示成功訊息
            messagebox.showinfo("成功", "設定已成功儲存")
            
            # 調用回調函數通知其他組件更新
            if self.on_save_callback:
                self.on_save_callback()
                
        except Exception as e:
            print(f"[ERROR] 儲存設定時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("錯誤", f"儲存設定失敗：{str(e)}")

    def activate(self):
        """當設定頁被選中時調用"""
        try:
            # 重新載入最新設定
            self.setup_data = load_setup()
            self.load_settings()
            print("[DEBUG] 設定頁已激活並載入最新設定")
        except Exception as e:
            print(f"[ERROR] 激活設定頁時發生錯誤: {e}") 