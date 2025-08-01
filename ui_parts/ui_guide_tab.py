# -*- coding: utf-8 -*-
"""
使用說明標籤頁模組 - 簡化版本
"""
import tkinter as tk
from tkinter import ttk

class GuideTab:
    """使用說明標籤頁類 - 簡化版本"""

    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.init_guide_tab()

    def init_guide_tab(self):
        """初始化使用說明分頁 - 簡化版本，提示使用者點擊按鈕開啟外部說明"""
        self.parent_frame.grid_rowconfigure(0, weight=1)
        self.parent_frame.grid_columnconfigure(0, weight=1)

        # 創建主框架
        guide_main_frame = ttk.Frame(self.parent_frame)
        guide_main_frame.grid(row=0, column=0, sticky='nsew', padx=50, pady=50)
        guide_main_frame.grid_rowconfigure(1, weight=1)
        guide_main_frame.grid_columnconfigure(0, weight=1)

        # 標題
        title_label = ttk.Label(
            guide_main_frame,
            text="VALO360 指令通使用說明",
            font=('Microsoft JhengHei UI', 20, 'bold'),
            style="TLabel"
        )
        title_label.grid(row=0, column=0, pady=(0, 40))

        # 說明文字
        desc_label = ttk.Label(
            guide_main_frame,
            text="請點擊 DUT 控制分頁中的「使用說明」按鈕\n開啟詳細的使用說明文件",
            font=('Microsoft JhengHei UI', 16),
            style="TLabel",
            justify='center'
        )
        desc_label.grid(row=1, column=0, pady=(0, 40))

        # 提示文字
        tip_label = ttk.Label(
            guide_main_frame,
            text="💡 提示：使用說明按鈕位於 DUT 控制分頁的底部按鈕區",
            font=('Microsoft JhengHei UI', 12),
            style="TLabel",
            foreground='#666666'
        )
        tip_label.grid(row=2, column=0)

