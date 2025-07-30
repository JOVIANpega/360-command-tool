# -*- coding: utf-8 -*-
"""
DOS標籤頁模組
提供DOS視窗開啟和批次檔執行功能
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess

class DosTab:
    """DOS標籤頁類"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.dos_process = None
        self.init_dos_tab()
    
    def init_dos_tab(self):
        """初始化DOS標籤頁"""
        self.parent_frame.grid_rowconfigure(0, weight=1)
        self.parent_frame.grid_columnconfigure(0, weight=1)
        
        # 創建主框架
        dos_main_frame = ttk.LabelFrame(
            self.parent_frame, 
            text="DOS 工具", 
            padding=20, 
            style="Main.TLabelframe"
        )
        dos_main_frame.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        dos_main_frame.grid_columnconfigure(0, weight=1)
        
        # 獲取版本號
        try:
            from config_utils import get_app_version
            app_version = get_app_version()
        except:
            app_version = "1.7.1"
        
        # 標題
        title_label = ttk.Label(
            dos_main_frame,
            text=f"VALO360 指令通 V{app_version} - DOS 工具",
            font=('Microsoft JhengHei UI', 16, 'bold'),
            style="TLabel"
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # DOS視窗區域
        dos_window_frame = ttk.LabelFrame(dos_main_frame, text="DOS 視窗控制", padding=15)
        dos_window_frame.grid(row=1, column=0, sticky='ew', pady=(0, 20))
        dos_window_frame.grid_columnconfigure(0, weight=1)
        
        # DOS視窗說明
        dos_desc_label = ttk.Label(
            dos_window_frame,
            text="開啟 DOS 命令提示字元視窗，方便執行系統指令",
            font=('Microsoft JhengHei UI', 11),
            style="TLabel"
        )
        dos_desc_label.grid(row=0, column=0, pady=(0, 15))
        
        # 開啟DOS視窗按鈕
        dos_button = tk.Button(
            dos_window_frame,
            text="開啟 DOS 視窗",
            command=self.open_dos_window,
            font=('Microsoft JhengHei UI', 14, 'bold'),
            width=20,
            height=2,
            bg='#4CAF50',
            fg='white',
            relief='groove',
            borderwidth=2,
            highlightthickness=0
        )
        dos_button.grid(row=1, column=0, pady=10)
        
        # 按鈕 hover 效果
        dos_button.bind("<Enter>", lambda e: dos_button.config(bg="#45a049"))
        dos_button.bind("<Leave>", lambda e: dos_button.config(bg="#4CAF50"))
        
        # 批次檔執行區域
        batch_frame = ttk.LabelFrame(dos_main_frame, text="批次檔執行", padding=15)
        batch_frame.grid(row=2, column=0, sticky='ew', pady=(0, 20))
        batch_frame.grid_columnconfigure(1, weight=1)
        
        # 批次檔說明
        batch_desc_label = ttk.Label(
            batch_frame,
            text="選擇並執行批次檔 (.bat, .cmd)",
            font=('Microsoft JhengHei UI', 11),
            style="TLabel"
        )
        batch_desc_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))
        
        # 批次檔路徑
        ttk.Label(batch_frame, text="批次檔路徑:").grid(row=1, column=0, sticky="w", pady=5)
        self.batch_path_var = tk.StringVar()
        batch_path_entry = ttk.Entry(batch_frame, textvariable=self.batch_path_var, width=50)
        batch_path_entry.grid(row=1, column=1, sticky="ew", padx=(10, 10), pady=5)
        
        # 瀏覽按鈕
        browse_button = ttk.Button(
            batch_frame,
            text="瀏覽",
            command=self.browse_batch_file
        )
        browse_button.grid(row=1, column=2, pady=5)
        
        # 執行按鈕區域
        execute_frame = ttk.Frame(batch_frame)
        execute_frame.grid(row=2, column=0, columnspan=3, pady=15)
        
        # 執行批次檔按鈕
        execute_button = tk.Button(
            execute_frame,
            text="執行批次檔",
            command=self.execute_batch_file,
            font=('Microsoft JhengHei UI', 12, 'bold'),
            width=15,
            height=2,
            bg='#FF9800',
            fg='white',
            relief='groove',
            borderwidth=2,
            highlightthickness=0
        )
        execute_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 按鈕 hover 效果
        execute_button.bind("<Enter>", lambda e: execute_button.config(bg="#F57C00"))
        execute_button.bind("<Leave>", lambda e: execute_button.config(bg="#FF9800"))
        
        # 在新視窗執行按鈕
        execute_new_window_button = tk.Button(
            execute_frame,
            text="在新視窗執行",
            command=self.execute_batch_file_new_window,
            font=('Microsoft JhengHei UI', 12, 'bold'),
            width=15,
            height=2,
            bg='#2196F3',
            fg='white',
            relief='groove',
            borderwidth=2,
            highlightthickness=0
        )
        execute_new_window_button.pack(side=tk.LEFT)
        
        # 按鈕 hover 效果
        execute_new_window_button.bind("<Enter>", lambda e: execute_new_window_button.config(bg="#1976D2"))
        execute_new_window_button.bind("<Leave>", lambda e: execute_new_window_button.config(bg="#2196F3"))
        
        # 狀態顯示區域
        status_frame = ttk.LabelFrame(dos_main_frame, text="執行狀態", padding=10)
        status_frame.grid(row=3, column=0, sticky='ew')
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(
            status_frame,
            text="就緒",
            font=('Microsoft JhengHei UI', 10),
            foreground='#2E8B57'
        )
        self.status_label.grid(row=0, column=0, sticky='w')
    
    def open_dos_window(self):
        """開啟DOS視窗"""
        try:
            # 檢查是否已經開啟 DOS 視窗
            if self.dos_process is None or self.dos_process.poll() is not None:
                # 如果沒有開啟或已關閉，則開啟新的 DOS 視窗
                self.dos_process = subprocess.Popen(["cmd"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                self.update_status("DOS 視窗已開啟", "success")
                print("[DEBUG] 已開啟 DOS 視窗")
            else:
                # 如果已經開啟，則顯示提示訊息
                messagebox.showinfo("提示", "DOS 視窗已經開啟")
                self.update_status("DOS 視窗已經在運行中", "info")
        except Exception as e:
            error_msg = f"開啟DOS視窗時發生錯誤：{str(e)}"
            messagebox.showerror("錯誤", error_msg)
            self.update_status(f"錯誤：{str(e)}", "error")
    
    def browse_batch_file(self):
        """瀏覽批次檔"""
        try:
            file_path = filedialog.askopenfilename(
                title="選擇批次檔",
                filetypes=[
                    ("批次檔", "*.bat;*.cmd"),
                    ("所有檔案", "*.*")
                ],
                initialdir=os.getcwd()
            )
            if file_path:
                self.batch_path_var.set(file_path)
                self.update_status(f"已選擇批次檔：{os.path.basename(file_path)}", "info")
        except Exception as e:
            error_msg = f"瀏覽檔案時發生錯誤：{str(e)}"
            messagebox.showerror("錯誤", error_msg)
            self.update_status(f"錯誤：{str(e)}", "error")
    
    def execute_batch_file(self):
        """執行批次檔（在當前視窗）"""
        batch_path = self.batch_path_var.get().strip()
        if not batch_path:
            messagebox.showwarning("警告", "請先選擇批次檔")
            self.update_status("請先選擇批次檔", "warning")
            return
        
        if not os.path.exists(batch_path):
            messagebox.showerror("錯誤", "批次檔不存在")
            self.update_status("批次檔不存在", "error")
            return
        
        try:
            # 在當前視窗執行批次檔
            result = subprocess.run([batch_path], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                self.update_status("批次檔執行完成", "success")
                messagebox.showinfo("完成", f"批次檔執行完成\n返回碼：{result.returncode}")
            else:
                self.update_status(f"批次檔執行失敗，返回碼：{result.returncode}", "error")
                messagebox.showerror("錯誤", f"批次檔執行失敗\n返回碼：{result.returncode}\n錯誤訊息：{result.stderr}")
        except Exception as e:
            error_msg = f"執行批次檔時發生錯誤：{str(e)}"
            messagebox.showerror("錯誤", error_msg)
            self.update_status(f"錯誤：{str(e)}", "error")
    
    def execute_batch_file_new_window(self):
        """在新視窗執行批次檔"""
        batch_path = self.batch_path_var.get().strip()
        if not batch_path:
            messagebox.showwarning("警告", "請先選擇批次檔")
            self.update_status("請先選擇批次檔", "warning")
            return
        
        if not os.path.exists(batch_path):
            messagebox.showerror("錯誤", "批次檔不存在")
            self.update_status("批次檔不存在", "error")
            return
        
        try:
            # 在新視窗執行批次檔
            subprocess.Popen([batch_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            self.update_status("批次檔已在新視窗中啟動", "success")
            messagebox.showinfo("完成", "批次檔已在新視窗中啟動")
        except Exception as e:
            error_msg = f"執行批次檔時發生錯誤：{str(e)}"
            messagebox.showerror("錯誤", error_msg)
            self.update_status(f"錯誤：{str(e)}", "error")
    
    def update_status(self, message, status_type="info"):
        """更新狀態顯示"""
        color_map = {
            "success": "#2E8B57",
            "error": "#DC143C",
            "warning": "#FF8C00",
            "info": "#4682B4"
        }
        
        self.status_label.config(
            text=message,
            foreground=color_map.get(status_type, "#4682B4")
        )
