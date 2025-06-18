import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import traceback

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

# 定义应用版本
APP_VERSION = "V1.36"

def main():
    root = tk.Tk()
    root.title(f'VALO360 指令通 {APP_VERSION}')
    try:
        root.iconbitmap('app.ico')
    except:
        pass
    
    # 設置窗口大小和位置
    window_width = 800
    window_height = 600
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f'{window_width}x{window_height}+{x}+{y}')
    
    # 創建分頁管理器（TabManager 會自己處理關閉事件）
    app = TabManager(root)
    
    root.mainloop()

if __name__ == '__main__':
    main()
    write_log("__main__ 結束")