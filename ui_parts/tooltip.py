# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import re
import os

class ToolTip:
    """
    創建一個ToolTip提示框
    """
    def __init__(self, widget, text='widget info', delay=500, wraplen=250, global_notification_manager=None):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplen = wraplen
        self.widget.bind("<Enter>", self.enter, add=True)
        self.widget.bind("<Leave>", self.leave, add=True)
        self.widget.bind("<ButtonPress>", self.leave, add=True)
        self.id = None
        self.tw = None
        self.enabled = True  # 控制是否啟用 ToolTip
        self.global_notification_manager = global_notification_manager  # 全域通知管理器
        
        # Windows 風格設定
        self.bg_color = "#FFFFDD"  # 淡黃色背景，類似 Windows 原生提示
        self.border_color = "#CCCCCC"  # 淺灰色邊框
        self.text_color = "#000000"  # 黑色文字
        self.font = ("Segoe UI", 9)  # Windows 預設字體
        self.padding = 5  # 內部填充
        self.alpha = 0.95  # 透明度 (0.0-1.0)
        self.corner_radius = 2  # 圓角半徑

    def enter(self, event=None):
        if not self.enabled:  # 檢查是否啟用
            return
        # 立即顯示於全域提示欄
        if self.global_notification_manager:
            self.global_notification_manager.show_notification(self.text, "info", 0)  # 0=不自動消失
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()
        # 清除全域通知
        if self.global_notification_manager:
            self.global_notification_manager.clear_notification()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        if not self.enabled:  # 檢查是否啟用
            return
        
        # 獲取元件位置
        x = y = 0
        if hasattr(self.widget, 'winfo_rootx') and hasattr(self.widget, 'winfo_rooty'):
            x = self.widget.winfo_rootx()
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        else:
            # 如果是特殊元件，嘗試其他方法獲取位置
            try:
                x, y, cx, cy = self.widget.bbox("insert")
                x += self.widget.winfo_rootx() + 25
                y += self.widget.winfo_rooty() + 20
            except:
                # 最後的備用方案
                x = self.widget.winfo_pointerx() + 15
                y = self.widget.winfo_pointery() + 15
        
        # 創建提示窗口
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)  # 移除窗口邊框
        self.tw.wm_geometry(f"+{x}+{y}")
        
        # 設置透明度 (如果平台支持)
        try:
            self.tw.attributes("-alpha", self.alpha)
        except:
            pass
        
        # 創建標籤
        label = tk.Label(self.tw, text=self.text, justify='left',
                        background=self.bg_color, foreground=self.text_color,
                        relief='solid', borderwidth=1, 
                        font=self.font,
                        wraplength=self.wraplen,
                        padx=self.padding, pady=self.padding)
        label.pack(ipadx=1)
        
        # 設置淡入效果
        self.fade_in()
        
        # 同時在全域通知區域顯示
        if self.global_notification_manager:
            self.global_notification_manager.show_notification(self.text, "info", 0)  # 不自動消失

    def fade_in(self, alpha=0.1):
        """實現淡入效果"""
        if not self.tw:
            return
            
        try:
            if alpha < self.alpha:
                self.tw.attributes("-alpha", alpha)
                self.tw.after(50, lambda: self.fade_in(alpha + 0.1))
        except:
            # 如果不支持透明度，直接顯示
            pass

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            # 設置淡出效果
            try:
                self.fade_out(tw)
            except:
                tw.destroy()

    def fade_out(self, window, alpha=0.9):
        """實現淡出效果"""
        try:
            if alpha > 0.1:
                window.attributes("-alpha", alpha)
                window.after(50, lambda: self.fade_out(window, alpha - 0.1))
            else:
                window.destroy()
        except:
            # 如果不支持透明度，直接關閉
            window.destroy()

    def set_enabled(self, enabled):
        """設定是否啟用 ToolTip"""
        self.enabled = enabled
        if not enabled and self.tw:
            self.hidetip()


class ToolTipManager:
    """
    管理所有 ToolTip 的啟用/停用狀態
    """
    def __init__(self, global_notification_manager=None):
        self.tooltips = []
        self.enabled = True
        self.global_notification_manager = global_notification_manager
        self.tooltip_config = {}  # 儲存tooltip配置
        self.load_tooltip_config()
        
        # 預設延遲時間 (毫秒)
        self.default_delay = 500

    def load_tooltip_config(self):
        """載入tooltip配置檔案"""
        try:
            config_file = "tooltip_config.txt"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            self.tooltip_config[key.strip()] = value.strip()
                print(f"[DEBUG] 已載入 {len(self.tooltip_config)} 個tooltip配置")
            else:
                print("[WARNING] tooltip_config.txt 檔案不存在，使用預設tooltip")
        except Exception as e:
            print(f"[ERROR] 載入tooltip配置檔案失敗: {e}")

    def get_tooltip_text(self, widget_name):
        """根據元件名稱獲取tooltip文字"""
        # 先從配置檔案中查找
        if widget_name in self.tooltip_config:
            return self.tooltip_config[widget_name]
        
        # 如果沒有找到，使用AI生成
        return AIToolTipGenerator.generate_tooltip_for_widget(
            widget=None,
            widget_name=widget_name,
            widget_type="",
            context=""
        )

    def add_tooltip(self, widget, text=None, delay=None, wraplen=250):
        """添加一個 ToolTip"""
        # 如果沒有提供text，嘗試從配置檔案中獲取
        if text is None:
            # 嘗試從widget的屬性中獲取名稱
            widget_name = getattr(widget, '_name', '')
            if not widget_name:
                # 嘗試從其他屬性推測名稱
                widget_name = self._guess_widget_name(widget)
            
            if widget_name:
                text = self.get_tooltip_text(widget_name)
            else:
                text = "UI 元件說明"
        
        # 如果沒有指定延遲時間，使用預設值
        if delay is None:
            delay = self.default_delay
            
        tooltip = ToolTip(widget, text, delay, wraplen, self.global_notification_manager)
        tooltip.set_enabled(self.enabled)
        self.tooltips.append(tooltip)
        return tooltip

    def _guess_widget_name(self, widget):
        """嘗試推測widget的名稱"""
        try:
            # 嘗試從widget的屬性中獲取名稱
            if hasattr(widget, 'cget'):
                try:
                    text = widget.cget('text')
                    if text:
                        # 根據text內容推測名稱
                        text_lower = text.lower()
                        if '刷新' in text or 'refresh' in text_lower:
                            return 'btn_refresh'
                        elif '執行' in text or 'execute' in text_lower:
                            return 'btn_execute'
                        elif '清空' in text or 'clear' in text_lower:
                            return 'btn_clear'
                        elif '備份' in text or 'backup' in text_lower:
                            return 'btn_backup'
                        elif '說明' in text or 'guide' in text_lower:
                            return 'btn_guide'
                        elif 'ping' in text_lower:
                            return 'btn_ping'
                        elif '儲存' in text or 'save' in text_lower:
                            return 'btn_save_ip'
                        elif '刪除' in text or 'delete' in text_lower:
                            return 'btn_delete_ip'
                        elif 'COM' in text:
                            return 'combobox_com'
                        elif '指令' in text:
                            return 'combobox_cmd'
                        elif 'IP' in text:
                            return 'entry_ip'
                        elif '超時' in text or 'timeout' in text_lower:
                            return 'entry_timeout'
                        elif '結束' in text or 'end' in text_lower:
                            return 'combobox_end'
                except:
                    pass
        except:
            pass
        return ""

    def set_all_enabled(self, enabled):
        """設定所有 ToolTip 的啟用狀態"""
        self.enabled = enabled
        for tooltip in self.tooltips:
            tooltip.set_enabled(enabled)

    def remove_tooltip(self, tooltip):
        """移除一個 ToolTip"""
        if tooltip in self.tooltips:
            self.tooltips.remove(tooltip)


class AIToolTipGenerator:
    """
    AI 自動生成 ToolTip 內容的類別
    """
    
    @staticmethod
    def generate_tooltip_for_widget(widget, widget_name="", widget_type="", context=""):
        """
        根據元件類型和名稱自動生成 tooltip 內容
        
        Args:
            widget: 元件物件
            widget_name: 元件名稱
            widget_type: 元件類型
            context: 上下文資訊
        
        Returns:
            str: 生成的 tooltip 文字
        """
        
        # 根據元件類型生成不同的 tooltip
        if isinstance(widget, ttk.Combobox):
            return AIToolTipGenerator._generate_combobox_tooltip(widget_name, context)
        elif isinstance(widget, tk.Button):
            return AIToolTipGenerator._generate_button_tooltip(widget_name, context)
        elif isinstance(widget, tk.Entry):
            return AIToolTipGenerator._generate_entry_tooltip(widget_name, context)
        elif isinstance(widget, tk.Label):
            return AIToolTipGenerator._generate_label_tooltip(widget_name, context)
        elif isinstance(widget, tk.Checkbutton):
            return AIToolTipGenerator._generate_checkbutton_tooltip(widget_name, context)
        elif isinstance(widget, tk.Radiobutton):
            return AIToolTipGenerator._generate_radiobutton_tooltip(widget_name, context)
        elif isinstance(widget, tk.Canvas):
            return AIToolTipGenerator._generate_canvas_tooltip(widget_name, context)
        elif isinstance(widget, ttk.Progressbar):
            return AIToolTipGenerator._generate_progressbar_tooltip(widget_name, context)
        elif isinstance(widget, tk.Text) or isinstance(widget, tk.scrolledtext.ScrolledText):
            return AIToolTipGenerator._generate_text_tooltip(widget_name, context)
        elif isinstance(widget, ttk.Scale):
            return AIToolTipGenerator._generate_scale_tooltip(widget_name, context)
        else:
            return AIToolTipGenerator._generate_generic_tooltip(widget_name, context)
    
    @staticmethod
    def _generate_combobox_tooltip(widget_name, context):
        """為 Combobox 生成 tooltip"""
        name_lower = widget_name.lower()
        
        if 'com' in name_lower:
            return "選擇要連接的 COM 通訊埠\n點擊下拉選單查看可用的串列埠"
        elif 'cmd' in name_lower or 'command' in name_lower:
            return "選擇要執行的指令\n從下拉選單中選擇預設的指令"
        elif 'end' in name_lower:
            return "選擇指令結束字串\n用於判斷指令執行完成"
        elif 'ip' in name_lower:
            return "選擇要測試的 IP 地址\n顯示之前使用過的 IP 記錄"
        elif 'section' in name_lower or 'category' in name_lower:
            return "選擇指令分類\n按功能分類組織指令"
        else:
            return f"選擇 {widget_name}\n從下拉選單中選擇選項"
    
    @staticmethod
    def _generate_button_tooltip(widget_name, context):
        """為 Button 生成 tooltip"""
        name_lower = widget_name.lower()
        text_lower = context.lower() if context else ""
        
        if 'refresh' in name_lower or '刷新' in text_lower:
            return "刷新可用選項列表\n重新掃描系統資源"
        elif 'execute' in name_lower or '執行' in text_lower:
            return "執行目前選擇的指令\n開始與設備通訊"
        elif 'ping' in name_lower:
            return "對指定 IP 進行網路連線測試\n檢查網路通訊狀態"
        elif 'save' in name_lower or '儲存' in text_lower:
            return "儲存目前設定或資料\n將變更寫入設定檔"
        elif 'clear' in name_lower or '清空' in text_lower:
            return "清空顯示內容\n清除所有輸出文字"
        elif 'backup' in name_lower or '備份' in text_lower:
            return "建立資料備份\n將重要資料儲存為檔案"
        elif 'guide' in name_lower or '說明' in text_lower:
            return "顯示使用說明\n查看操作指南"
        elif 'delete' in name_lower or '刪除' in text_lower:
            return "刪除選中的項目\n移除不需要的資料"
        elif 'plus' in name_lower or '+' in text_lower:
            return "增加數值\n向上調整設定"
        elif 'minus' in name_lower or '-' in text_lower:
            return "減少數值\n向下調整設定"
        elif 'remove' in name_lower:
            return "移除選中的項目\n從列表中刪除"
        else:
            return f"執行 {widget_name} 功能\n點擊執行相關操作"
    
    @staticmethod
    def _generate_entry_tooltip(widget_name, context):
        """為 Entry 生成 tooltip"""
        name_lower = widget_name.lower()
        
        if 'ip' in name_lower:
            return "輸入 IP 地址\n格式：192.168.1.1"
        elif 'timeout' in name_lower:
            return "設定超時時間（秒）\n指令執行的最大等待時間"
        elif 'title' in name_lower:
            return "輸入視窗標題\n設定應用程式視窗名稱"
        elif 'font' in name_lower:
            return "輸入字體大小\n設定介面或內容字體"
        elif 'end' in name_lower:
            return "輸入結束字串\n用於判斷指令執行完成"
        else:
            return f"輸入 {widget_name}\n在此欄位中輸入資料"
    
    @staticmethod
    def _generate_label_tooltip(widget_name, context):
        """為 Label 生成 tooltip"""
        name_lower = widget_name.lower()
        
        if 'com' in name_lower:
            return "COM 口選擇標籤\n顯示串列通訊埠設定"
        elif 'cmd' in name_lower or 'command' in name_lower:
            return "指令選擇標籤\n顯示指令執行設定"
        elif 'ip' in name_lower:
            return "IP 地址標籤\n顯示網路測試設定"
        elif 'timeout' in name_lower:
            return "超時設定標籤\n顯示指令執行超時設定"
        elif 'end' in name_lower:
            return "結束字串標籤\n顯示指令結束判斷設定"
        elif 'font' in name_lower:
            return "字體設定標籤\n顯示字體大小設定"
        else:
            return f"{widget_name} 標籤\n顯示相關設定說明"
    
    @staticmethod
    def _generate_checkbutton_tooltip(widget_name, context):
        """為 Checkbutton 生成 tooltip"""
        name_lower = widget_name.lower()
        text_lower = context.lower() if context else ""
        
        if 'auto' in name_lower or '自動' in text_lower:
            return "啟用自動執行功能\n程式啟動時自動執行指令"
        elif 'test' in name_lower:
            return "啟用測試模式\n執行測試相關功能"
        else:
            return f"啟用 {widget_name} 功能\n勾選啟用相關設定"
    
    @staticmethod
    def _generate_radiobutton_tooltip(widget_name, context):
        """為 Radiobutton 生成 tooltip"""
        name_lower = widget_name.lower()
        
        if 'section' in name_lower or 'category' in name_lower:
            return f"切換到 {widget_name} 分類\n顯示該分類下的指令"
        else:
            return f"選擇 {widget_name} 選項\n切換到相關功能"
    
    @staticmethod
    def _generate_canvas_tooltip(widget_name, context):
        """為 Canvas 生成 tooltip"""
        name_lower = widget_name.lower()
        
        if 'status' in name_lower or 'led' in name_lower:
            return "狀態指示燈\n顯示連接狀態（綠色=已連接，紅色=未連接）"
        else:
            return f"{widget_name} 顯示區域\n顯示相關狀態資訊"
    
    @staticmethod
    def _generate_progressbar_tooltip(widget_name, context):
        """為 Progressbar 生成 tooltip"""
        return "執行進度顯示\n顯示指令執行的進度狀態"
    
    @staticmethod
    def _generate_text_tooltip(widget_name, context):
        """為 Text 生成 tooltip"""
        name_lower = widget_name.lower()
        
        if 'output' in name_lower:
            return "指令執行結果顯示區域\n支援右鍵選單操作（複製、全選等）"
        else:
            return f"{widget_name} 文字顯示區域\n顯示相關文字內容"
    
    @staticmethod
    def _generate_scale_tooltip(widget_name, context):
        """為 Scale 生成 tooltip"""
        name_lower = widget_name.lower()
        
        if 'font' in name_lower:
            return "拖動調整字體大小\n即時預覽字體變化"
        else:
            return f"拖動調整 {widget_name}\n即時調整相關設定"
    
    @staticmethod
    def _generate_generic_tooltip(widget_name, context):
        """為其他元件生成通用 tooltip"""
        if widget_name:
            return f"{widget_name} 元件\n用於相關功能操作"
        else:
            return "UI 元件\n用於介面操作"
    
    @staticmethod
    def extract_widget_info(widget):
        """
        從元件中提取資訊用於生成 tooltip
        
        Args:
            widget: 元件物件
        
        Returns:
            dict: 包含元件資訊的字典
        """
        info = {
            'name': '',
            'text': '',
            'type': type(widget).__name__,
            'context': ''
        }
        
        try:
            # 嘗試獲取元件名稱
            if hasattr(widget, 'cget'):
                try:
                    info['text'] = widget.cget('text') or ''
                except:
                    pass
                
                try:
                    info['name'] = widget.cget('name') or ''
                except:
                    pass
            
            # 嘗試從變數名稱推測
            if not info['name'] and hasattr(widget, '_name'):
                info['name'] = widget._name
            
            # 從 text 屬性推測功能
            if info['text']:
                info['context'] = info['text']
            
        except Exception as e:
            print(f"[DEBUG] 提取元件資訊時發生錯誤: {e}")
        
        return info
