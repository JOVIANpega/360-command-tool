#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全域通知區域測試腳本
用於驗證全域通知功能是否正常工作
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def test_global_notification():
    """測試全域通知功能"""
    try:
        # 導入主要模組
        from ui_parts.ui_main import TabManager
        from config_core import load_setup
        
        print("[INFO] 正在啟動全域通知測試...")
        
        # 創建測試視窗
        root = tk.Tk()
        root.title("全域通知測試")
        root.geometry("800x600")
        
        # 載入設定
        setup = load_setup()
        
        # 創建TabManager（包含全域通知管理器）
        tab_manager = TabManager(root)
        
        # 等待1秒後開始測試通知
        def run_notification_tests():
            print("[INFO] 開始測試全域通知...")
            
            # 測試不同類型的通知
            notifications = [
                ("歡迎使用全域通知系統！", "info", 2000),
                ("連接測試成功", "success", 2000),
                ("這是一個警告信息", "warning", 2000),
                ("錯誤信息測試", "error", 2000),
                ("系統狀態: 一切正常", "default", 2000),
            ]
            
            delay = 0
            for message, msg_type, duration in notifications:
                # 使用延遲來依次顯示通知
                root.after(delay, lambda m=message, t=msg_type, d=duration: 
                          tab_manager.show_global_notification(m, t, d))
                delay += 2500  # 每2.5秒顯示下一個通知
            
            # 最後顯示系統信息
            root.after(delay, lambda: tab_manager.show_global_notification(
                "全域通知系統測試完成！\n所有功能正常運行\n可以在任何Tab中看到此通知", 
                "success", 
                5000
            ))
        
        # 延遲1.5秒開始測試（等待初始化完成）
        root.after(1500, run_notification_tests)
        
        print("[INFO] 測試視窗已啟動，請查看GUI底部的全域通知區域")
        print("[INFO] 將會依次顯示不同類型的通知消息")
        print("[INFO] 按Ctrl+C或關閉視窗結束測試")
        
        # 啟動GUI主循環
        root.mainloop()
        
    except Exception as e:
        print(f"[ERROR] 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_global_notification() 