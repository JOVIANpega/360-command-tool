import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import traceback

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
ui_parts_dir = os.path.join(current_dir, 'ui_parts')
sys.path.append(ui_parts_dir)

def write_log(msg):
    with open("run_log.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

write_log("main.py 啟動")

try:
    from ui_parts.ui_main import TabManager
    write_log("成功 import TabManager")
except Exception as e:
    write_log("import TabManager 失敗：" + traceback.format_exc())
    raise

def main():
    root = tk.Tk()
    root.title('VALO360 指令通')
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
    
    # 創建分頁管理器
    app = TabManager(root)
    
    # 設置關閉事件
    def on_closing():
        try:
            dut = app.get_dut_settings() if hasattr(app, 'get_dut_settings') else {}
            fixture = app.get_fixture_settings() if hasattr(app, 'get_fixture_settings') else {}
            from config import save_setup
            save_setup({'DUT': dut, 'FIXTURE': fixture})
            root.destroy()
        except Exception as e:
            messagebox.showerror('錯誤', f'關閉程式時發生錯誤: {e}')
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == '__main__':
    main()
    write_log("__main__ 結束")