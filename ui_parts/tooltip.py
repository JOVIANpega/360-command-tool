# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk

class ToolTip:
    """
    創建一個ToolTip提示框
    """
    def __init__(self, widget, text='widget info', delay=500, wraplen=250):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplen = wraplen
        self.widget.bind("<Enter>", self.enter, add=True)
        self.widget.bind("<Leave>", self.leave, add=True)
        self.widget.bind("<ButtonPress>", self.leave, add=True)
        self.id = None
        self.tw = None
        self.enabled = True  # 新增：控制是否啟用 ToolTip

    def enter(self, event=None):
        if not self.enabled:  # 新增：檢查是否啟用
            return
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        if not self.enabled:  # 新增：檢查是否啟用
            return
        x, y, cx, cy = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        # 創建提示窗口
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        
        # 創建標籤
        label = tk.Label(self.tw, text=self.text, justify='left',
                        background="#ffffe0", relief='solid', borderwidth=1,
                        font=("Microsoft JhengHei UI", "10", "normal"),
                        wraplength=self.wraplen)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()

    def set_enabled(self, enabled):
        """設定是否啟用 ToolTip"""
        self.enabled = enabled
        if not enabled and self.tw:
            self.hidetip()

    def update_text(self, new_text):
        """更新提示文字"""
        self.text = new_text


class ToolTipManager:
    """
    管理所有 ToolTip 的啟用/停用狀態
    """
    def __init__(self):
        self.tooltips = []
        self.enabled = True

    def add_tooltip(self, widget, text, delay=500, wraplen=250):
        """添加一個 ToolTip"""
        tooltip = ToolTip(widget, text, delay, wraplen)
        tooltip.set_enabled(self.enabled)
        self.tooltips.append(tooltip)
        return tooltip

    def set_all_enabled(self, enabled):
        """設定所有 ToolTip 的啟用狀態"""
        self.enabled = enabled
        for tooltip in self.tooltips:
            tooltip.set_enabled(enabled)

    def remove_tooltip(self, tooltip):
        """移除一個 ToolTip"""
        if tooltip in self.tooltips:
            self.tooltips.remove(tooltip) 