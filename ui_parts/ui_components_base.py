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





import platform


import re


import threading


import time


from datetime import datetime


import psutil


# 導入通知訊息系統


from config_utils import get_notification_text, get_app_version





class UIComponentsBase:


    def __init__(self, parent):


        self.parent = parent


        self.last_size = (0, 0)


        self.led_blinking = False


        self.main_frame = None


        self.radiobutton_frame = None


        self.section_radiobuttons = []


        # 控制下拉列表最大顯示項目數


        self.max_dropdown_items = 15  # 設定下拉菜單最大顯示項目數為15


        # 下拉列表字典


        self.dropdown_boxes = {}


        # 左側面板行數追蹤


        self.current_left_row = 0


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
        # 創建一個可滾動的左側面板容器
        left_container = ttk.Frame(self.main_frame)
        
        # 創建 Canvas 和滾動條
        self.left_canvas = tk.Canvas(left_container, highlightthickness=0)
        self.left_scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=self.left_canvas.yview)
        
        # 創建實際的左側面板（放在 Canvas 內）
        self.left_panel = ttk.LabelFrame(self.left_canvas, text='控制面板', padding=5, style="Main.TLabelframe")
        
        # 配置滾動
        self.left_canvas.configure(yscrollcommand=self.left_scrollbar.set)
        
        # 將左側面板放入 Canvas
        self.left_canvas.create_window((0, 0), window=self.left_panel, anchor="nw")
        
        # 綁定滾動事件
        self.left_panel.bind("<Configure>", self.on_left_panel_configure)
        self.left_canvas.bind("<Configure>", self.on_left_canvas_configure)
        
        # 綁定滑鼠滾輪事件
        self.left_canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.left_canvas.bind("<Button-4>", self.on_mousewheel)
        self.left_canvas.bind("<Button-5>", self.on_mousewheel)
        
        # 配置滾動區域的 grid
        left_container.grid_rowconfigure(0, weight=1)
        left_container.grid_columnconfigure(0, weight=1)
        self.left_canvas.grid(row=0, column=0, sticky="nsew")
        self.left_scrollbar.grid(row=0, column=1, sticky="ns")





        # 建立右側面板


        self.right_panel = ttk.LabelFrame(self.main_frame, text='回應內容', padding=5, style="Main.TLabelframe")





        # 將左右面板加入 PanedWindow


        self.main_frame.add(left_container, weight=1)


        self.main_frame.add(self.right_panel, weight=2)





        # 綁定分割位置變更事件


        self.main_frame.bind("<ButtonRelease-1>", self.on_pane_position_changed)





        # 在UI完全加載後恢復分割位置


        self.parent.root.after(100, self.restore_pane_position)





        # 初始化各個元件


        # 這些方法將在子類中實現





        # 強化 left_panel 內所有 Entry/Combobox 的 <Return> 綁定


        # 這將在子類中完成，因為這些元件尚未創建





        # 恢復 PanedWindow 分割位置（延遲執行，確保視窗已完全載入）


        self.parent.root.after(200, self.restore_pane_position)





        # 顯示版本信息


        app_version = get_app_version()
        self.parent.root.after(500, lambda: self.show_notification(get_notification_text("app_started"), "blue", 5000))
        
        # 在元件初始化完成後更新滾動狀態
        self.parent.root.after(500, self.update_left_panel_scroll)





        # 顯示歡迎訊息


        welcome_message = "歡迎使用指令通！點擊「使用說明」按鈕查看詳細操作指南。"


        self.parent.root.after(6000, lambda: self.show_notification(welcome_message, "green", 8000))





        # 顯示系統狀態


        self.parent.root.after(15000, self.show_system_status)





        # 顯示基本操作提示


        basic_tips = "基本操作：選擇COM口和指令後點擊「執行指令」按鈕。通知區域可使用 +/- 調整文字大小。"


        self.parent.root.after(25000, lambda: self.show_notification(basic_tips, "blue", 10000))

        # 標記啟動完成，允許保存事件
        self.parent.root.after(30000, self._mark_startup_complete)





    def on_pane_position_changed(self, event):
        """當 PanedWindow 分割位置變更時的處理"""
        try:
            if hasattr(self, 'main_frame') and self.main_frame:
                # 獲取新的分割位置
                sash_position = self.main_frame.sashpos(0)
                
                # 延遲保存，避免頻繁寫入
                if hasattr(self, '_pane_timer'):
                    self.parent.root.after_cancel(self._pane_timer)
                self._pane_timer = self.parent.root.after(1000, self._delayed_save_pane_position, sash_position)
                
                print(f"[DEBUG] 分割位置已變更: {sash_position}")
                
        except Exception as e:
            print(f"[ERROR] 處理分割位置變更時發生錯誤: {e}")

    def on_window_resize(self, event):
        """當視窗大小變更時的處理"""
        try:
            # 只在主視窗且尺寸真的有變時記錄
            if event.widget == self.parent.root:
                w, h = event.width, event.height
                if (w, h) != self.last_size and w > 200 and h > 200:
                    self.last_size = (w, h)
                    
                    # 更新當前設定
                    if 'DUT_Control' not in self.parent.setup:
                        self.parent.setup['DUT_Control'] = {}
                    self.parent.setup['DUT_Control']['Window_Width'] = str(w)
                    self.parent.setup['DUT_Control']['Window_Height'] = str(h)
                    
                    # 延遲保存，避免頻繁寫入
                    if hasattr(self, '_resize_timer'):
                        self.parent.root.after_cancel(self._resize_timer)
                    self._resize_timer = self.parent.root.after(2000, self._delayed_save_window_size, w, h)
                    
                    # 更新左側面板滾動狀態
                    self.parent.root.after(100, self.update_left_panel_scroll)
                    
        except Exception as e:
            print(f"[ERROR] 處理視窗大小變更時發生錯誤: {e}")

    def on_left_panel_configure(self, event):
        """當左側面板大小變更時，更新 Canvas 的滾動區域"""
        try:
            # 更新 Canvas 的滾動區域
            self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
        except Exception as e:
            print(f"[DEBUG] 更新左側面板滾動區域時發生錯誤: {e}")

    def on_left_canvas_configure(self, event):
        """當 Canvas 大小變更時，調整內部面板的寬度"""
        try:
            # 調整內部面板的寬度以匹配 Canvas
            canvas_width = event.width
            self.left_canvas.itemconfig(self.left_canvas.find_withtag("all")[0], width=canvas_width)
        except Exception as e:
            print(f"[DEBUG] 調整左側面板寬度時發生錯誤: {e}")

    def on_mousewheel(self, event):
        """處理滑鼠滾輪事件"""
        try:
            if platform.system() == "Windows":
                # Windows 使用 delta
                delta = event.delta
            else:
                # Linux 使用 num
                if event.num == 4:
                    delta = 120
                elif event.num == 5:
                    delta = -120
                else:
                    delta = 0
            
            # 滾動 Canvas
            self.left_canvas.yview_scroll(int(-1 * (delta / 120)), "units")
        except Exception as e:
            print(f"[DEBUG] 處理滑鼠滾輪事件時發生錯誤: {e}")

    def update_left_panel_scroll(self):
        """更新左側面板的滾動狀態"""
        try:
            # 檢查是否需要滾動條
            panel_height = self.left_panel.winfo_reqheight()
            canvas_height = self.left_canvas.winfo_height()
            
            if panel_height > canvas_height:
                # 需要滾動條
                self.left_scrollbar.grid()
                # 更新滾動區域
                self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
            else:
                # 不需要滾動條
                self.left_scrollbar.grid_remove()
                
        except Exception as e:
            print(f"[DEBUG] 更新左側面板滾動狀態時發生錯誤: {e}")

    def scroll_to_top(self):
        """滾動到頂部"""
        try:
            self.left_canvas.yview_moveto(0)
        except Exception as e:
            print(f"[DEBUG] 滾動到頂部時發生錯誤: {e}")

    def scroll_to_bottom(self):
        """滾動到底部"""
        try:
            self.left_canvas.yview_moveto(1)
        except Exception as e:
            print(f"[DEBUG] 滾動到底部時發生錯誤: {e}")

    def scroll_to_widget(self, widget):
        """滾動到指定元件"""
        try:
            # 獲取元件在 Canvas 中的位置
            bbox = self.left_canvas.bbox(widget)
            if bbox:
                # 計算元件應該在視窗中的位置
                widget_y = bbox[1]
                canvas_height = self.left_canvas.winfo_height()
                
                # 滾動到元件位置
                self.left_canvas.yview_moveto(widget_y / self.left_panel.winfo_reqheight())
        except Exception as e:
            print(f"[DEBUG] 滾動到指定元件時發生錯誤: {e}")

    def _delayed_save_pane_position(self, sash_position):
        """延遲保存分割位置"""
        try:
            from config_core import load_setup, save_setup
            full_setup = load_setup()
            if 'DUT_Control' not in full_setup:
                full_setup['DUT_Control'] = {}
            full_setup['DUT_Control']['Pane_Sash_Position'] = str(sash_position)
            save_setup(full_setup, manual_save=True)  # 使用手動保存
            print(f"[DEBUG] 分割位置已保存到設定檔: {sash_position}")
        except Exception as e:
            print(f"[ERROR] 保存分割位置到設定檔時發生錯誤: {e}")
    def _mark_startup_complete(self):
        """標記啟動完成"""
        self._startup_complete = True
        print("[DEBUG] 程式啟動完成，啟用配置保存功能")





    def restore_pane_position(self):
        """恢復 PanedWindow 分割位置"""
        try:
            # 獲取保存的分割位置
            sash_position = self.parent.setup.get('DUT_Control', {}).get('Pane_Sash_Position', 633)
            
            # 確保 sash_position 是有效的數字
            try:
                sash_position = int(sash_position)
                if sash_position < 100:  # 最小值檢查
                    sash_position = 633
            except (ValueError, TypeError):
                sash_position = 633
            
            # 設定分割位置
            if hasattr(self, 'main_frame') and self.main_frame:
                self.main_frame.sashpos(0, sash_position)
                print(f"[DEBUG] 已恢復分割位置: {sash_position}")
                
                # 更新左側面板滾動狀態
                self.parent.root.after(100, self.update_left_panel_scroll)
                
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
        """顯示系統狀態（COM口、超時設定、分類）"""
        try:
            if hasattr(self, 'label_countdown') and hasattr(self.parent, 'setup'):
                # 獲取COM口設定
                com_port = self.parent.setup.get('Serial_COM_Port', 'N/A')

                # 獲取當前選中的分類及該分類下的指令數量
                section = "全部指令"
                cmd_count = 0

                if hasattr(self, 'section_var') and hasattr(self, 'sections'):
                    section = self.section_var.get()

                # 獲取指令數量
                if hasattr(self.parent, 'handlers') and hasattr(self.parent.handlers, 'commands'):
                    cmd_count = len(self.parent.handlers.commands.get(section, {}))

                # 獲取超時設定
                timeout = self.parent.setup.get('Command_Timeout_Seconds', '30')

                # 構建狀態訊息
                status_message = get_notification_text("system_status", com_port, section, cmd_count, timeout)

                # 顯示狀態訊息
                self.show_notification(status_message, "blue", 10000)
        except Exception as e:
            print(f"[ERROR] 顯示系統狀態時發生錯誤: {e}")
            import traceback
            traceback.print_exc()