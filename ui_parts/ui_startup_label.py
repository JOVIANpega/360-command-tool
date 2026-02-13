"""
UI 啟動標籤組件
負責在 DUT 控制頁面顯示可自訂的啟動標籤
"""

import tkinter as tk
import tkinter.ttk as ttk
import os
import sys

# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from config_core import load_setup, save_setup


class StartupLabelManager:
    """啟動標籤管理器"""
    
    def __init__(self, parent_ui):
        """
        初始化啟動標籤管理器
        
        Args:
            parent_ui: 父級 UI 組件實例
        """
        self.parent_ui = parent_ui
        self.startup_label = None
        self.current_label_text = "TEST"  # 預設值

        # 閃爍功能相關屬性
        self.is_blinking = False
        self.original_bg_color = '#FFFACD'  # 淡黃色
        self.blink_color = '#FF6B6B'  # 閃爍時的紅色
        self.blink_after_id = None

        # 載入設定
        self.load_startup_label_setting()
    
    def load_startup_label_setting(self):
        """從設定檔載入啟動標籤文字"""
        try:
            setup = load_setup()
            self.current_label_text = setup.get("Startup_Label", "TEST")
            print(f"[DEBUG] 載入啟動標籤設定: {self.current_label_text}")
        except Exception as e:
            print(f"[ERROR] 載入啟動標籤設定失敗: {e}")
            self.current_label_text = "TEST"
    
    def create_startup_label(self, parent_frame, row):
        """
        在指定的父框架中創建啟動標籤
        
        Args:
            parent_frame: 父級框架
            row: 要插入的行號
            
        Returns:
            創建的標籤組件
        """
        try:
            # 創建標籤框架
            label_frame = ttk.Frame(parent_frame, style="TFrame")
            label_frame.grid(row=row, column=0, sticky='ew', pady=(30, 5)) # 增加上方間距至 30px
            label_frame.columnconfigure(0, weight=1)
            
            # 創建淡黃底黑字的大標籤
            self.startup_label = tk.Label(
                label_frame,
                text=self.current_label_text,
                font=('Microsoft JhengHei UI', 20, 'bold'),
                bg='#FFFACD',  # 淡黃色背景 (LemonChiffon)
                fg='black',    # 黑色文字
                relief='raised',
                borderwidth=2,
                height=2,
                anchor='center'
            )
            self.startup_label.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
            
            print(f"[DEBUG] 啟動標籤已創建: {self.current_label_text}")
            return self.startup_label
            
        except Exception as e:
            print(f"[ERROR] 創建啟動標籤失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def update_label_text(self, new_text):
        """
        更新標籤文字
        
        Args:
            new_text: 新的標籤文字
        """
        try:
            if new_text is None or new_text.strip() == "":
                new_text = "TEST"
            
            self.current_label_text = new_text.strip()
            
            # 更新 UI 標籤
            if self.startup_label and self.startup_label.winfo_exists():
                self.startup_label.config(text=self.current_label_text)
                print(f"[DEBUG] 啟動標籤文字已更新: {self.current_label_text}")
            
        except Exception as e:
            print(f"[ERROR] 更新啟動標籤文字失敗: {e}")
    
    def save_startup_label_setting(self, new_text):
        """
        保存啟動標籤設定到檔案
        
        Args:
            new_text: 要保存的標籤文字
        """
        try:
            if new_text is None or new_text.strip() == "":
                new_text = "TEST"
            
            # 載入完整設定
            setup = load_setup()
            
            # 更新啟動標籤設定
            setup["Startup_Label"] = new_text.strip()
            
            # 保存設定
            save_setup(setup)
            
            # 更新本地變數
            self.current_label_text = new_text.strip()
            
            # 更新 UI 標籤
            self.update_label_text(self.current_label_text)
            
            print(f"[DEBUG] 啟動標籤設定已保存: {self.current_label_text}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 保存啟動標籤設定失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_current_text(self):
        """
        獲取當前標籤文字
        
        Returns:
            當前的標籤文字
        """
        return self.current_label_text
    
    def hide_label(self):
        """隱藏啟動標籤"""
        try:
            if self.startup_label and self.startup_label.winfo_exists():
                self.startup_label.grid_remove()
                print("[DEBUG] 啟動標籤已隱藏")
        except Exception as e:
            print(f"[ERROR] 隱藏啟動標籤失敗: {e}")
    
    def show_label(self):
        """顯示啟動標籤"""
        try:
            if self.startup_label and self.startup_label.winfo_exists():
                self.startup_label.grid()
                print("[DEBUG] 啟動標籤已顯示")
        except Exception as e:
            print(f"[ERROR] 顯示啟動標籤失敗: {e}")
    
    def update_font_size(self, ui_font_size):
        """
        根據 UI 字體大小更新標籤字體
        
        Args:
            ui_font_size: UI 字體大小
        """
        try:
            if self.startup_label and self.startup_label.winfo_exists():
                # 標籤字體大小為 UI 字體大小的 1.5 倍，但最小為 16，最大為 24
                label_font_size = max(16, min(24, int(ui_font_size * 1.5)))
                new_font = ('Microsoft JhengHei UI', label_font_size, 'bold')
                self.startup_label.config(font=new_font)
                print(f"[DEBUG] 啟動標籤字體大小已更新: {label_font_size}")
        except Exception as e:
            print(f"[ERROR] 更新啟動標籤字體大小失敗: {e}")

    def start_blink(self):
        """開始閃爍啟動標籤"""
        try:
            if self.startup_label and self.startup_label.winfo_exists():
                self.is_blinking = True
                self._blink_cycle()
                print("[DEBUG] 啟動標籤開始閃爍")
        except Exception as e:
            print(f"[ERROR] 啟動標籤閃爍失敗: {e}")

    def stop_blink(self):
        """停止閃爍並恢復原色"""
        try:
            self.is_blinking = False
            if self.blink_after_id:
                # 取消排程的閃爍
                if hasattr(self.startup_label, 'after_cancel'):
                    self.startup_label.after_cancel(self.blink_after_id)
                self.blink_after_id = None

            if self.startup_label and self.startup_label.winfo_exists():
                # 恢復原來的淡黃色
                self.startup_label.config(bg=self.original_bg_color)
                print("[DEBUG] 啟動標籤停止閃爍，恢復原色")
        except Exception as e:
            print(f"[ERROR] 停止啟動標籤閃爍失敗: {e}")

    def _blink_cycle(self):
        """閃爍循環"""
        try:
            if not self.is_blinking or not self.startup_label or not self.startup_label.winfo_exists():
                return

            # 獲取當前背景色
            current_bg = self.startup_label.cget('bg')

            # 切換顏色
            if current_bg == self.original_bg_color:
                next_color = self.blink_color
            else:
                next_color = self.original_bg_color

            # 設置新顏色
            self.startup_label.config(bg=next_color)

            # 排程下一次閃爍（500ms 間隔）
            self.blink_after_id = self.startup_label.after(500, self._blink_cycle)

        except Exception as e:
            print(f"[ERROR] 啟動標籤閃爍循環失敗: {e}")
            self.is_blinking = False
