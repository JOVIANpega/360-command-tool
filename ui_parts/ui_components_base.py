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


        # 直接使用 Frame 而非滾動區域，因為我們已經優化佈局使其不需要滾動


        self.left_panel = ttk.LabelFrame(self.main_frame, text='控制面板', padding=5, style="Main.TLabelframe")





        # 建立右側面板


        self.right_panel = ttk.LabelFrame(self.main_frame, text='回應內容', padding=5, style="Main.TLabelframe")





        # 將左右面板加入 PanedWindow


        self.main_frame.add(self.left_panel, weight=1)


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
            # 防止在程式啟動階段觸發保存
            if not hasattr(self, '_startup_complete') or not self._startup_complete:
                return

            # 獲取當前分割位置
            sash_position = self.main_frame.sashpos(0)

            # 如果位置有效（大於0），則保存到設定
            if sash_position > 0:
                # 更新內存中的設定（同時更新兩個位置）
                self.parent.setup['Pane_Sash_Position'] = str(sash_position)
                if 'DUT_Control' not in self.parent.setup:
                    self.parent.setup['DUT_Control'] = {}
                self.parent.setup['DUT_Control']['Pane_Sash_Position'] = str(sash_position)
                print(f"[DEBUG] 分割位置已更新: {sash_position}")

                # 延遲保存，避免頻繁寫入
                if hasattr(self, '_save_timer'):
                    self.parent.root.after_cancel(self._save_timer)
                self._save_timer = self.parent.root.after(1000, self._delayed_save_pane_position, sash_position)
        except Exception as e:
            print(f"[ERROR] 更新分割位置時發生錯誤: {e}")

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
        """恢復上次保存的分割位置"""
        try:
            # 從設定中獲取分割位置（優先從 DUT_Control 中獲取）
            dut_control = self.parent.setup.get('DUT_Control', {})
            sash_position = dut_control.get('Pane_Sash_Position')

            # 如果 DUT_Control 中沒有，則從頂層獲取
            if not sash_position:
                sash_position = self.parent.setup.get('Pane_Sash_Position', '400')

            # 確保是整數
            if sash_position and sash_position.isdigit():
                sash_position = int(sash_position)

                # 獲取當前窗口寬度
                window_width = self.parent.root.winfo_width()

                # 確保分割位置在合理範圍內 (10% ~ 90% 窗口寬度)
                min_pos = int(window_width * 0.1)
                max_pos = int(window_width * 0.9)

                if sash_position < min_pos:
                    sash_position = min_pos
                elif sash_position > max_pos:
                    sash_position = max_pos

                # 設置分割位置
                self.main_frame.update_idletasks()  # 確保UI元素已經完成佈局
                self.main_frame.sashpos(0, sash_position)
                print(f"[DEBUG] 已恢復分割位置: {sash_position}, 窗口寬度: {window_width}")

                # 再次確認分割位置是否設置成功
                actual_pos = self.main_frame.sashpos(0)
                if actual_pos != sash_position:
                    print(f"[WARNING] 分割位置設置不成功，嘗試再次設置。預期: {sash_position}, 實際: {actual_pos}")
                    # 延遲500毫秒後再次嘗試設置
                    self.parent.root.after(500, lambda: self.main_frame.sashpos(0, sash_position))
            else:
                print(f"[DEBUG] 無效的分割位置值: {sash_position}，使用預設值")
                # 使用預設值 (窗口寬度的40%)
                window_width = self.parent.root.winfo_width()
                default_pos = int(window_width * 0.4)
                self.main_frame.sashpos(0, default_pos)

        except Exception as e:
            print(f"[ERROR] 恢復分割位置時發生錯誤: {e}")
            import traceback
            traceback.print_exc()





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