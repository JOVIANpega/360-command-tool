# -*- coding: utf-8 -*-
"""
測試 tooltip 顯示功能
"""

import tkinter as tk
from tkinter import ttk
import sys

# 模擬打包後的環境
sys.frozen = True

# 導入 tooltip 管理器
from ui_parts.tooltip import get_tooltip_manager

def test_tooltip_display():
    """測試 tooltip 顯示功能"""
    root = tk.Tk()
    root.title("Tooltip 測試")
    root.geometry("400x300")
    
    # 獲取 tooltip 管理器
    tm = get_tooltip_manager()
    print(f"Tooltip 管理器狀態: enabled={tm.enabled}, 配置數量={len(tm.tooltip_config)}")
    
    # 創建測試按鈕
    test_button = ttk.Button(root, text="測試按鈕 (應該有 tooltip)")
    test_button.pack(pady=20)
    
    # 添加 tooltip
    tm.add_tooltip(test_button, "btn_refresh")
    
    # 創建測試輸入框
    test_entry = ttk.Entry(root, width=30)
    test_entry.pack(pady=20)
    test_entry.insert(0, "測試輸入框")
    
    # 添加 tooltip
    tm.add_tooltip(test_entry, "entry_window_title")
    
    # 創建測試下拉選單
    test_combo = ttk.Combobox(root, values=["選項1", "選項2", "選項3"])
    test_combo.pack(pady=20)
    test_combo.set("選擇選項")
    
    # 添加 tooltip
    tm.add_tooltip(test_combo, "combobox_transport")
    
    # 創建測試標籤
    test_label = ttk.Label(root, text="測試標籤")
    test_label.pack(pady=20)
    
    # 添加 tooltip
    tm.add_tooltip(test_label, "label_com")
    
    # 顯示配置資訊
    info_text = f"""
Tooltip 測試視窗

配置狀態:
- 啟用: {tm.enabled}
- 配置數量: {len(tm.tooltip_config)}
- 測試按鈕 tooltip: {tm.tooltip_config.get('btn_refresh', '找不到')}
- 測試輸入框 tooltip: {tm.tooltip_config.get('entry_window_title', '找不到')}
- 測試下拉選單 tooltip: {tm.tooltip_config.get('combobox_transport', '找不到')}

請將滑鼠懸停在各種元件上測試 tooltip 功能
    """
    
    info_label = ttk.Label(root, text=info_text, justify='left')
    info_label.pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    test_tooltip_display()
