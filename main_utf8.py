# -*- coding: utf-8 -*-
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import traceback
from config_core import load_commands, load_highlight_keywords
from ui_parts.ui_main import SerialUI, TabManager
import re
import threading

# 設置路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

ui_parts_dir = os.path.join(current_dir, 'ui_parts')
if ui_parts_dir not in sys.path:
    sys.path.insert(0, ui_parts_dir)

def write_log(msg):
    try:
        with open("run_log.txt", "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

write_log("main.py 啟動")

try:
    from ui_parts.ui_main import TabManager
    write_log("成功 import TabManager")
except Exception as e:
    write_log("import TabManager 失敗：" + traceback.format_exc())
    messagebox.showerror('錯誤', f'導入模組失敗: {e}')
    sys.exit(1)

def main():
    # 版本訊息
    VERSION = "V1.38"
    print(f"===== VALO360 指令通 {VERSION} =====")

    # 載入命令清單
    commands = load_commands()
    
    # 載入關鍵字高亮設定
    highlight_keywords = load_highlight_keywords()
    print(f"[DEBUG] main 函數載入完成，關鍵字高亮設定: {highlight_keywords}")
    
    # 初始化 Tkinter
    root = tk.Tk()
    root.title(f"VALO360 指令通 {VERSION}")
    try:
        root.iconbitmap('app.ico')
    except:
        pass
    
    # 建立標籤頁管理器並初始化 UI
    app = TabManager(root, highlight_keywords)
    
    # 介面置中顯示
    root.update_idletasks()  # 更新元件尺寸
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # 啟動應用程式
    root.mainloop()

if __name__ == "__main__":
    main()
    write_log("__main__ 結束")

