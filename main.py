# -*- coding: utf-8 -*-

import os

import sys

import tkinter as tk

from tkinter import ttk, messagebox

import traceback

from config_core import load_commands, load_highlight_keywords, load_setup

from ui_parts.ui_main import SerialUI, TabManager

import re

import threading

import json



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



def setup_logging():

    try:

        with open("run_log.txt", "a", encoding="utf-8") as f:

            f.write("=== 應用程式啟動 ===\n")

    except Exception:

        pass



if __name__ == "__main__":

    log_file = "error_log.txt"

    try:

        setup_logging()

        

        # 讀取 highlight_keywords

        try:

            with open('highlight_keywords.json', 'r', encoding='utf-8') as f:

                highlight_keywords = json.load(f)

        except (FileNotFoundError, json.JSONDecodeError):

            highlight_keywords = {}



        root = tk.Tk()

        # 初始化統一設定管理器
        from ui_parts.shared_config import get_shared_config
        shared_config = get_shared_config(root)
        print("[DEBUG] 統一設定管理器已在主程式中初始化")

        app = TabManager(root, highlight_keywords=highlight_keywords)

        

        # 載入視窗標題和大小

        setup = load_setup()

        dut_setup = setup.get('DUT_Control', {})

        

        # 優先使用頂層的 Window_Title

        title = setup.get('Window_Title')

        if not title:

            title = dut_setup.get('Window_Title', 'VALO360 指令通')

            

        print(f"[DEBUG] 程式啟動時設置視窗標題: {title}")

        width = dut_setup.get('Window_Width', 1024)

        height = dut_setup.get('Window_Height', 768)

        

        # 設置視窗標題和大小

        root.title(title)

        root.geometry(f"{width}x{height}")
        
        # 新增：視窗大小變動時即時寫回 setup.json
        def on_resize(event):
            try:
                # 確保 root 視窗存在
                if not root.winfo_exists():
                    return
                
                import json
                from config_core import load_setup, save_setup
                setup = load_setup()
                setup["Window_Width"] = str(root.winfo_width())
                setup["Window_Height"] = str(root.winfo_height())
                if "DUT_Control" not in setup:
                    setup["DUT_Control"] = {}
                setup["DUT_Control"]["Window_Width"] = str(root.winfo_width())
                setup["DUT_Control"]["Window_Height"] = str(root.winfo_height())
                save_setup(setup)
            except Exception as e:
                # 減少在主控台的輸出，避免干擾
                # print(f"[錯誤] 即時寫回視窗大小失敗: {e}")
                pass
        root.bind('<Configure>', on_resize)

        

        # 讀取標籤頁名稱並立即更新

        if hasattr(app, 'update_tab_names'):

            print(f"[DEBUG] 程式啟動時更新標籤頁名稱")

            app.update_tab_names()

        

        root.mainloop()



    except Exception as e:

        import traceback

        with open(log_file, "w", encoding="utf-8") as f:

            f.write(f"An unexpected error occurred: {e}\n")

            f.write(traceback.format_exc())

        print(f"An error occurred. Details have been written to {log_file}")

