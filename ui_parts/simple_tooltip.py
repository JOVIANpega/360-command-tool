# -*- coding: utf-8 -*-
"""
超級簡單的 Tooltip 系統
不依賴任何外部配置，直接內建所有 tooltip 文字
"""

import tkinter as tk
from tkinter import ttk

class SimpleToolTip:
    """超級簡單的 tooltip 類別"""
    
    def __init__(self, widget, text='', delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.id = None
        self.tw = None
        
        # 綁定事件
        self.widget.bind("<Enter>", self.on_enter, add=True)
        self.widget.bind("<Leave>", self.on_leave, add=True)
        self.widget.bind("<ButtonPress>", self.on_leave, add=True)

    def on_enter(self, event=None):
        """滑鼠進入元件"""
        if not self.text:
            return
        self.schedule_tooltip()

    def on_leave(self, event=None):
        """滑鼠離開元件"""
        self.cancel_tooltip()
        self.hide_tooltip()

    def schedule_tooltip(self):
        """安排顯示 tooltip"""
        self.cancel_tooltip()
        self.id = self.widget.after(self.delay, self.show_tooltip)

    def cancel_tooltip(self):
        """取消 tooltip 顯示"""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show_tooltip(self):
        """顯示 tooltip"""
        if self.tw or not self.text:
            return

        # 獲取元件的螢幕座標
        try:
            x = self.widget.winfo_rootx()
            y = self.widget.winfo_rooty()
            w = self.widget.winfo_width()
            h = self.widget.winfo_height()
        except tk.TclError:
            return

        # 創建 tooltip 視窗
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_attributes("-topmost", True)

        # 創建標籤
        label = tk.Label(self.tw, 
                        text=self.text, 
                        justify='left',
                        background="#ffffe0",
                        foreground="#000000",
                        relief='solid',
                        borderwidth=1,
                        wraplength=250,
                        font=('Tahoma', 9))
        label.pack()

        # 計算位置
        tooltip_width = label.winfo_reqwidth() + 10
        tooltip_height = label.winfo_reqheight() + 10
        
        # 預設顯示在元件下方
        tooltip_x = x + (w - tooltip_width) // 2
        tooltip_y = y + h + 5
        
        # 檢查是否超出螢幕邊界
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()
        
        if tooltip_x + tooltip_width > screen_width:
            tooltip_x = screen_width - tooltip_width - 5
        if tooltip_y + tooltip_height > screen_height:
            tooltip_y = y - tooltip_height - 5
        if tooltip_x < 0:
            tooltip_x = 5
        if tooltip_y < 0:
            tooltip_y = 5

        self.tw.geometry(f"{tooltip_width}x{tooltip_height}+{tooltip_x}+{tooltip_y}")

    def hide_tooltip(self):
        """隱藏 tooltip"""
        if self.tw:
            try:
                self.tw.destroy()
            except tk.TclError:
                pass
            finally:
                self.tw = None

class SimpleToolTipManager:
    """超級簡單的 tooltip 管理器"""
    
    def __init__(self):
        self.tooltips = {}
        self.enabled = True
        
        # 內建所有 tooltip 文字
        self.tooltip_texts = {
            # DUT 控制標籤頁
            'btn_refresh': '重新掃描可用的COM通訊埠',
            'btn_execute': '執行目前選擇的指令',
            'btn_ping': '測試網路連線狀態',
            'btn_save_ip': '將目前位址加入常用清單',
            'btn_delete_ip': '從常用清單中移除目前位址',
            'btn_clear_ip': '清空所有常用位址記錄',
            'btn_ip_plus': 'IP地址最後一段數字+1（範圍0-255）',
            'btn_ip_minus': 'IP地址最後一段數字-1（範圍0-255）',
            'btn_clear': '清空回應內容',
            'btn_backup': '將回應內容儲存為檔案',
            'btn_guide': '顯示使用說明',
            'btn_ui_font_plus': '放大介面文字大小',
            'btn_ui_font_minus': '縮小介面文字大小',
            'btn_content_font_plus': '放大內容文字大小',
            'btn_content_font_minus': '縮小內容文字大小',
            'btn_remove_end': '移除目前選擇的結束字串',
            'btn_open_cmd_table': '開啟指令檔案編輯器',
            
            # 治具控制標籤頁
            'btn_fixture_execute': '執行治具控制指令',
            'btn_fixture_clear': '清空治具控制回應內容',
            
            # 手動輸入標籤頁
            'btn_manual_execute': '執行手動輸入的指令',
            'btn_manual_clear': '清空手動輸入回應內容',
            
            # DOS標籤頁
            'btn_open_cmd': '開啟命令提示字元',
            'btn_open_powershell': '開啟PowerShell',
            'btn_browse_batch': '瀏覽批次檔',
            'btn_execute_batch': '執行批次檔',
            
            # 設定標籤頁 (Settings)
            'btn_manual_save': '將目前所有修改過的設定值立即儲存到 setup.json 檔案中。',
            'btn_browse_file': '開啟檔案選取對話框，選取新的指令 TXT 檔案（選取後會自動儲存並即時更新指令清單）。',
            'entry_window_title': '設定應用程式視窗最上方顯示的標題名稱（最多 50 個字元）。',
            'entry_window_width': '設定應用程式啟動時的預設視窗寬度（像素）。',
            'entry_window_height': '設定應用程式啟動時的預設視窗高度（像素）。',
            'entry_version': '顯示或修改目前的應用程式版本號碼資訊。',
            'entry_ssh_host': '設定 SSH 連線的遠端主機 IP 位址。',
            'entry_ssh_port': '設定 SSH 連線使用的通訊埠（預設為 22）。',
            'entry_ssh_account': '設定 SSH 登入使用的預設帳號與密碼，格式通常為 account/password。',
            'entry_ssh_timeout': '設定 SSH 連線時的超時等待時間（秒）。',
            'combobox_separator': '選擇多重指令之間的分隔符號，用於在指令檔中區分不同的連續指令。',
            'entry_custom_separator': '在此輸入自訂的指令分隔符號，點擊旁邊的 [+] 號可加入下拉清單。',
            'entry_single_timeout': '設定「單個指令」送出後，程式等待設備回傳回應的最長時間（秒）。若超過此時間未收到回應則視為超時。',
            'entry_command_interval': '設定「連續多個指令」執行時，每個指令之間的停頓間隔時間（秒）。',
            'entry_tab_name': '設定此分頁標籤在主畫面標籤列上顯示的自訂名稱。',
            'entry_manual_hint': '設定「手動輸入指令」頁面輸入框內的預設提示文字內容。',
            'entry_device_label': '設定顯示在 DUT 控制頁面「清空回應」按鈕下方的設備資訊文字（如型號與帳密資訊）。',
            'entry_startup_label': '設定顯示在主畫面左上角綠色區塊內的標題文字，用於區分不同的測試專案。',
            'combobox_transport': '選擇指令的傳輸通訊方式（Console、SSH 或 ADB）。',
            'checkbox_tooltip': '啟用或禁用介面按鈕的滑鼠懸停提示功能。',
            'checkbox_auto_execute': '程式啟動時自動執行指令',
            
            # 通用組件
            'combobox_com': '選擇要連接的設備通訊埠',
            'combobox_cmd': '選擇要執行的指令',
            'combobox_end': '選擇指令結束的判斷字串',
            'entry_ip': '輸入或選擇要測試的網路位址',
            'auto_exec_checkbox': '程式啟動時自動執行指令',
            
            # 標籤組件
            'label_com': 'COM通訊埠標籤',
            'label_cmd': '指令選擇標籤',
            'label_ip': 'IP位址標籤',
            'label_end': '結束字串標籤',
            'label_timeout': '超時設定標籤',
            'label_ui_font': '介面字體大小標籤',
            'label_content_font': '內容字體大小標籤',
            
            # 控制組件
            'ui_font_scale': '調整介面字體大小的滑桿',
            'content_font_scale': '調整內容字體大小的滑桿',
            
            # 顯示組件
            'text_output': '指令執行結果顯示區域',
            'progress': '進度條顯示區域',
            
            # 框架組件
            'left_panel': '左側控制面板',
            'right_panel': '右側顯示面板',
            'main_frame': '主要內容框架',
            
            # 編輯器組件
            'section_description': '指令區段描述',
            'editor_text': '指令檔案編輯區域',
            'save_button': '儲存指令檔案',
            'reload_button': '重新載入指令檔案',
            'close_button': '關閉編輯器視窗'
        }
        
        print(f"[DEBUG] SimpleToolTipManager 初始化完成，內建 {len(self.tooltip_texts)} 個 tooltip")
    
    def add_tooltip(self, widget, widget_name):
        """為元件添加 tooltip"""
        if not self.enabled or not widget:
            return
            
        tooltip_text = self.tooltip_texts.get(widget_name, '')
        if not tooltip_text:
            print(f"[DEBUG] 找不到 tooltip 配置: {widget_name}")
            return
            
        try:
            # 移除舊的 tooltip
            widget_id = id(widget)
            if widget_id in self.tooltips:
                self.tooltips[widget_id].hide_tooltip()
                del self.tooltips[widget_id]
            
            # 創建新的 tooltip
            tooltip = SimpleToolTip(widget, tooltip_text)
            self.tooltips[widget_id] = tooltip
            print(f"[DEBUG] 為元件 {widget_name} 添加 tooltip: {tooltip_text[:30]}...")
            
        except Exception as e:
            print(f"[ERROR] 添加 tooltip 失敗 ({widget_name}): {e}")
    
    def add_tooltip_with_text(self, widget, text):
        """直接用文字為元件添加 tooltip"""
        if not widget or not text:
            return
            
        try:
            widget_id = id(widget)
            if widget_id in self.tooltips:
                self.tooltips[widget_id].hide_tooltip()
                del self.tooltips[widget_id]
            
            tooltip = SimpleToolTip(widget, text)
            self.tooltips[widget_id] = tooltip
            print(f"[DEBUG] 為元件添加文字 tooltip: {text[:30]}...")
            
        except Exception as e:
            print(f"[ERROR] 添加文字 tooltip 失敗: {e}")
    
    def set_enabled(self, enabled):
        """設定 tooltip 啟用狀態"""
        self.enabled = enabled
        for tooltip in self.tooltips.values():
            if hasattr(tooltip, 'enabled'):
                tooltip.enabled = enabled

# 創建全域實例
simple_tooltip_manager = SimpleToolTipManager()

def get_simple_tooltip_manager():
    """獲取簡單 tooltip 管理器"""
    return simple_tooltip_manager
