# -*- coding: utf-8 -*-
"""
Tooltip 系統 - 重構版本
支援所有 tkinter 元件類型的工具提示
"""

import tkinter as tk
from tkinter import ttk
import configparser
import os
import sys

class ToolTip:
    """
    為 tkinter 元件提供工具提示的類別
    支援所有類型的 tkinter 元件
    """
    def __init__(self, widget, text='', delay=500, wraplen=250):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplen = wraplen
        self.id = None
        self.tw = None
        self.enabled = True
        
        # 綁定事件
        self.widget.bind("<Enter>", self.on_enter, add=True)
        self.widget.bind("<Leave>", self.on_leave, add=True)
        self.widget.bind("<Motion>", self.on_motion, add=True)
        self.widget.bind("<ButtonPress>", self.on_leave, add=True)

    def on_enter(self, event=None):
        """滑鼠進入元件"""
        if not self.enabled or not self.text:
            return
        self.schedule_tooltip()

    def on_leave(self, event=None):
        """滑鼠離開元件"""
        self.cancel_tooltip()
        self.hide_tooltip()

    def on_motion(self, event=None):
        """滑鼠移動"""
        if not self.enabled or not self.text:
            return
        # 取消當前的 tooltip 並重新安排
        self.cancel_tooltip()
        if self.tw is None:  # 只有在 tooltip 未顯示時才重新安排
            self.schedule_tooltip()

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
        if self.tw or not self.text or not self.enabled:
            return

        # 獲取元件的螢幕座標
        try:
            x = self.widget.winfo_rootx()
            y = self.widget.winfo_rooty()
            w = self.widget.winfo_width()
            h = self.widget.winfo_height()
        except tk.TclError:
            # 元件可能已被銷毀
            return

        # 創建 tooltip 視窗
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        
        # 設定視窗樣式
        try:
            # 嘗試設定視窗樣式 (Windows)
            self.tw.wm_attributes("-topmost", True)
            if hasattr(self.tw, 'wm_attributes'):
                try:
                    self.tw.wm_attributes("-alpha", 0.9)
                except tk.TclError:
                    pass  # 某些系統可能不支援透明度
        except tk.TclError:
            pass

        # 創建標籤
        label = tk.Label(self.tw, 
                        text=self.text, 
                        justify='left',
                        background="#ffffe0",
                        foreground="#000000",
                        relief='solid', 
                        borderwidth=1,
                        font=("Microsoft JhengHei", "9", "normal"),
                        wraplength=self.wraplen,
                        padx=4,
                        pady=2)
        label.pack()

        # 計算 tooltip 位置
        self.tw.update_idletasks()  # 更新視窗尺寸
        tw_width = self.tw.winfo_reqwidth()
        tw_height = self.tw.winfo_reqheight()
        
        # 在元件下方顯示，如果空間不足則在上方顯示
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()
        
        # 水平位置
        if x + tw_width > screen_width:
            x = screen_width - tw_width - 10
        
        # 垂直位置
        if y + h + tw_height > screen_height:
            # 在元件上方顯示
            y = y - tw_height - 5
        else:
            # 在元件下方顯示
            y = y + h + 5

        self.tw.wm_geometry(f"+{x}+{y}")

    def hide_tooltip(self):
        """隱藏 tooltip"""
        if self.tw:
            try:
                self.tw.destroy()
            except tk.TclError:
                pass
            self.tw = None

    def set_text(self, text):
        """設定 tooltip 文字"""
        self.text = text

    def set_enabled(self, enabled):
        """設定是否啟用"""
        self.enabled = enabled
        if not enabled:
            self.hide_tooltip()

class ToolTipManager:
    """
    工具提示管理器
    負責管理所有的 tooltip，並從配置文件中讀取設定
    """
    
    def __init__(self):
        self.tooltips = {}
        self.tooltip_config = {}
        self.enabled = True
        self.load_tooltip_config()
        print(f"[DEBUG] ToolTipManager 初始化完成，enabled={self.enabled}")
    
    def load_tooltip_config(self):
        """載入 tooltip 配置"""
        try:
            # 獲取配置文件路徑
            if hasattr(sys, '_MEIPASS'):
                # 打包後的環境
                config_path = os.path.join(sys._MEIPASS, 'tooltips.ini')
            else:
                # 開發環境
                config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tooltips.ini')
            
            if not os.path.exists(config_path):
                print(f"[WARNING] 找不到 tooltip 配置文件: {config_path}")
                self.enabled = False
                return
            
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')
            
            if not config.has_section('Tooltips'):
                print("[WARNING] tooltip 配置文件中找不到 [Tooltips] 區段")
                self.enabled = False
                return
                
            self.tooltip_config = dict(config['Tooltips'])
            print(f"[DEBUG] 成功載入 {len(self.tooltip_config)} 個tooltip配置")
            
        except Exception as e:
            print(f"[ERROR] 載入 tooltip 配置時發生錯誤: {e}")
            self.enabled = False
    
    def add_tooltip(self, widget, widget_name):
        """
        為元件添加 tooltip
        widget: 要添加 tooltip 的元件
        widget_name: 在 tooltips.ini 中對應的鍵名
        """
        if not self.enabled or not widget:
            return
            
        tooltip_text = self.tooltip_config.get(widget_name, '')
        if not tooltip_text:
            return
            
        try:
            # 移除舊的 tooltip
            widget_id = id(widget)
            if widget_id in self.tooltips:
                self.tooltips[widget_id].hide_tooltip()
                del self.tooltips[widget_id]
            
            # 創建新的 tooltip
            tooltip = ToolTip(widget, tooltip_text)
            self.tooltips[widget_id] = tooltip
            print(f"[DEBUG] 為元件 {widget_name} 添加 tooltip: {tooltip_text[:30]}...")
            
        except Exception as e:
            print(f"[ERROR] 添加 tooltip 失敗 ({widget_name}): {e}")
    
    def add_tooltip_with_text(self, widget, text):
        """
        直接用文字為元件添加 tooltip
        """
        if not widget or not text:
            return
            
        try:
            widget_id = id(widget)
            if widget_id in self.tooltips:
                self.tooltips[widget_id].hide_tooltip()
                del self.tooltips[widget_id]
            
            tooltip = ToolTip(widget, text)
            self.tooltips[widget_id] = tooltip
            
        except Exception as e:
            print(f"[ERROR] 添加文字 tooltip 失敗: {e}")
    
    def remove_tooltip(self, widget):
        """移除元件的 tooltip"""
        widget_id = id(widget)
        if widget_id in self.tooltips:
            self.tooltips[widget_id].hide_tooltip()
            del self.tooltips[widget_id]
    
    def set_all_enabled(self, enabled):
        """設定所有 tooltip 的啟用狀態"""
        self.enabled = enabled
        for tooltip in self.tooltips.values():
            tooltip.set_enabled(enabled)
        print(f"[DEBUG] 設定所有 tooltip 啟用狀態: {enabled}")
    
    def destroy_all(self):
        """銷毀所有 tooltip"""
        for tooltip in self.tooltips.values():
            tooltip.hide_tooltip()
        self.tooltips.clear()