#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試手動輸入指令模組功能
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# 添加當前目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui_parts.ui_manual_command import ManualCommandUI

def test_manual_command():
    """測試手動輸入指令模組"""
    print("=== 測試手動輸入指令模組 ===")
    
    # 創建測試視窗
    root = tk.Tk()
    root.title("手動輸入指令測試")
    root.geometry("800x600")
    
    # 創建手動輸入指令 UI
    manual_ui = ManualCommandUI(root, root)
    
    print("✓ 手動輸入指令模組初始化成功")
    print("✓ 請在視窗中測試以下功能：")
    print("  1. COM Port 顯示（應顯示 DM PORT / AT PORT / NMEA PORT）")
    print("  2. 指令檔案載入（應顯示分組按鈕）")
    print("  3. 指令清單顯示（應顯示全部指令）")
    print("  4. 在執行結果框中按 Enter 或 Ctrl+V 輸入指令")
    print("  5. 關閉視窗時應正確清理資源")
    
    # 運行測試
    root.mainloop()
    
    print("✓ 測試完成")

if __name__ == "__main__":
    test_manual_command() 