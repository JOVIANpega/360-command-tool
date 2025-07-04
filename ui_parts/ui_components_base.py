# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import sys
import json

# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from config_core import list_com_ports, save_setup, GUIDE_FILE, COMMAND_FILE

class UIComponentsBase:
    def __init__(self, parent):
        self.parent = parent
        self.last_size = (0, 0)
        self.led_blinking = False
        self.main_frame = None
        self.radiobutton_frame = None
        self.section_radiobuttons = []
        # 控制下拉列表最大顯示項目數
        self.max_dropdown_items = 20  # 將下拉菜單最大顯示項目數從10改為20
        # 下拉列表字典
        self.dropdown_boxes = {}
        # 獲取高亮關鍵字
        self.highlight_keywords = getattr(parent, 'highlight_keywords', {})
        print(f"[DEBUG] 載入了 {len(self.highlight_keywords)} 個高亮關鍵字到 UIComponents")
        self.init_ui()
        # 讀取 setup.txt 的寬高
        width = int(self.parent.setup.get('Window_Width', 800))
        height = int(self.parent.setup.get('Window_Height', 600))
        # 視窗最大化
        try:
            self.parent.root.state('zoomed')  # Windows
        except Exception:
            self.parent.root.attributes('-zoomed', True)  # Linux
        self.last_size = (width, height)
        self.parent.root.bind('<Configure>', self.on_window_resize)
        # 綁定 Enter 鍵執行指令
        self.parent.root.bind('<Return>', lambda e: self.parent.handlers.on_execute())

    def center_window(self, width, height):
        self.parent.root.update_idletasks()
        screen_width = self.parent.root.winfo_screenwidth()
        screen_height = self.parent.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.parent.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def init_ui(self):
        # 建立主框架
        self.main_frame = ttk.PanedWindow(self.parent.parent, orient='horizontal', style="Main.TFrame")
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        # 配置主框架的 grid
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=2)
        
        # --- 左側控制面板 ---
        # 直接使用 Frame 而非滾動區域，因為我們已經優化佈局使其不需要滾動
        self.left_panel = ttk.LabelFrame(self.main_frame, text='控制面板', padding=5, style="Main.TLabelframe")
        
        # 建立右側面板
        self.right_panel = ttk.LabelFrame(self.main_frame, text='回應內容', padding=5, style="Main.TLabelframe")
        
        # 將左右面板加入 PanedWindow
        self.main_frame.add(self.left_panel, weight=1)
        self.main_frame.add(self.right_panel, weight=2)
        
        # 綁定 PanedWindow 分割位置變更事件
        self.main_frame.bind('<ButtonRelease-1>', self.on_pane_position_changed)
        
        # 初始化各個元件
        # 這些方法將在子類中實現
        
        # 強化 left_panel 內所有 Entry/Combobox 的 <Return> 綁定
        # 這將在子類中完成，因為這些元件尚未創建
        
        # 恢復 PanedWindow 分割位置（延遲執行，確保視窗已完全載入）
        self.parent.root.after(200, self.restore_pane_position)
        
        # 顯示版本信息
        self.parent.root.after(500, lambda: self.show_notification("VALO360 指令通 V1.12 已啟動", "blue", 5000))
        
        # 顯示歡迎訊息
        welcome_message = "歡迎使用 VALO360 指令通！點擊「使用說明」按鈕查看詳細操作指南。"
        self.parent.root.after(6000, lambda: self.show_notification(welcome_message, "green", 8000))
        
        # 顯示系統狀態
        self.parent.root.after(15000, self.show_system_status)
        
        # 顯示基本操作提示
        basic_tips = "基本操作：選擇COM口和指令後點擊「執行指令」按鈕。通知區域可使用 +/- 調整文字大小。"
        self.parent.root.after(25000, lambda: self.show_notification(basic_tips, "blue", 10000))

    def on_window_resize(self, event):
        # 只在主視窗且尺寸真的有變時記錄
        if event.widget == self.parent.root:
            new_size = (self.parent.root.winfo_width(), self.parent.root.winfo_height())
            if new_size != self.last_size and new_size[0] > 100 and new_size[1] > 100:
                self.last_size = new_size
                print(f"[DEBUG] 視窗大小變更為: {new_size}")
                # 更新設定中的視窗大小
                self.parent.setup['Window_Width'] = str(new_size[0])
                self.parent.setup['Window_Height'] = str(new_size[1])

    def on_pane_position_changed(self, event):
        """當分割位置變更時儲存位置"""
        try:
            # 獲取當前分割位置
            sash_position = self.main_frame.sashpos(0)
            
            # 如果位置有效（大於0），則保存到設定
            if sash_position > 0:
                self.parent.setup['Pane_Sash_Position'] = str(sash_position)
                print(f"[DEBUG] 分割位置已更新: {sash_position}")
        except Exception as e:
            print(f"[ERROR] 更新分割位置時發生錯誤: {e}")

    def restore_pane_position(self):
        """恢復上次保存的分割位置"""
        try:
            # 從設定中獲取分割位置
            sash_position = int(self.parent.setup.get('Pane_Sash_Position', '400'))
            
            # 設置分割位置
            self.main_frame.sashpos(0, sash_position)
            print(f"[DEBUG] 已恢復分割位置: {sash_position}")
        except Exception as e:
            print(f"[ERROR] 恢復分割位置時發生錯誤: {e}")

    def show_notification(self, message, color="red", duration=5000, callback=None):
        """在倒數計時標籤顯示通知訊息"""
        try:
            if hasattr(self, 'label_countdown'):
                # 保存原來的顏色
                original_fg = self.label_countdown.cget('fg')
                # 設置新的顏色和訊息
                self.label_countdown.config(fg=color, text=message)
                # 設定計時器，在指定時間後恢復原來的顏色和清空訊息
                self.parent.root.after(duration, lambda: self._restore_after_notification(original_fg, callback))
        except Exception as e:
            print(f"[ERROR] 顯示通知時發生錯誤: {e}")

    def _restore_after_notification(self, original_fg, callback=None):
        """恢復通知標籤的原始狀態"""
        if hasattr(self, 'label_countdown'):
            self.label_countdown.config(fg=original_fg, text='')
        if callback:
            callback()

    def show_system_status(self):
        """顯示系統狀態通知"""
        try:
            import platform
            import psutil
            
            # 獲取系統信息
            system_info = platform.system() + " " + platform.version()
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            
            # 顯示系統狀態通知
            status_message = f"系統狀態: {system_info}\nCPU: {cpu_usage}%, 記憶體: {memory_usage}%"
            self.show_notification(status_message, "blue", 8000)
        except Exception as e:
            print(f"[ERROR] 獲取系統狀態時發生錯誤: {e}")
            # 顯示簡化版本的狀態通知
            self.show_notification("系統已就緒", "blue", 5000) 