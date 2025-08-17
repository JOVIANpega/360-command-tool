# -*- coding: utf-8 -*-
"""
Tooltip 功能測試腳本
用於驗證 tooltip 系統是否正常工作
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# 添加 ui_parts 到路徑
sys.path.insert(0, 'ui_parts')

def test_tooltip():
    """測試 tooltip 功能"""
    root = tk.Tk()
    root.title("Tooltip 測試")
    root.geometry("400x300")
    
    # 測試 tooltip 管理器
    try:
        from ui_parts.tooltip import get_tooltip_manager
        tooltip_manager = get_tooltip_manager()
        print(f"[TEST] Tooltip 管理器狀態: enabled={tooltip_manager.enabled}")
        print(f"[TEST] Tooltip 配置數量: {len(tooltip_manager.tooltip_config)}")
        
        # 創建測試按鈕
        test_button = tk.Button(root, text="測試按鈕 (應該有 tooltip)")
        test_button.pack(pady=20)
        
        # 添加 tooltip
        tooltip_manager.add_tooltip(test_button, "btn_execute")
        print(f"[TEST] 已為測試按鈕添加 tooltip")
        
        # 創建另一個測試按鈕
        test_button2 = tk.Button(root, text="測試按鈕 2 (應該有 tooltip)")
        test_button2.pack(pady=20)
        
        # 添加 tooltip
        tooltip_manager.add_tooltip(test_button2, "btn_clear")
        print(f"[TEST] 已為測試按鈕2添加 tooltip")
        
        # 創建一個沒有 tooltip 的按鈕
        no_tooltip_button = tk.Button(root, text="無 tooltip 按鈕")
        no_tooltip_button.pack(pady=20)
        
        # 顯示配置資訊
        info_label = tk.Label(root, text=f"Tooltip 配置載入成功！\n共 {len(tooltip_manager.tooltip_config)} 個配置\n\n將滑鼠懸停在按鈕上測試 tooltip")
        info_label.pack(pady=20)
        
        print("[TEST] 測試視窗已創建，請將滑鼠懸停在按鈕上測試 tooltip")
        
    except Exception as e:
        print(f"[ERROR] 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        
        # 顯示錯誤資訊
        error_label = tk.Label(root, text=f"Tooltip 測試失敗:\n{str(e)}", fg="red")
        error_label.pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    test_tooltip()
