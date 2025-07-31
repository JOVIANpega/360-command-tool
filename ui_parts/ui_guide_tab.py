# -*- coding: utf-8 -*-
"""
使用說明標籤頁模組
提供嵌入式HTML顯示功能
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import webbrowser
import subprocess
import re

class GuideTab:
    """使用說明標籤頁類"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.guide_text = None
        self.dos_process = None
        self.init_guide_tab()
    
    def init_guide_tab(self):
        """初始化使用說明分頁 - 簡化版本，只保留開啟外部網頁功能"""
        self.parent_frame.grid_rowconfigure(0, weight=1)
        self.parent_frame.grid_columnconfigure(0, weight=1)

        # 創建主框架
        guide_main_frame = ttk.Frame(self.parent_frame)
        guide_main_frame.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        guide_main_frame.grid_rowconfigure(1, weight=1)
        guide_main_frame.grid_columnconfigure(0, weight=1)

        # 獲取版本號
        try:
            from config_utils import get_app_version
            app_version = get_app_version()
        except:
            app_version = "1.7.1"

        # 標題
        title_label = ttk.Label(
            guide_main_frame,
            text=f"指令通 V{app_version} 使用說明",
            font=('Microsoft JhengHei UI', 18, 'bold'),
            style="TLabel"
        )
        title_label.grid(row=0, column=0, pady=(0, 30))

        # 說明文字
        desc_label = ttk.Label(
            guide_main_frame,
            text="點擊下方按鈕開啟詳細的使用說明文件",
            font=('Microsoft JhengHei UI', 14),
            style="TLabel"
        )
        desc_label.grid(row=1, column=0, pady=(0, 30))

        # 按鈕區域
        button_frame = ttk.Frame(guide_main_frame)
        button_frame.grid(row=2, column=0, pady=20)

        # 開啟使用說明按鈕
        guide_button = tk.Button(
            button_frame,
            text="開啟使用說明",
            command=self.open_external_guide,
            font=('Microsoft JhengHei UI', 16, 'bold'),
            width=20,
            height=3,
            bg='#cccccc',
            fg='black',
            relief='groove',
            borderwidth=2,
            highlightthickness=0
        )
        guide_button.pack(pady=10)

        # 按鈕 hover 效果
        guide_button.bind("<Enter>", lambda e: guide_button.config(bg="#4caf50", fg="white"))
        guide_button.bind("<Leave>", lambda e: guide_button.config(bg="#cccccc", fg="black"))
    

    
    def open_external_guide(self):
        """開啟外部HTML檔案"""
        try:
            # 獲取檔案路徑
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
            else:
                exe_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            guide_file = os.path.join(exe_dir, "VALO360 指令通使用指南.html")
            
            if os.path.exists(guide_file):
                # 使用預設瀏覽器開啟
                webbrowser.open(f"file:///{guide_file.replace(os.sep, '/')}")
            else:
                messagebox.showinfo("提示", "外部HTML檔案不存在，請查看上方的內嵌說明內容。")
        except Exception as e:
            messagebox.showerror("錯誤", f"開啟使用指南時發生錯誤：\n{str(e)}")
    

