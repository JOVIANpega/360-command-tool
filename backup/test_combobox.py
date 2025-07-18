# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import sys
import os

def limit_dropdown_height(event=None, combo=None):
    """限制下拉列表的高度，最多顯示指定行數"""
    try:
        # 獲取觸發事件的 combobox
        if event and event.widget:
            combo = event.widget
        
        if not combo:
            print("[ERROR] 未提供 combobox")
            return
            
        # 獲取項目總數和設置的最大顯示數
        total_items = len(combo['values'])
        max_items = min(total_items, 20)  # 最多顯示20項
        
        # 使用 tkinter 的 option_add 方法設置全局下拉列表高度
        root.option_add('*TCombobox*Listbox.maxHeight', str(max_items))
        
        # 另一種方法：直接設置 combobox 的 height 屬性
        combo.configure(height=max_items)
        
        print(f"[DEBUG] 限制下拉列表高度為 {max_items} 行")
        
    except Exception as e:
        print(f"[ERROR] 限制下拉列表高度時發生錯誤：{e}")
        import traceback
        traceback.print_exc()

def create_test_window():
    global root
    root = tk.Tk()
    root.title("下拉列表測試")
    root.geometry("400x300")
    
    # 創建一個框架
    frame = ttk.Frame(root)
    frame.pack(padx=10, pady=10, fill='both', expand=True)
    
    # 創建標籤
    label = ttk.Label(frame, text="測試下拉列表:")
    label.pack(anchor='w', pady=5)
    
    # 創建下拉列表
    values = [f"選項 {i}" for i in range(1, 51)]  # 創建50個選項
    combo = ttk.Combobox(frame, values=values, state='readonly')
    combo.pack(fill='x', pady=5)
    
    # 綁定事件
    combo.bind("<<ComboboxOpened>>", lambda e: limit_dropdown_height(e))
    
    # 創建按鈕
    btn = ttk.Button(frame, text="測試", command=lambda: print("按鈕點擊"))
    btn.pack(pady=10)
    
    # 顯示窗口
    root.mainloop()

if __name__ == "__main__":
    create_test_window() 