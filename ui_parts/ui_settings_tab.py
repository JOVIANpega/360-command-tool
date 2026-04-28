# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import json

# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from config_core import load_setup, save_setup
from ui_parts.tooltip import ToolTipManager
from core.error_handler import get_error_handler, safe_execute

class SettingsTab(ttk.Frame):
    def __init__(self, parent, on_save_callback=None, tooltip_manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.parent_frame = self  # 設置parent_frame屬性供字體更新使用
        self.on_save_callback = on_save_callback
        self.setup_data = load_setup()
        self.vars = {}
        
        # 字體大小追蹤變數 (用於即時更新)
        self.font_size_trace_active = False
        
        # 初始化 ToolTip 管理器 - 使用超級簡單的版本
        if tooltip_manager:
            self.tooltip_manager = tooltip_manager
        else:
            try:
                # 優先使用超級簡單的 tooltip 管理器
                from ui_parts.simple_tooltip import get_simple_tooltip_manager
                self.tooltip_manager = get_simple_tooltip_manager()
                print("[DEBUG] 使用超級簡單的 tooltip 管理器")
            except Exception as e:
                print(f"[DEBUG] 超級簡單 tooltip 管理器失敗，嘗試使用原版: {e}")
                try:
                    # 備用：使用原版 tooltip 管理器
                    from ui_parts.tooltip import get_tooltip_manager
                    self.tooltip_manager = get_tooltip_manager()
                    print("[DEBUG] 使用原版 tooltip 管理器")
                except Exception as e2:
                    print(f"[DEBUG] 原版 tooltip 管理器也失敗: {e2}")
                    self.tooltip_manager = None
        
        self.create_widgets()
        self.setup_tooltips()

        # 初始化間隔符號下拉選單
        self.update_separator_combo()

    def create_widgets(self):
        # 1. 創建捲軸容器
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        def _on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.bind('<Configure>', _on_canvas_configure)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # 綁定滑鼠滾輪
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # 2. 創建主容器，使用 PanedWindow 來提供可調整的左右分隔
        self.main_container = ttk.PanedWindow(self.scrollable_frame, orient='horizontal')
        self.main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 左側容器
        left_frame = ttk.Frame(self.main_container)
        self.main_container.add(left_frame, weight=1)
        
        # 右側容器
        right_frame = ttk.Frame(self.main_container)
        self.main_container.add(right_frame, weight=1)
        
        # 讀取並設定分隔位置
        self.after(200, self.restore_sash)
        self.after(500, self.restore_sash)
        
        # 綁定分割位置變更事件，即時記錄
        self._last_known_sash_pos = None
        def on_sash_pos_changed_local(e):
            try:
                pos = self.main_container.sashpos(0)
                if pos > 100:
                    self._last_known_sash_pos = pos
                    # 即時同步到全域管理器 (SharedConfig)
                    try:
                        from ui_parts.shared_config import get_shared_config
                        shared_config = get_shared_config()
                        if 'settings_sash_position' in shared_config.vars:
                            shared_config.vars['settings_sash_position'].set(str(pos))
                    except: pass
                    print(f"[DEBUG] 記錄並同步設定頁面分欄位置: {pos}")
            except: pass
        self.main_container.bind("<ButtonRelease-1>", on_sash_pos_changed_local)
        
        # 移除儲存按鈕區域 - 因為已經移動到DUT控制區塊了
        
        # === 左側內容 ===
        left_container = ttk.Frame(left_frame)
        left_container.pack(fill='both', expand=True, padx=(0, 5))
        
        current_row = 0
        
        # 應用程式基本設定 (對齊優化)
        basic_frame = ttk.LabelFrame(left_container, text="應用程式基本設定", padding=(10, 8))
        basic_frame.pack(fill='x', pady=(0, 10))
        basic_frame.columnconfigure(0, minsize=140) # 讓左側標籤統一寬度
        basic_frame.columnconfigure(1, weight=0)
        
        # 獲取版本號（用於後面的版本與路徑資訊區塊）
        current_version = self.setup_data.get("version", "1.7.1")
        self.vars["version"] = tk.StringVar(value=current_version)
        print(f"[DEBUG] 設定頁面初始化版本號: {current_version}")

        # 視窗標題 - 最多30個字元
        ttk.Label(basic_frame, text="視窗標題 (最多30字元):").grid(row=0, column=0, sticky="w", pady=4)
        self.vars["Window_Title"] = tk.StringVar(value=self.setup_data.get("Window_Title", "指令通"))
        self.title_entry = ttk.Entry(basic_frame, textvariable=self.vars["Window_Title"], width=30)
        self.title_entry.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=4)

        # 綁定字元限制檢查
        self.vars["Window_Title"].trace('w', self.on_title_changed)

        # 添加字元計數標籤
        self.title_count_label = ttk.Label(basic_frame, text=f"({len(self.vars['Window_Title'].get())}/30)",
                                          font=('Microsoft JhengHei UI', 9), foreground='gray')
        self.title_count_label.grid(row=0, column=2, sticky="w", padx=(10, 0), pady=4)
        
        # 視窗大小設定已簡化為自動記錄，初始化變數以維持儲存邏輯
        self.vars["Window_Width"] = tk.StringVar(value=self.setup_data.get("Window_Width", "1536"))
        self.vars["Window_Height"] = tk.StringVar(value=self.setup_data.get("Window_Height", "793"))
        pass
        
        # 使用者介面設定
        ui_frame = ttk.LabelFrame(left_container, text="使用者介面設定", padding=(12, 10))
        ui_frame.pack(fill='x', pady=(0, 15))
        ui_frame.columnconfigure(1, weight=1)
        
        # 初始化 UI_ToolTip_Enabled 變數 (強制開啟)
        self.vars["UI_ToolTip_Enabled"] = tk.BooleanVar(value=True)
        # 確保設定檔中的值也是 True
        if 'UI_Settings' not in self.setup_data:
            self.setup_data['UI_Settings'] = {}
        self.setup_data['UI_Settings']['ToolTip_Enabled'] = True
        
        # ToolTip 提示功能開關 - 已移除，預設強制開啟
        # tooltip_checkbutton = ttk.Checkbutton(ui_frame, text="啟用按鈕提示 (ToolTip)", 
        #                                     variable=self.vars["UI_ToolTip_Enabled"],
        #                                     command=self.on_tooltip_setting_changed)
        # tooltip_checkbutton.grid(row=0, column=0, columnspan=2, sticky="w", pady=4)
        

        
        # DUT 控制設定
        dut_frame = ttk.LabelFrame(left_container, text="DUT 控制設定", padding=(12, 10))
        dut_frame.pack(fill='both', expand=True, pady=(0, 15))

        # SSH 設定 (全寬對齊)
        ssh_frame = ttk.LabelFrame(left_container, text="SSH 設定", padding=(12, 10))
        ssh_frame.pack(fill='x', pady=(0, 15))
        ssh_frame.columnconfigure(0, minsize=140)
        
        ssh_settings = self.setup_data.get("SSH_Settings", {})
        
        # 主機地址
        ttk.Label(ssh_frame, text="主機地址:").grid(row=0, column=0, sticky="w", pady=4)
        self.vars["SSH_Host"] = tk.StringVar(value=ssh_settings.get("Host", "192.168.11.143"))
        # 限制 SSH 主機最多 30 個字並更新計數器
        def limit_ssh_host_len(*args):
            val = self.vars["SSH_Host"].get()
            if len(val) > 30:
                val = val[:30]
                self.vars["SSH_Host"].set(val)
            if hasattr(self, 'ssh_host_count_label'):
                color = 'red' if len(val) >= 30 else 'gray'
                self.ssh_host_count_label.config(text=f"({len(val)}/30)", foreground=color)
        self.vars["SSH_Host"].trace('w', limit_ssh_host_len)

        ssh_host_entry = ttk.Entry(ssh_frame, textvariable=self.vars["SSH_Host"], width=30)
        ssh_host_entry.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=4)
        
        self.ssh_host_count_label = ttk.Label(ssh_frame, text=f"({len(self.vars['SSH_Host'].get())}/30)", 
                                            font=('Microsoft JhengHei UI', 9), foreground='gray')
        self.ssh_host_count_label.grid(row=0, column=2, sticky="w", padx=(10, 0))
        
        # 埠號
        ttk.Label(ssh_frame, text="埠號 (Port):").grid(row=1, column=0, sticky="w", pady=4)
        self.vars["SSH_Port"] = tk.StringVar(value=str(ssh_settings.get("Port", 22)))
        self.ssh_port_entry = ttk.Entry(ssh_frame, textvariable=self.vars["SSH_Port"], width=30)
        self.ssh_port_entry.grid(row=1, column=1, sticky="w", padx=(5, 0), pady=4)
        
        # 預設帳號
        ttk.Label(ssh_frame, text="預設帳號/密碼:").grid(row=2, column=0, sticky="w", pady=4)
        
        # 限制 SSH 帳號最多 40 個字並更新計數器
        def limit_ssh_acc_len(*args):
            val = self.vars["SSH_Default_Account"].get()
            if len(val) > 40:
                val = val[:40]
                self.vars["SSH_Default_Account"].set(val)
            if hasattr(self, 'ssh_acc_count_label'):
                color = 'red' if len(val) >= 40 else 'gray'
                self.ssh_acc_count_label.config(text=f"({len(val)}/40)", foreground=color)
        self.vars["SSH_Default_Account"] = tk.StringVar(value=ssh_settings.get("Default_Account", "root/oelinux123"))
        self.vars["SSH_Default_Account"].trace('w', limit_ssh_acc_len)

        ssh_acc_entry = ttk.Entry(ssh_frame, textvariable=self.vars["SSH_Default_Account"], width=30)
        ssh_acc_entry.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=4)
        
        self.ssh_acc_count_label = ttk.Label(ssh_frame, text=f"({len(self.vars['SSH_Default_Account'].get())}/40)", 
                                           font=('Microsoft JhengHei UI', 9), foreground='gray')
        self.ssh_acc_count_label.grid(row=2, column=2, sticky="w", padx=(10, 0))
        
        # 連線超時
        ttk.Label(ssh_frame, text="連線超時:").grid(row=3, column=0, sticky="w", pady=4)
        self.vars["SSH_Connection_Timeout"] = tk.StringVar(value=str(ssh_settings.get("Connection_Timeout", 30)))
        self.ssh_conn_timeout_entry = ttk.Entry(ssh_frame, textvariable=self.vars["SSH_Connection_Timeout"], width=30)
        self.ssh_conn_timeout_entry.grid(row=3, column=1, sticky="w", padx=(5, 0), pady=4)
        dut_frame.columnconfigure(1, weight=1)
        
        dut_settings = self.setup_data.get('DUT_Control', {})
        dut_row = 0
        
        # 移除串口、指令超時、指令結束字串設定 - 這些設定已移至其他頁面
        
        # 指令間隔符號管理
        separator_frame = ttk.LabelFrame(dut_frame, text="指令間隔符號管理", padding=(5, 2))
        separator_frame.grid(row=dut_row, column=0, columnspan=2, sticky="w", pady=4)
        # 移除 columnconfigure(1, weight=1)
        
        # 當前選擇的間隔符號 (改為可直填入模式)
        ttk.Label(separator_frame, text="當前選擇:").grid(row=0, column=0, sticky="w", pady=2)
        self.vars["DUT_Command_Separator"] = tk.StringVar(value=dut_settings.get("Command_Separator", "|"))
        self.separator_combo = ttk.Combobox(separator_frame, textvariable=self.vars["DUT_Command_Separator"], 
                                           values=["|", "||", "==>"], width=15) # 移除 state="readonly"
        self.separator_combo.grid(row=0, column=1, sticky="w", padx=(5, 10), pady=2)
        self.separator_combo.bind('<<ComboboxSelected>>', self.on_separator_changed)
        
        # 新增自訂間隔符號
        ttk.Label(separator_frame, text="新增自訂:").grid(row=1, column=0, sticky="w", pady=2)
        
        # 輸入框和按鈕的容器，讓它們緊密排列
        input_buttons_container = ttk.Frame(separator_frame)
        input_buttons_container.grid(row=1, column=1, sticky="w", pady=2)
        
        # 輸入框
        self.custom_separator_entry = ttk.Entry(input_buttons_container, width=15)
        self.custom_separator_entry.grid(row=0, column=0, sticky="w")
        
        # +/- 按鈕緊貼輸入框
        ttk.Button(input_buttons_container, text="+", width=2, command=self.add_custom_separator).grid(row=0, column=1, padx=(2, 1))
        ttk.Button(input_buttons_container, text="-", width=2, command=self.remove_custom_separator).grid(row=0, column=2, padx=(1, 0))
        
        # 說明標籤
        separator_help_label = ttk.Label(separator_frame, text="選擇或自訂多重指令的分隔符號，用於 command.txt 中的指令分割",
                                   font=('Microsoft JhengHei UI', 9), foreground='#666666')
        separator_help_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(2, 0))
        
        dut_row += 1
        
        # 預設 IP 地址 UI 已移除，初始化變數以維持儲存邏輯
        self.vars["DUT_Default_IP_Address"] = tk.StringVar(value=dut_settings.get("Default_IP_Address", "192.168.11.143"))

        # 單個指令超時 (回傳超時)
        ttk.Label(dut_frame, text="單個指令待響應超時 (秒):").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Single_Command_Timeout"] = tk.StringVar(value=str(dut_settings.get("Single_Command_Timeout", 10)))
        
        # 使用 tk.Entry 以便更改背景顏色
        self.timeout_entry = tk.Entry(
            dut_frame, 
            textvariable=self.vars["DUT_Single_Command_Timeout"], 
            width=20,
            bg='#FFFACD',  # 淺黃色
            relief='sunken',
            borderwidth=1
        )
        self.timeout_entry.grid(row=dut_row, column=1, sticky="w", padx=(10, 0), pady=4)
        dut_row += 1
        
        # 跟單多重指令間隔時間 (跟單指令時間)
        ttk.Label(dut_frame, text="跟單多重指令間隔 (秒):").grid(row=dut_row, column=0, sticky="w", pady=4)
        self.vars["DUT_Command_Interval"] = tk.StringVar(value=str(dut_settings.get("Command_Interval", 1.0)))
        
        self.interval_entry = tk.Entry(
            dut_frame, 
            textvariable=self.vars["DUT_Command_Interval"], 
            width=20,
            bg='#E6F3FF',  # 淺藍色
            relief='sunken',
            borderwidth=1
        )
        self.interval_entry.grid(row=dut_row, column=1, sticky="w", padx=(10, 0), pady=4)
        dut_row += 1
        

        

        


        self.vars["DUT_Pane_Sash_Position"] = tk.StringVar(value=dut_settings.get("Pane_Sash_Position", "633"))
        self.vars["DUT_Auto_Execute"] = tk.BooleanVar(value=dut_settings.get("Auto_Execute", False))

        # 字體設定已移至DUT控制標籤頁，此處不再顯示
        # 保留註解以說明字體設定位置
        
        # === 儲存設定按鈕區域 (Grid 佈局，增加與上方組件間距) ===
        save_btn_container = ttk.Frame(dut_frame)
        save_btn_container.grid(row=dut_row, column=0, columnspan=3, sticky="w", pady=(40, 15))
        
        self.manual_save_button = tk.Button(
            save_btn_container,
            text="💾 儲存所有設定",
            command=self.manual_save_settings,
            bg='#2E7D32',  # 預設深綠色
            fg='white',
            font=('Microsoft JhengHei UI', 12, 'bold'),
            width=30,
            height=2,
            relief='raised',
            borderwidth=2,
            cursor="hand2"
        )
        self.manual_save_button.grid(row=0, column=0, sticky="w")
        
        # 設置懸停效果 (綠 -> 藍)
        def on_save_enter(e):
            self.manual_save_button.config(bg='#1565C0') # 變為深藍
        def on_save_leave(e):
            self.manual_save_button.config(bg='#2E7D32') # 回到深綠
            
        self.manual_save_button.bind("<Enter>", on_save_enter)
        self.manual_save_button.bind("<Leave>", on_save_leave)

        # 添加說明文字 (使用 grid 並加大 padx 確保不重疊)
        ttk.Label(
            save_btn_container,
            text="(部分設定需重啟生效)",
            font=('Microsoft JhengHei UI', 9),
            foreground='gray'
        ).grid(row=0, column=1, sticky="w", padx=(20, 0))

        dut_row += 1
        
        # 移除版本與路徑資訊區區塊 - 將移動到右側
        dut_row += 1
        
        # === 右側內容 ===
        right_container = ttk.Frame(right_frame)
        right_container.pack(fill='both', expand=True, padx=(5, 0))
        
        # 標籤頁名稱設定 (全寬對齊)
        tab_frame = ttk.LabelFrame(right_container, text="標籤頁名稱設定", padding=(10, 8))
        tab_frame.pack(fill='x', pady=(0, 10))
        tab_frame.columnconfigure(0, minsize=120)
        
        # 獲取當前的標籤頁名稱與顯示狀態
        tab_names = self.setup_data.get('tab_names', {})
        tab_visibility = self.setup_data.get('tab_visibility', {})
        default_tab_names = ['DUT 控制', '治具控制', '手動輸入指令', 'DOS 工具', '設定']

        # 創建標籤頁名稱輸入框與勾選框
        self.tab_count_labels = {}
        for i in range(5):
            tab_key = f'tab{i}'
            tab_name = tab_names.get(tab_key, default_tab_names[i] if i < len(default_tab_names) else f'標籤頁 {i+1}')
            
            # --- 勾選框邏輯 ---
            # 分頁 1 (DUT) 與 分頁 5 (設定) 強制顯示，不提供勾選框
            if i == 0 or i == 4:
                # 建立一個隱藏的變數確保儲存邏輯不變，但在介面上不顯示 Checkbutton
                self.vars[f"tab_visible_{tab_key}"] = tk.BooleanVar(value=True)
                # 放置一個佔位 Label 或是顯示「強制顯示」字樣
                lock_label = ttk.Label(tab_frame, text="🔒", foreground='gray')
                lock_label.grid(row=i, column=0, sticky="w", padx=(5, 10), pady=4)
            else:
                is_visible = tab_visibility.get(tab_key, True)
                v_var = tk.BooleanVar(value=is_visible)
                self.vars[f"tab_visible_{tab_key}"] = v_var
                cb = ttk.Checkbutton(tab_frame, variable=v_var)
                cb.grid(row=i, column=0, sticky="w", padx=(0, 10), pady=4)
            
            # --- 名稱輸入與計數器 ---
            ttk.Label(tab_frame, text=f"分頁 {i+1}:").grid(row=i, column=1, sticky="w", pady=4)
            
            def update_tab_ui(var_name, limit=10, key=tab_key):
                val = self.vars[var_name].get()
                if len(val) > limit:
                    val = val[:limit]
                    self.vars[var_name].set(val)
                if key in self.tab_count_labels:
                    color = 'red' if len(val) >= limit else 'gray'
                    self.tab_count_labels[key].config(text=f"({len(val)}/{limit})", foreground=color)

            self.vars[f"tab_names_{tab_key}"] = tk.StringVar(value=tab_name)
            entry = ttk.Entry(tab_frame, textvariable=self.vars[f"tab_names_{tab_key}"], width=25)
            entry.grid(row=i, column=2, sticky="w", padx=(5, 0), pady=4)
            # 為分頁名稱輸入框命名以利 ToolTip
            setattr(self, f"tab_name_entry_{i}", entry)
            
            count_label = ttk.Label(tab_frame, text=f"({len(tab_name)}/10)", font=('Microsoft JhengHei UI', 9), foreground='gray')
            count_label.grid(row=i, column=3, sticky="w", padx=(10, 0), pady=4)
            self.tab_count_labels[tab_key] = count_label
            
            self.vars[f"tab_names_{tab_key}"].trace('w', lambda *args, name=f"tab_names_{tab_key}", k=tab_key: update_tab_ui(name, 10, k))
        
        # 手動輸入指令提示文字設定 (全寬對齊)
        manual_frame = ttk.LabelFrame(right_container, text="手動輸入指令設定", padding=(10, 8))
        manual_frame.pack(fill='x', pady=(0, 10))
        manual_frame.columnconfigure(0, minsize=120)
        
        ttk.Label(manual_frame, text="提示文字:").grid(row=0, column=0, sticky="w", pady=4)
        
        # 限制提示文字最多 50 個字並更新計數器
        def limit_manual_hint_len(*args):
            val = self.vars["Manual_Hint_Text"].get()
            if len(val) > 50:
                val = val[:50]
                self.vars["Manual_Hint_Text"].set(val)
            if hasattr(self, 'manual_hint_count_label'):
                color = 'red' if len(val) >= 50 else 'gray'
                self.manual_hint_count_label.config(text=f"({len(val)}/50)", foreground=color)

        self.vars["Manual_Hint_Text"] = tk.StringVar(value=self.setup_data.get("Manual_Command", {}).get("Hint_Text", "請輸入指令並按執行"))
        self.vars["Manual_Hint_Text"].trace('w', limit_manual_hint_len)
        
        self.manual_hint_entry = ttk.Entry(manual_frame, textvariable=self.vars["Manual_Hint_Text"], width=35)
        self.manual_hint_entry.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=4)
        
        self.manual_hint_count_label = ttk.Label(manual_frame, text=f"({len(self.vars['Manual_Hint_Text'].get())}/50)", 
                                                font=('Microsoft JhengHei UI', 9), foreground='gray')
        self.manual_hint_count_label.grid(row=0, column=2, sticky="w", padx=(10, 0))
        
        # 添加說明標籤
        manual_help_label = ttk.Label(manual_frame, text="此文字將顯示在手動輸入指令頁面的提示區域",
                                     font=('Microsoft JhengHei UI', 9), foreground='#666666')
        manual_help_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))
        
        # 版本與路徑資訊區塊 (全寬對齊)
        info_frame = ttk.LabelFrame(right_container, text="版本與路徑資訊", padding=(10, 8))
        info_frame.pack(fill='x', pady=(0, 10))
        info_frame.columnconfigure(0, minsize=120)

        # 應用程式版本
        ttk.Label(info_frame, text="程式版本:").grid(row=0, column=0, sticky="w", pady=2)
        
        # 限制版本號最多 12 個字並更新計數器
        def limit_version_len(*args):
            val = self.vars["version"].get()
            if len(val) > 12:
                val = val[:12]
                self.vars["version"].set(val)
            if hasattr(self, 'version_count_label'):
                color = 'red' if len(val) >= 12 else 'gray'
                self.version_count_label.config(text=f"({len(val)}/12)", foreground=color)

        self.vars["version"].trace('w', limit_version_len)

        self.version_entry = ttk.Entry(info_frame, textvariable=self.vars["version"], width=10,
                                 font=('Microsoft JhengHei UI', 10, 'bold'))
        self.version_entry.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=2)
        
        self.version_count_label = ttk.Label(info_frame, text=f"({len(self.vars['version'].get())}/12)", 
                                           font=('Microsoft JhengHei UI', 9), foreground='gray')
        self.version_count_label.grid(row=0, column=2, sticky="w", padx=(3, 0))

        # 指令檔案路徑
        ttk.Label(info_frame, text="指令檔案路徑:").grid(row=1, column=0, sticky="nw", pady=2)
        path_container = ttk.Frame(info_frame)
        path_container.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=2)
        path_container.columnconfigure(0, weight=1)

        default_path = os.path.join("Command_TABLE", "command.txt")
        current_path = dut_settings.get("Command_File_Path", default_path)
        self.vars["DUT_Command_File_Path"] = tk.StringVar(value=current_path)
        
        # 使用 Label 並開啟自動換行 (wraplength)，最多顯示兩行
        path_display = ttk.Label(path_container, textvariable=self.vars["DUT_Command_File_Path"], 
                                foreground="#2196F3", font=('Consolas', 9),
                                wraplength=450, justify="left")
        path_display.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # 為路徑輸入框添加 ToolTip 顯示完整路徑
        if self.tooltip_manager:
            # 即時更新提示內容
            def update_path_tooltip(*args):
                try:
                    path = self.vars["DUT_Command_File_Path"].get()
                    if hasattr(self.tooltip_manager, 'add_tooltip_with_text'):
                        # 修正為 path_display
                        self.tooltip_manager.add_tooltip_with_text(path_display, f"完整路徑:\n{path}")
                except Exception as e:
                    print(f"[DEBUG] 更新路徑 ToolTip 失敗: {e}")
            
            self.vars["DUT_Command_File_Path"].trace('w', update_path_tooltip)
            # 初始化時呼叫一次
            self.after(500, update_path_tooltip) # 延遲一下確保元件已完全初始化

        # 瀏覽按鈕
        self.browse_button = ttk.Button(path_container, text="瀏覽檔案", command=lambda: self.browse_file("DUT_Command_File_Path"))
        self.browse_button.grid(row=1, column=0, sticky="w")

        # 設備標籤設定
        ttk.Label(info_frame, text="設備標籤內容:").grid(row=2, column=0, sticky="nw", pady=2)
        device_label_container = ttk.Frame(info_frame)
        device_label_container.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=2)
        device_label_container.columnconfigure(0, weight=1)

        self.vars["Device_Label"] = tk.StringVar(value=self.setup_data.get("Device_Label", "MU310 : root/oelinux123"))
        
        # 限制設備標籤最多 25 個字並更新計數器
        def limit_device_label_len(*args):
            val = self.vars["Device_Label"].get()
            if len(val) > 25:
                val = val[:25]
                self.vars["Device_Label"].set(val)
            if hasattr(self, 'device_count_label'):
                color = 'red' if len(val) >= 25 else 'gray'
                self.device_count_label.config(text=f"({len(val)}/25)", foreground=color)

        self.vars["Device_Label"].trace('w', limit_device_label_len)

        self.device_label_entry = ttk.Entry(device_label_container, textvariable=self.vars["Device_Label"], width=18)
        self.device_label_entry.grid(row=0, column=0, sticky="w")
        
        self.device_count_label = ttk.Label(device_label_container, text=f"({len(self.vars['Device_Label'].get())}/25)", 
                                          font=('Microsoft JhengHei UI', 9), foreground='gray')
        self.device_count_label.grid(row=0, column=1, sticky="w", padx=(3, 0))

        # 添加說明標籤
        device_help_label = ttk.Label(device_label_container, text="此內容將顯示在DUT控制頁面的清空回應按鈕下方",
                                     font=('Microsoft JhengHei UI', 9), foreground='#666666')
        device_help_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # 自訂啟動名稱設定
        ttk.Label(info_frame, text="自訂啟動名稱:").grid(row=3, column=0, sticky="nw", pady=2)
        startup_label_container = ttk.Frame(info_frame)
        startup_label_container.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=2)
        startup_label_container.columnconfigure(0, weight=1)

        self.vars["Startup_Label"] = tk.StringVar(value=self.setup_data.get("Startup_Label", "TEST"))
        
        # 限制自訂啟動名稱最多 15 個字並更新計數器
        def limit_startup_label_len(*args):
            val = self.vars["Startup_Label"].get()
            if len(val) > 15:
                val = val[:15]
                self.vars["Startup_Label"].set(val)
            if hasattr(self, 'startup_count_label'):
                color = 'red' if len(val) >= 15 else 'gray'
                self.startup_count_label.config(text=f"({len(val)}/15)", foreground=color)

        self.vars["Startup_Label"].trace('w', limit_startup_label_len)

        self.startup_label_entry = ttk.Entry(startup_label_container, textvariable=self.vars["Startup_Label"], width=30)
        self.startup_label_entry.grid(row=0, column=0, sticky="w")
        
        self.startup_count_label = ttk.Label(startup_label_container, text=f"({len(self.vars['Startup_Label'].get())}/15)", 
                                           font=('Microsoft JhengHei UI', 9), foreground='gray')
        self.startup_count_label.grid(row=0, column=1, sticky="w", padx=(10, 0))

        # 添加說明標籤
        startup_help_label = ttk.Label(startup_label_container, text="此名稱將顯示在DUT控制頁面的綠色標籤中",
                                     font=('Microsoft JhengHei UI', 9), foreground='#666666')
        startup_help_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # 儲存按鈕已移至左側 DUT 控制設定下方
        pass

    # 字體設定函式已移至DUT控制標籤頁





    def on_fixture_font_changed(self, event=None):
        """治具字體大小即時更新（僅更新顯示，不自動保存）"""
        try:
            new_size = self.vars["Fixture_Font_Size"].get()
            if new_size.isdigit():
                size = int(new_size)
                if 8 <= size <= 24:
                    # 只更新UI顯示，不自動保存到檔案
                    print(f"[DEBUG] 治具字體大小已變更為 {size}，請點擊保存按鈕以儲存變更")

                    # 通知制具控制頁面更新字體顯示
                    self.apply_fixture_font_changes(size)
        except Exception as e:
            print(f"更新治具字體時發生錯誤: {e}")

    def on_title_changed(self, *args):
        """視窗標題變更時的處理，限制最多50個字元"""
        try:
            current_title = self.vars["Window_Title"].get()
            char_count = len(current_title)
            
            # 更新字元計數顯示
            if hasattr(self, 'title_count_label'):
                color = 'red' if char_count > 30 else 'gray'
                self.title_count_label.config(text=f"({char_count}/30)", foreground=color)
            
            # 如果超過30個字元，截斷
            if char_count > 30:
                truncated_title = current_title[:30]
                self.vars["Window_Title"].set(truncated_title)
                print(f"[WARNING] 視窗標題已截斷至30個字元: {truncated_title}")
                
                # 顯示提示訊息
                print("[NOTIFICATION] 視窗標題已限制為50個字元")
                    
        except Exception as e:
            print(f"[ERROR] 處理視窗標題變更時發生錯誤: {e}")

    def on_separator_changed(self, event=None):
        """指令間隔符號選擇變更時的處理"""
        try:
            new_separator = self.vars["DUT_Command_Separator"].get()
            if new_separator:  # 確保不為空
                print(f"[DEBUG] 間隔符號變更為: '{new_separator}'")
                
                # 立即更新設定檔
                settings = load_setup()
                if 'DUT_Control' not in settings:
                    settings['DUT_Control'] = {}
                
                # 保存當前選擇的間隔符號
                settings['DUT_Control']['Command_Separator'] = new_separator
                
                # 確保自訂間隔符號列表存在
                if 'Custom_Separators' not in settings['DUT_Control']:
                    settings['DUT_Control']['Custom_Separators'] = ["|", "||", "==>"]
                
                # 如果新選擇的符號不在自訂列表中，添加它
                custom_separators = settings['DUT_Control']['Custom_Separators']
                if new_separator not in custom_separators:
                    custom_separators.append(new_separator)
                    settings['DUT_Control']['Custom_Separators'] = custom_separators
                    print(f"[DEBUG] 已將新選擇的間隔符號 '{new_separator}' 添加到自訂列表")
                
                # 保存設定
                save_setup(settings)
                print(f"[INFO] 指令間隔符號已保存到 setup.json: '{new_separator}'")
                
                # 通知其他元件更新
                self.apply_separator_changes_immediately()
                
        except Exception as e:
            print(f"更新指令間隔符號時發生錯誤: {e}")
            import traceback
            traceback.print_exc()




    def add_custom_separator(self):
        """新增自訂間隔符號"""
        try:
            new_separator = self.custom_separator_entry.get().strip()
            if not new_separator:
                messagebox.showwarning("警告", "請輸入間隔符號")
                return
            
            # 讀取當前設定
            settings = load_setup()
            if 'DUT_Control' not in settings:
                settings['DUT_Control'] = {}
            
            # 獲取現有的自訂清單，若不存在則初始化
            custom_separators = settings['DUT_Control'].get('Custom_Separators', ["|", "||", "==>"])
            
            # 檢查是否已存在
            if new_separator in custom_separators:
                messagebox.showwarning("警告", "該間隔符號已存在於清單中")
                # 即使存在，也讓它變成當前選中的值
                self.vars["DUT_Command_Separator"].set(new_separator)
                return
            
            # 添加到列表
            custom_separators.append(new_separator)
            settings['DUT_Control']['Custom_Separators'] = custom_separators
            
            # 立即保存到 setup.json
            save_setup(settings, manual_save=True)
            
            # 立即更新下拉選單的 values
            self.update_separator_combo()
            
            # 讓新輸入的符號變成當前選中的值
            self.vars["DUT_Command_Separator"].set(new_separator)
            
            # 清空新增用的輸入框
            self.custom_separator_entry.delete(0, tk.END)
            
            print(f"[INFO] 已新增並成功套用自訂間隔符號: {new_separator}")
            messagebox.showinfo("成功", f"已新增並選取間隔符號: {new_separator}")
            
        except Exception as e:
            print(f"新增自訂間隔符號時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"新增間隔符號失敗: {e}")

    def remove_custom_separator(self):
        """移除選中的自訂間隔符號"""
        try:
            current_separator = self.vars["DUT_Command_Separator"].get()
            
            # 讀取當前設定
            settings = load_setup()
            if 'DUT_Control' not in settings:
                settings['DUT_Control'] = {}
            if 'Custom_Separators' not in settings['DUT_Control']:
                settings['DUT_Control']['Custom_Separators'] = ["|", "||", "==>"]
            
            custom_separators = settings['DUT_Control']['Custom_Separators']
            
            # 檢查是否為內建符號
            built_in_separators = ["|", "||", "==>"]
            if current_separator in built_in_separators:
                messagebox.showwarning("警告", "無法移除內建的間隔符號")
                return
            
            # 詢問確認
            result = messagebox.askyesno("確認移除", f"確定要移除間隔符號 '{current_separator}' 嗎？")
            if not result:
                return
            
            # 從列表中移除
            if current_separator in custom_separators:
                custom_separators.remove(current_separator)
                settings['DUT_Control']['Custom_Separators'] = custom_separators
                
                # 保存設定 (務必開啟 manual_save 以確保立即寫入)
                save_setup(settings, manual_save=True)
                
                # 重置為預設值
                self.vars["DUT_Command_Separator"].set("|")
                
                # 更新下拉選單
                self.update_separator_combo()
                
                print(f"[INFO] 已移除間隔符號: {current_separator}")
                messagebox.showinfo("成功", f"已移除間隔符號: {current_separator}")
            else:
                messagebox.showwarning("警告", "找不到要移除的間隔符號")
                
        except Exception as e:
            print(f"移除自訂間隔符號時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"移除間隔符號失敗: {e}")

    def update_separator_combo(self):
        """更新間隔符號下拉選單"""
        try:
            # 讀取當前設定
            settings = load_setup()
            if 'DUT_Control' not in settings:
                settings['DUT_Control'] = {}
            if 'Custom_Separators' not in settings['DUT_Control']:
                settings['DUT_Control']['Custom_Separators'] = ["|", "||", "==>"]
            
            custom_separators = settings['DUT_Control']['Custom_Separators']
            
            # 更新下拉選單的值
            self.separator_combo['values'] = custom_separators
            
            print(f"[DEBUG] 間隔符號下拉選單已更新，共 {len(custom_separators)} 個選項")
            
        except Exception as e:
            print(f"更新間隔符號下拉選單時發生錯誤: {e}")

    def on_command_separator_changed(self, event=None):
        """指令間隔符號即時更新（保留原有函式以維持相容性）"""
        self.on_separator_changed(event)



    def apply_separator_changes_immediately(self):
        """立即套用間隔符號變更到所有相關元件"""
        try:
            # 找到主管理器
            parent = self.parent
            while parent and not hasattr(parent, 'dut_ui'):
                parent = getattr(parent, 'parent', None) or getattr(parent, 'master', None)
            
            if parent and hasattr(parent, 'dut_ui'):
                # 通知 DUT 控制頁面重新載入指令
                dut_ui = parent.dut_ui
                if hasattr(dut_ui, 'handlers') and hasattr(dut_ui.handlers, 'parse_commands_by_section'):
                    dut_ui.commands_by_section = dut_ui.handlers.parse_commands_by_section()
                    if hasattr(dut_ui.handlers, 'update_cmd_list'):
                        dut_ui.handlers.update_cmd_list()
                        
        except Exception as e:
            print(f"套用間隔符號變更時發生錯誤: {e}")

    def apply_font_changes_immediately(self):
        """立即套用字體變更到所有相關元件"""
        try:
            # 找到主管理器
            parent = self.parent
            while parent and not hasattr(parent, 'dut_ui'):
                parent = getattr(parent, 'parent', None) or getattr(parent, 'master', None)
            
            if parent and hasattr(parent, 'dut_ui'):
                # 更新 DUT 控制頁面
                dut_ui = parent.dut_ui
                if hasattr(dut_ui, 'update_from_config'):
                    dut_ui.update_from_config()
                
                # 字體設定已移至DUT控制標籤頁，此處不再處理
                    
                    # 觸發字體更新
                    if hasattr(components, 'update_fonts'):
                        components.update_fonts()
                        
        except Exception as e:
            print(f"套用字體變更時發生錯誤: {e}")

    def apply_fixture_font_changes(self, size):
        """套用治具頁面字體變更"""
        try:
            # 找到主管理器
            parent = self.parent
            while parent and not hasattr(parent, 'fixture_ui'):
                parent = getattr(parent, 'parent', None) or getattr(parent, 'master', None)
            
            if parent and hasattr(parent, 'fixture_ui'):
                fixture_ui = parent.fixture_ui
                if hasattr(fixture_ui, 'update_font_size'):
                    fixture_ui.update_font_size(size)
                        
        except Exception as e:
            print(f"套用治具字體變更時發生錯誤: {e}")

    def browse_file(self, var_name):
        """瀏覽檔案並自動更新指令清單"""
        filename = filedialog.askopenfilename(
            title="選取指令檔案",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.vars[var_name].set(filename)
            print(f"[INFO] 指令檔案路徑已變更為: {filename}")
            
            try:
                # 1. 立即儲存設定到 setup.json
                from config_core import load_setup, save_setup
                setup_data = load_setup()
                if "DUT_Control" not in setup_data:
                    setup_data["DUT_Control"] = {}
                setup_data["DUT_Control"]["Command_File_Path"] = filename
                save_setup(setup_data, manual_save=True)
                
                # 2. 同步到全域變數 (SharedConfig)
                from ui_parts.shared_config import get_shared_config
                shared_config = get_shared_config()
                if 'dut_command_file_path' in shared_config.vars:
                    shared_config.vars['dut_command_file_path'].set(filename)
                    
                # 3. 尋找主視窗並即時更新 DUT UI 中的指令列表
                parent = self.parent
                while parent and not hasattr(parent, 'dut_ui'):
                    parent = getattr(parent, 'master', None) or getattr(parent, 'parent', None)
                    
                if parent and hasattr(parent, 'dut_ui'):
                    dut_ui = parent.dut_ui
                    
                    # 重新解析檔案並更新分類
                    if hasattr(dut_ui, 'handlers') and hasattr(dut_ui.handlers, 'parse_commands_by_section'):
                        dut_ui.commands_by_section = dut_ui.handlers.parse_commands_by_section()
                    
                    # 觸發 UI 更新
                    updated = False
                    if hasattr(dut_ui, 'components') and hasattr(dut_ui.components, 'update_cmd_list'):
                        dut_ui.components.update_cmd_list()
                        updated = True
                    if hasattr(dut_ui, 'handlers') and hasattr(dut_ui.handlers, 'update_cmd_list'):
                        dut_ui.handlers.update_cmd_list()
                        updated = True
                        
                    if updated:
                        messagebox.showinfo("成功", f"指令檔案已成功切換！\n\n您現在可以直接在「DUT 控制」分頁中使用新的指令清單。")
                    else:
                        messagebox.showinfo("提示", "檔案路徑已儲存，但無法自動更新介面，請手動重啟程式。")
                else:
                    messagebox.showinfo("提示", "檔案路徑已儲存。請切換回主畫面查看。")
                    
            except Exception as e:
                print(f"[ERROR] 更新指令檔案時發生錯誤：{e}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("錯誤", f"自動更新清單時發生錯誤：\n{e}\n請嘗試手動重啟程式。")

    def generate_settings_dict(self):
        """根據當前設定生成字典 - 保持現有設定不丟失"""
        # 首先載入現有的完整設定
        current_setup = load_setup()
        
        # 更新基本設定
        current_setup["version"] = self.vars["version"].get()
        current_setup["Window_Title"] = self.vars["Window_Title"].get()
        current_setup["Window_Width"] = self.vars["Window_Width"].get()
        current_setup["Window_Height"] = self.vars["Window_Height"].get()
        # 指令傳輸方式已移至 DUT 控制區域，這裡不再重複處理
        
        # 更新標籤頁名稱
        if "tab_names" not in current_setup:
            current_setup["tab_names"] = {}
        current_setup["tab_names"]["tab0"] = self.vars["tab_names_tab0"].get()
        current_setup["tab_names"]["tab1"] = self.vars["tab_names_tab1"].get()
        current_setup["tab_names"]["tab2"] = self.vars["tab_names_tab2"].get()
        current_setup["tab_names"]["tab3"] = self.vars["tab_names_tab3"].get()
        current_setup["tab_names"]["tab4"] = self.vars["tab_names_tab4"].get()
        
        # 更新標籤頁顯示狀態 (隱藏功能關鍵)
        if "tab_visibility" not in current_setup:
            current_setup["tab_visibility"] = {}
        current_setup["tab_visibility"]["tab0"] = bool(self.vars["tab_visible_tab0"].get())
        current_setup["tab_visibility"]["tab1"] = bool(self.vars["tab_visible_tab1"].get())
        current_setup["tab_visibility"]["tab2"] = bool(self.vars["tab_visible_tab2"].get())
        current_setup["tab_visibility"]["tab3"] = bool(self.vars["tab_visible_tab3"].get())
        current_setup["tab_visibility"]["tab4"] = True # 設定頁永遠顯示
        
        # 更新DUT_Control設定
        if "DUT_Control" not in current_setup:
            current_setup["DUT_Control"] = {}
        
        # 移除已刪除的欄位設定
        # current_setup["DUT_Control"]["Serial_COM_Port"] = self.vars["DUT_Serial_COM_Port"].get()
        # current_setup["DUT_Control"]["Command_Timeout_Seconds"] = self.vars["DUT_Command_Timeout_Seconds"].get()
        # current_setup["DUT_Command_End_String"] = self.vars["DUT_Command_End_String"].get()
        current_setup["DUT_Control"]["Command_Separator"] = self.vars["DUT_Command_Separator"].get()
        current_setup["DUT_Control"]["Default_IP_Address"] = self.vars["DUT_Default_IP_Address"].get()
        current_setup["DUT_Control"]["Single_Command_Timeout"] = self.vars["DUT_Single_Command_Timeout"].get()
        current_setup["DUT_Control"]["Command_Interval"] = self.vars["DUT_Command_Interval"].get()
        # 字體設定已移至DUT控制標籤頁，此處不再處理
        current_setup["DUT_Control"]["Pane_Sash_Position"] = self.vars["DUT_Pane_Sash_Position"].get()
        current_setup["DUT_Control"]["Auto_Execute"] = self.vars["DUT_Auto_Execute"].get()
        current_setup["DUT_Control"]["Command_File_Path"] = self.vars["DUT_Command_File_Path"].get()
        
        # 更新 SSH 設定 (新增)
        if "SSH_Settings" not in current_setup:
            current_setup["SSH_Settings"] = {}
        
        current_setup["SSH_Settings"]["Host"] = self.vars["SSH_Host"].get()
        current_setup["SSH_Settings"]["Port"] = int(self.vars["SSH_Port"].get()) if self.vars["SSH_Port"].get().isdigit() else 22
        current_setup["SSH_Settings"]["Default_Account"] = self.vars["SSH_Default_Account"].get()
        current_setup["SSH_Settings"]["Connection_Timeout"] = int(self.vars["SSH_Connection_Timeout"].get()) if self.vars["SSH_Connection_Timeout"].get().isdigit() else 30
        
        # 注意：Fixture_Control 設定已移動至治具控制TAB中，這裡不再處理
        # 只保留基本結構，確保不破壞現有設定
        if "Fixture_Control" not in current_setup:
            current_setup["Fixture_Control"] = {}
        
        # 更新 UI 設定
        if "UI_Settings" not in current_setup:
            current_setup["UI_Settings"] = {}
        current_setup["UI_Settings"]["ToolTip_Enabled"] = self.vars["UI_ToolTip_Enabled"].get()
        
        # 全域字體設定已移至DUT控制標籤頁，此處不再處理

        # 更新設備標籤設定
        current_setup["Device_Label"] = self.vars["Device_Label"].get()

        # 更新啟動標籤設定
        current_setup["Startup_Label"] = self.vars["Startup_Label"].get()
        
        # 更新手動輸入指令設定
        if "Manual_Command" not in current_setup:
            current_setup["Manual_Command"] = {}
        current_setup["Manual_Command"]["Hint_Text"] = self.vars["Manual_Hint_Text"].get()

        return current_setup

    # 移除了 reload_settings 函數及相關程式碼

    def manual_save_settings(self):
        """手動保存設定到 setup.json"""
        import traceback
        try:
            print("[DEBUG] 開始手動保存設定...")

            # 生成設定字典
            settings_dict = self.generate_settings_dict()

            # 獲取當前視窗狀態並添加到設定中
            try:
                # 找到主視窗
                root = self.parent
                while root and not hasattr(root, 'winfo_exists'):
                    root = getattr(root, 'master', None) or getattr(root, 'parent', None)

                if root and hasattr(root, 'winfo_exists') and root.winfo_exists():
                    # 獲取當前視窗大小
                    width = root.winfo_width()
                    height = root.winfo_height()

                    if width > 100 and height > 100:  # 確保視窗大小有效
                        settings_dict['Window_Width'] = str(width)
                        settings_dict['Window_Height'] = str(height)
                        settings_dict['DUT_Control']['Window_Width'] = str(width)
                        settings_dict['DUT_Control']['Window_Height'] = str(height)
                        print(f"[DEBUG] 手動保存：視窗大小 {width}x{height}")

                    # 獲取當前視窗標題（去除版本號）
                    current_title = root.title()
                    window_title = current_title
                    if "_" in current_title:
                        parts = current_title.split("_")
                        if len(parts) >= 2:
                            window_title = "_".join(parts[:-1])
                    elif " V" in current_title:
                        window_title = current_title.split(" V")[0]

                    settings_dict['Window_Title'] = window_title
                    settings_dict['DUT_Control']['Window_Title'] = window_title
                    print(f"[DEBUG] 手動保存：視窗標題 {window_title}")

            except Exception as e:
                print(f"[WARNING] 獲取視窗狀態失敗: {e}")

            # 獲取設定頁面分欄位置
            try:
                # 優先使用即時記錄的位置
                sash_pos = getattr(self, '_last_known_sash_pos', None)
                
                # 如果沒有記錄或記錄無效，嘗試即時獲取
                if sash_pos is None or sash_pos <= 100:
                    self.update_idletasks()
                    try:
                        # 優先嘗試 sash_coord 獲取 X 軸位置
                        sash_pos = self.main_container.sash_coord(0)[0]
                    except:
                        sash_pos = self.main_container.sashpos(0)
                
                if sash_pos and sash_pos > 100:
                    settings_dict['UI_Settings']['Settings_Sash_Position'] = str(sash_pos)
                    print(f"[DEBUG] 手動保存：設定頁面分欄位置 {sash_pos}")
            except Exception as e:
                print(f"[DEBUG] 獲取設定分欄位置失敗: {e}")

            # [關鍵修復] 必須先將 settings_dict 保存到磁碟，否則 SharedConfigManager 會讀取到舊的設定
            print("[DEBUG] 正在寫入 setup.json...")
            save_setup(settings_dict, manual_save=True)
            print("[DEBUG] settings_dict 已寫入磁碟")

            # 強制保存 SharedConfigManager 中的設定
            try:
                from ui_parts.shared_config import get_shared_config
                shared_config = get_shared_config()
                
                # 同步 ToolTip 狀態至全域 (解決 ToolTip 消失問題)
                if 'tooltip_enabled' in shared_config.vars:
                    shared_config.vars['tooltip_enabled'].set(True) # 強制啟用，確保重啟後存在
                
                # 同步設定分欄位置至全域 (解決分隔位置沒記住的問題)
                sash_pos_str = settings_dict['UI_Settings'].get('Settings_Sash_Position', '450')
                if 'settings_sash_position' in shared_config.vars:
                    shared_config.vars['settings_sash_position'].set(sash_pos_str)
                
                # [新增] 同步標籤頁名稱至全域，防止被舊值覆蓋
                if 'tab_names' in settings_dict:
                    for i in range(5):
                        t_key = f'tab{i}'
                        s_key = f'tab_name_{i}'
                        if t_key in settings_dict['tab_names'] and s_key in shared_config.vars:
                            shared_config.vars[s_key].set(settings_dict['tab_names'][t_key])
                            
                # [新增] 同步 DUT 控制相關設定至全域
                if 'DUT_Control' in settings_dict:
                    # 指令檔路徑
                    if 'Command_File_Path' in settings_dict['DUT_Control'] and 'dut_command_file_path' in shared_config.vars:
                         shared_config.vars['dut_command_file_path'].set(settings_dict['DUT_Control']['Command_File_Path'])
                    # 自動執行
                    if 'Auto_Execute' in settings_dict['DUT_Control'] and 'dut_auto_execute' in shared_config.vars:
                         shared_config.vars['dut_auto_execute'].set(settings_dict['DUT_Control']['Auto_Execute'])
                
                if hasattr(shared_config, 'force_save_all'):
                    shared_config.force_save_all()
                    print(f"[DEBUG] SharedConfigManager 強制保存完成 (同步變數: ToolTip, Sash, Tabs, Path)")
            except Exception as e:
                print(f"[WARNING] SharedConfigManager 強制保存失敗: {e}")

            # 立即重新讀取setup.json的所有資料
            print("[DEBUG] 手動儲存完成，重新讀取setup.json...")
            updated_setup = load_setup()

            # 更新本地設定資料
            self.setup_data = updated_setup

            # 重新載入UI顯示的所有設定值
            self.update_ui_from_settings()

            # 調用回調函數通知其他組件設定已更新
            if self.on_save_callback:
                # 傳遞最新的設定資料
                self.on_save_callback(updated_setup)
            
            # 手動更新後再次強制恢復分欄位置
            self.after(100, self.restore_sash)
            
            # 更新手動輸入指令設定
            try:
                # 找到主視窗的 TabManager
                root = self.parent
                while root and not hasattr(root, 'tab_manager'):
                    root = getattr(root, 'master', None) or getattr(root, 'parent', None)
                
                if root and hasattr(root, 'tab_manager'):
                    tab_manager = root.tab_manager
                    if hasattr(tab_manager, 'update_manual_settings'):
                        tab_manager.update_manual_settings()
                        print("[DEBUG] 手動輸入指令設定已更新")
                    
                    # 即時更新手動輸入頁面的提示文字
                    if hasattr(tab_manager, 'manual_ui'):
                        hint_text = self.vars["Manual_Hint_Text"].get()
                        tab_manager.manual_ui.update_hint_text(hint_text)
                        print(f"[DEBUG] 手動輸入頁面提示文字已更新為: {hint_text}")
                        
            except Exception as e:
                print(f"[WARNING] 更新手動輸入指令設定失敗: {e}")

            # 立即更新標籤頁名稱
            self.update_tab_names_immediately()

            # 顯示成功訊息並詢問是否重啟
            msg = "設定已手動儲存並【立即生效】！\n\n大部分變更（超時、IP、分隔符號、標籤名稱）已同步更新。\n是否要立即自動重啟應用程式以確保所有底層變更完整載入？"
            if messagebox.askyesno("設定已更新", msg):
                print("[INFO] 用戶選擇立即重啟應用程式...")
                self.restart_application()
            else:
                print("[DEBUG] 設定已手動儲存並重新載入完成 (用戶選擇不重啟)")

        except Exception as e:
            print(f"[錯誤] 手動儲存設定失敗: {e}")
            traceback.print_exc()
            messagebox.showerror("錯誤", f"手動儲存設定時發生錯誤: {e}")

    def restart_application(self):
        """重啟應用程式"""
        import sys
        import subprocess
        try:
            print("[SYSTEM] 正在重啟應用程式...")
            # 獲取當前執行的 python 解釋器路徑和腳本路徑
            python = sys.executable
            # 重啟當前腳本
            os.execl(python, python, *sys.argv)
        except Exception as e:
            print(f"[ERROR] 重啟應用程式失敗: {e}")
            messagebox.showerror("錯誤", f"自動重啟失敗，請手動重啟程式。\n錯誤訊息: {e}")

    def save_settings(self):
        """儲存設定到 setup.json（保留原有方法以維持相容性）"""
        # 直接調用手動保存方法
        self.manual_save_settings()

    def update_tab_names_immediately(self):
        """立即更新主介面上的標籤頁名稱 (採用物件比對以防止名稱錯位)"""
        try:
            # 找到主視窗的 TabManager
            root = self.parent
            while root and not hasattr(root, 'tab_manager'):
                root = getattr(root, 'master', None) or getattr(root, 'parent', None)
            
            if root and hasattr(root, 'tab_manager'):
                tab_manager = root.tab_manager
                notebook = tab_manager.notebook
                
                # 建立物件與 Key 的對照表
                frame_map = {
                    str(tab_manager.dut_frame): 'tab0',
                    str(tab_manager.fixture_frame): 'tab1',
                    str(tab_manager.manual_frame): 'tab2',
                    str(tab_manager.dos_frame): 'tab3',
                    str(tab_manager.settings_frame): 'tab4'
                }

                # 遍歷所有當前「可見」的分頁
                for tab_id in notebook.tabs():
                    tab_key = frame_map.get(tab_id)
                    if tab_key and f"tab_names_{tab_key}" in self.vars:
                        new_name = self.vars[f"tab_names_{tab_key}"].get()
                        
                        # 截斷長度限制
                        if len(new_name) > 10:
                            new_name = new_name[:9] + "..."
                            
                        # 更新顯示文字
                        notebook.tab(tab_id, text=new_name)
                print("[DEBUG] 標籤頁名稱已即時同步 (採用物件比對防錯位)")
        except Exception as e:
            print(f"[WARNING] 即時更新標籤頁名稱失敗: {e}")

        except Exception as e:
            print(f"[ERROR] 即時更新標籤頁名稱時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def on_tooltip_setting_changed(self):
        """當 ToolTip 設定變更時的處理"""
        try:
            enabled = self.vars["UI_ToolTip_Enabled"].get()
            
            # 立即更新設定檔
            settings = load_setup()
            if "UI_Settings" not in settings:
                settings["UI_Settings"] = {}
            settings["UI_Settings"]["ToolTip_Enabled"] = enabled
            save_setup(settings)
            
            # 更新 ToolTip 管理器狀態
            if self.tooltip_manager:
                self.tooltip_manager.enabled = enabled
            
            # 通知主程式更新
            if self.on_save_callback:
                self.on_save_callback(settings)
            
            status = "啟用" if enabled else "停用"
            print(f"[DEBUG] ToolTip 設定已{status}")
            
        except Exception as e:
            print(f"[ERROR] 更新 ToolTip 設定失敗: {e}")

    def setup_tooltips(self):
        """設定所有元件的 tooltip"""
        if not self.tooltip_manager:
            print("[DEBUG] tooltip_manager 為空，跳過 tooltip 設定")
            return
            
        print("[DEBUG] 開始設定設定標籤頁的 tooltip...")
        
        # 1. 基本設定
        if hasattr(self, 'title_entry'):
            self.tooltip_manager.add_tooltip(self.title_entry, "entry_window_title")
        
        # 2. SSH 設定
        if hasattr(self, 'ssh_host_entry'):
            self.tooltip_manager.add_tooltip(self.ssh_host_entry, "entry_ssh_host")
        if hasattr(self, 'ssh_port_entry'):
            self.tooltip_manager.add_tooltip(self.ssh_port_entry, "entry_ssh_port")
        if hasattr(self, 'ssh_acc_entry'):
            self.tooltip_manager.add_tooltip(self.ssh_acc_entry, "entry_ssh_account")
        if hasattr(self, 'ssh_conn_timeout_entry'):
            self.tooltip_manager.add_tooltip(self.ssh_conn_timeout_entry, "entry_ssh_timeout")
        
        # 3. DUT 控制設定
        if hasattr(self, 'separator_combo'):
            self.tooltip_manager.add_tooltip(self.separator_combo, "combobox_separator")
        if hasattr(self, 'custom_separator_entry'):
            self.tooltip_manager.add_tooltip(self.custom_separator_entry, "entry_custom_separator")
        if hasattr(self, 'timeout_entry'):
            self.tooltip_manager.add_tooltip(self.timeout_entry, "entry_single_timeout")
        if hasattr(self, 'interval_entry'):
            self.tooltip_manager.add_tooltip(self.interval_entry, "entry_command_interval")
            
        # 4. 右側資訊設定
        for i in range(5):
            entry_name = f"tab_name_entry_{i}"
            if hasattr(self, entry_name):
                self.tooltip_manager.add_tooltip(getattr(self, entry_name), "entry_tab_name")
        
        if hasattr(self, 'manual_hint_entry'):
            self.tooltip_manager.add_tooltip(self.manual_hint_entry, "entry_manual_hint")
        if hasattr(self, 'version_entry'):
            self.tooltip_manager.add_tooltip(self.version_entry, "entry_version")
        if hasattr(self, 'device_label_entry'):
            self.tooltip_manager.add_tooltip(self.device_label_entry, "entry_device_label")
        if hasattr(self, 'startup_label_entry'):
            self.tooltip_manager.add_tooltip(self.startup_label_entry, "entry_startup_label")
        if hasattr(self, 'browse_button'):
            self.tooltip_manager.add_tooltip(self.browse_button, "btn_browse_file")
            
        # 5. 儲存按鈕
        if hasattr(self, 'manual_save_button'):
            self.tooltip_manager.add_tooltip(self.manual_save_button, "btn_manual_save")
                                    except:
                                        pass
                                    
                                    # 根據標籤文字添加相應的 tooltip
                                    if "視窗標題" in parent_text:
                                        self.tooltip_manager.add_tooltip(grandchild, "entry_window_title")
                                        print(f"[DEBUG] 為視窗標題輸入框添加 tooltip: {parent_text}")
                                    elif "視窗寬度" in parent_text:
                                        self.tooltip_manager.add_tooltip(grandchild, "entry_window_width")
                                        print(f"[DEBUG] 為視窗寬度輸入框添加 tooltip: {parent_text}")
                                    elif "視窗高度" in parent_text:
                                        self.tooltip_manager.add_tooltip(grandchild, "entry_window_height")
                                        print(f"[DEBUG] 為視窗高度輸入框添加 tooltip: {parent_text}")
                                    elif "串口" in parent_text:
                                        self.tooltip_manager.add_tooltip(grandchild, "entry_com_port")
                                        print(f"[DEBUG] 為串口輸入框添加 tooltip: {parent_text}")
                                    elif "指令超時" in parent_text:
                                        self.tooltip_manager.add_tooltip(grandchild, "entry_timeout")
                                        print(f"[DEBUG] 為指令超時輸入框添加 tooltip: {parent_text}")
                                    elif "指令結束字串" in parent_text:
                                        self.tooltip_manager.add_tooltip(grandchild, "entry_end_string")
                                        print(f"[DEBUG] 為指令結束字串輸入框添加 tooltip: {parent_text}")
                                    elif "指令間隔符號" in parent_text:
                                        self.tooltip_manager.add_tooltip(grandchild, "entry_separator")
                                        print(f"[DEBUG] 為指令間隔符號輸入框添加 tooltip: {parent_text}")
                                    elif "預設IP地址" in parent_text:
                                        self.tooltip_manager.add_tooltip(grandchild, "entry_ip_address")
                                        print(f"[DEBUG] 為預設IP地址輸入框添加 tooltip: {parent_text}")
                                    elif "應用程式版本" in parent_text:
                                        self.tooltip_manager.add_tooltip(grandchild, "entry_version")
                                        print(f"[DEBUG] 為應用程式版本輸入框添加 tooltip: {parent_text}")
                                    elif "指令檔案路徑" in parent_text:
                                        self.tooltip_manager.add_tooltip(grandchild, "entry_command_file")
                                        print(f"[DEBUG] 為指令檔案路徑輸入框添加 tooltip: {parent_text}")
                                    elif "設備標籤內容" in parent_text:
                                        self.tooltip_manager.add_tooltip(grandchild, "entry_device_label")
                                        print(f"[DEBUG] 為設備標籤內容輸入框添加 tooltip: {parent_text}")
                                    elif "自訂啟動名稱" in parent_text:
                                        self.tooltip_manager.add_tooltip(grandchild, "entry_startup_label")
                                        print(f"[DEBUG] 為自訂啟動名稱輸入框添加 tooltip: {parent_text}")
                                    elif "提示文字" in parent_text:
                                        self.tooltip_manager.add_tooltip(grandchild, "entry_manual_hint")
                                        print(f"[DEBUG] 為提示文字輸入框添加 tooltip: {parent_text}")
                                    else:
                                        # 為其他輸入框添加通用 tooltip
                                        self.tooltip_manager.add_tooltip_with_text(grandchild, "輸入框")
                                        print(f"[DEBUG] 為未知輸入框添加通用 tooltip: {parent_text}")
                                        
        except Exception as e:
            print(f"[WARNING] 自動添加 tooltip 時發生錯誤: {e}")
        
        print(f"[DEBUG] 設定標籤頁 tooltip 設定完成，共處理了 {len(self.tooltip_manager.tooltips)} 個元件")

    def activate(self):
        """當分頁被選中時調用"""
        # 重新載入最新設定
        self.setup_data = load_setup()
        
        # 更新所有 UI 控件的值
        self.update_ui_from_settings()
        
        # 恢復分欄位置
        self.after(100, self.restore_sash)
        
        print("[DEBUG] 設定分頁已激活並更新 (包含分欄位置)")

    def sync_current_window_size(self):
        """同步當前視窗大小到設定欄位"""
        try:
            # 獲取主視窗
            root = self.winfo_toplevel()
            if root and hasattr(root, 'winfo_exists') and root.winfo_exists():
                width = root.winfo_width()
                height = root.winfo_height()

                # 更新設定欄位
                self.vars["Window_Width"].set(str(width))
                self.vars["Window_Height"].set(str(height))
                print(f"[DEBUG] 已同步當前視窗大小: {width}x{height}")
        except Exception as e:
            print(f"[ERROR] 同步視窗大小失敗: {e}")

    def start_window_size_sync(self):
        """啟動定時同步視窗大小"""
        def update_window_size():
            try:
                # 獲取主視窗
                root = self.winfo_toplevel()
                if root and hasattr(root, 'winfo_exists') and root.winfo_exists():
                    width = root.winfo_width()
                    height = root.winfo_height()

                    # 只有當值真正改變時才更新，避免無限循環
                    current_width = self.vars["Window_Width"].get()
                    current_height = self.vars["Window_Height"].get()

                    if current_width != str(width) or current_height != str(height):
                        self.vars["Window_Width"].set(str(width))
                        self.vars["Window_Height"].set(str(height))

                # 每秒更新一次
                self.after(1000, update_window_size)
            except Exception as e:
                # 靜默處理錯誤，避免干擾用戶操作
                self.after(1000, update_window_size)

        # 啟動定時更新
        self.after(1000, update_window_size)

    def update_ui_from_settings(self):
        """從設定更新 UI 控件的值"""
        try:
            # 更新基本設定 - 版本號直接從setup_data讀取
            current_version = self.setup_data.get("version", "1.6.2.0")
            self.vars["version"].set(current_version)
            print(f"[DEBUG] 設定頁面版本號更新為: {current_version}")
            window_title = self.setup_data.get("Window_Title", "指令通")
            self.vars["Window_Title"].set(window_title)
            # 更新字元計數顯示
            if hasattr(self, 'title_count_label'):
                char_count = len(window_title)
                color = 'red' if char_count > 50 else 'gray'
                self.title_count_label.config(text=f"({char_count}/50)", foreground=color)
            self.vars["Window_Width"].set(self.setup_data.get("Window_Width", "1536"))
            self.vars["Window_Height"].set(self.setup_data.get("Window_Height", "793"))
            
            # 更新標籤頁名稱與顯示狀態
            tab_names = self.setup_data.get('tab_names', {})
            tab_visibility = self.setup_data.get('tab_visibility', {})
            for i in range(5):
                tab_key = f'tab{i}'
                # 更新名稱
                if f"tab_names_{tab_key}" in self.vars:
                    default_names = ['DUT 控制', '治具控制', '手動輸入指令', 'DOS 工具', '設定']
                    self.vars[f"tab_names_{tab_key}"].set(tab_names.get(tab_key, default_names[i] if i < len(default_names) else f'標籤頁 {i+1}'))
                # 更新顯示勾選狀態
                if f"tab_visible_{tab_key}" in self.vars:
                    self.vars[f"tab_visible_{tab_key}"].set(tab_visibility.get(tab_key, True))
            
            # 更新 DUT 控制設定
            dut_settings = self.setup_data.get('DUT_Control', {})
            # 移除已刪除的欄位設定
            # self.vars["DUT_Serial_COM_Port"].set(dut_settings.get("Serial_COM_Port", "COM5"))
            # self.vars["DUT_Command_Timeout_Seconds"].set(dut_settings.get("Command_Timeout_Seconds", "30"))
            # self.vars["DUT_Command_End_String"].set(dut_settings.get("Command_End_String", "root"))
            self.vars["DUT_Command_Separator"].set(dut_settings.get("Command_Separator", "|"))
            self.vars["DUT_Default_IP_Address"].set(dut_settings.get("Default_IP_Address", "192.168.11.143"))
            self.vars["DUT_Single_Command_Timeout"].set(str(dut_settings.get("Single_Command_Timeout", 10)))
            self.vars["DUT_Command_Interval"].set(str(dut_settings.get("Command_Interval", 1.0)))
            # 字體設定已移至DUT控制標籤頁，此處不再處理
            self.vars["DUT_Pane_Sash_Position"].set(dut_settings.get("Pane_Sash_Position", "633"))
            self.vars["DUT_Auto_Execute"].set(dut_settings.get("Auto_Execute", False))
            self.vars["DUT_Command_File_Path"].set(dut_settings.get("Command_File_Path", ""))
            
            # 注意：治具控制設定已移動至治具控制TAB中，這裡不再處理
            
            # 更新 UI 設定
            ui_settings = self.setup_data.get('UI_Settings', {})
            self.vars["UI_ToolTip_Enabled"].set(ui_settings.get("ToolTip_Enabled", True))

            # 更新 SSH 設定 (新增)
            ssh_settings = self.setup_data.get("SSH_Settings", {})
            self.vars["SSH_Host"].set(ssh_settings.get("Host", "192.168.11.143"))
            self.vars["SSH_Port"].set(str(ssh_settings.get("Port", 22)))
            self.vars["SSH_Default_Account"].set(ssh_settings.get("Default_Account", "root/oelinux123"))
            self.vars["SSH_Connection_Timeout"].set(str(ssh_settings.get("Connection_Timeout", 30)))
            
            # 更新其他設定 (新增)
            self.vars["Device_Label"].set(self.setup_data.get("Device_Label", "MU310 : root/oelinux123"))
            self.vars["Startup_Label"].set(self.setup_data.get("Startup_Label", "TEST"))
            
            manual_cmd = self.setup_data.get("Manual_Command", {})
            self.vars["Manual_Hint_Text"].set(manual_cmd.get("Hint_Text", "請輸入指令並按執行"))
            
        except Exception as e:
            print(f"[ERROR] 更新 UI 設定時發生錯誤: {e}")

    def restore_sash(self):
        """恢復 PanedWindow 分割位置"""
        try:
            # 優先從即時記錄的位置恢復
            saved_sash_pos = getattr(self, '_last_known_sash_pos', None)
            
            # 如果沒有，嘗試從全域管理器 (SharedConfig) 獲取
            if not saved_sash_pos or saved_sash_pos <= 100:
                try:
                    from ui_parts.shared_config import get_shared_config
                    shared_config = get_shared_config()
                    if 'settings_sash_position' in shared_config.vars:
                        val = shared_config.vars['settings_sash_position'].get()
                        if val and int(val) > 100:
                            saved_sash_pos = int(val)
                except: pass

            # 如果還是沒有，才從目前的 setup_data (可能是剛從磁碟載入的) 獲取
            if not saved_sash_pos or saved_sash_pos <= 100:
                ui_settings = self.setup_data.get("UI_Settings", {})
                saved_sash_pos = ui_settings.get("Settings_Sash_Position")
            
            # 最後保險：從磁碟重新載入
            if not saved_sash_pos:
                fresh_setup = load_setup()
                saved_sash_pos = fresh_setup.get("UI_Settings", {}).get("Settings_Sash_Position", 450)
            
            pos = int(saved_sash_pos)
            if pos > 0:
                self.main_container.sashpos(0, pos)
                self._last_known_sash_pos = pos # 同步更新本地記錄
                print(f"[DEBUG] 設定頁面分欄位置恢復成功: {pos}")
        except Exception as e:
            print(f"[DEBUG] 恢復設定分欄位置異常: {e}")
            try:
                self.main_container.sashpos(0, 450)
            except:
                pass













 