# -*- coding: utf-8 -*-
"""
指令通主程式
提供序列埠通訊和指令執行的圖形化介面
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import traceback
import re
import threading
import json

# 導入核心模組
from core import get_error_handler, get_config_manager, safe_execute, log_info, log_error

# 導入配置和UI模組
from config_core import load_commands, load_highlight_keywords, load_setup
from ui_parts.ui_main import SerialUI, TabManager



# 初始化核心組件
error_handler = get_error_handler()
config_manager = get_config_manager()

# 設置路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

ui_parts_dir = os.path.join(current_dir, 'ui_parts')
if ui_parts_dir not in sys.path:
    sys.path.insert(0, ui_parts_dir)

@safe_execute(error_handler)
def write_log(msg: str):
    """寫入運行日誌"""
    try:
        with open("run_log.txt", "a", encoding="utf-8") as f:
            f.write(msg + "\n")
        log_info(f"運行日誌: {msg}")
    except Exception as e:
        log_error("寫入運行日誌失敗", e)

# 記錄啟動
write_log("main.py 啟動")
log_info("指令通主程式啟動")



@safe_execute(error_handler, show_user_error=True)
def import_required_modules():
    """導入必要的模組"""
    try:
        from ui_parts.ui_main import TabManager
        write_log("成功 import TabManager")
        log_info("UI模組導入成功")
        return TabManager
    except Exception as e:
        write_log("import TabManager 失敗：" + traceback.format_exc())
        log_error("導入UI模組失敗", e, show_user=True)
        sys.exit(1)

@safe_execute(error_handler)
def setup_logging():
    """設置日誌系統"""
    try:
        with open("run_log.txt", "a", encoding="utf-8") as f:
            f.write("=== 應用程式啟動 ===\n")
        log_info("日誌系統初始化完成")
    except Exception as e:
        log_error("設置日誌系統失敗", e)

# 導入模組
TabManager = import_required_modules()

@safe_execute(error_handler)
def setup_window_properties(root):
    """設置視窗屬性"""
    try:
        # 載入設定
        setup = load_setup()
        dut_setup = setup.get('DUT_Control', {})

        # 設置視窗標題
        base_title = setup.get('Window_Title')
        if not base_title:
            base_title = dut_setup.get('Window_Title', '指令通')

        app_version = setup.get('version', '')
        full_title = f"{base_title}_{app_version}" if app_version else base_title

        # 設置視窗大小
        width = int(dut_setup.get('Window_Width', 1024))
        height = int(dut_setup.get('Window_Height', 768))

        # 應用設置
        root.title(full_title)
        root.geometry(f"{width}x{height}")

        log_info(f"視窗設置完成: {full_title} ({width}x{height})")

        # 設置視窗大小變動事件
        setup_window_resize_handler(root)

    except Exception as e:
        log_error("設置視窗屬性失敗", e)

@safe_execute(error_handler)
def setup_window_resize_handler(root):
    """設置視窗大小變動處理器"""
    def on_resize(event):
        try:
            if not root.winfo_exists():
                return

            # 使用配置管理器更新設定（不自動保存）
            config_manager.set_value('Window_Width', str(root.winfo_width()), manual_save=False)
            config_manager.set_value('Window_Height', str(root.winfo_height()), manual_save=False)
            config_manager.set_value('DUT_Control.Window_Width', str(root.winfo_width()), manual_save=False)
            config_manager.set_value('DUT_Control.Window_Height', str(root.winfo_height()), manual_save=False)

        except Exception as e:
            # 靜默處理，避免干擾用戶操作
            pass

    root.bind('<Configure>', on_resize)



@safe_execute(error_handler)
def load_highlight_keywords() -> dict:
    """載入關鍵字高亮設定"""
    try:
        with open('highlight_keywords.json', 'r', encoding='utf-8') as f:
            highlight_keywords = json.load(f)
        log_info(f"載入了 {len(highlight_keywords)} 個關鍵字高亮設定")
        return highlight_keywords
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log_info("未找到關鍵字高亮設定文件，使用空設定")
        return {}
    except Exception as e:
        log_error("載入關鍵字高亮設定失敗", e)
        return {}

@safe_execute(error_handler, show_user_error=True)
def initialize_application():
    """初始化應用程式"""
    try:
        setup_logging()

        # 禁用ConfigManager的自動保存功能
        from core.config_manager import get_config_manager
        config_manager = get_config_manager()
        config_manager.disable_auto_save()
        log_info("ConfigManager自動保存已禁用")

        # 載入關鍵字高亮設定
        highlight_keywords = load_highlight_keywords()

        # 創建主視窗
        root = tk.Tk()

        # 設定應用程式圖標
        try:
            icon_path = os.path.join(current_dir, 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
                log_info(f"應用程式圖標已設定: {icon_path}")
            else:
                log_info("圖標文件不存在，使用預設圖標")
        except Exception as e:
            log_error("設定應用程式圖標失敗", e)

        # 初始化統一設定管理器
        from ui_parts.shared_config import get_shared_config
        shared_config = get_shared_config(root)
        log_info("統一設定管理器已初始化")

        # 創建應用程式實例
        app = TabManager(root, highlight_keywords=highlight_keywords)

        return root, app

    except Exception as e:
        log_error("初始化應用程式失敗", e, show_user=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        # 初始化應用程式
        root, app = initialize_application()

        # 設置視窗屬性
        setup_window_properties(root)

        # 更新標籤頁名稱
        if hasattr(app, 'update_tab_names'):
            log_info("程式啟動時更新標籤頁名稱")
            app.update_tab_names()

        # 設置關閉事件處理
        def on_closing():
            try:
                # 保存視窗大小（手動保存）
                from core.config_manager import get_config_manager
                config_manager = get_config_manager()
                config_manager.set_value('Window_Width', str(root.winfo_width()), manual_save=True)
                config_manager.set_value('Window_Height', str(root.winfo_height()), manual_save=True)

                # 強制保存所有待保存的設定
                from ui_parts.shared_config import get_shared_config
                shared_config = get_shared_config()
                if hasattr(shared_config, 'force_save_all'):
                    shared_config.force_save_all()
                    log_info("程式關閉時已保存所有待保存的設定")

                log_info("程式正常關閉")
            except Exception as e:
                log_error(f"關閉程式時發生錯誤: {e}")
            finally:
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        # 啟動主循環
        log_info("應用程式啟動完成，進入主循環")
        root.mainloop()

    except Exception as e:
        log_error("應用程式運行時發生嚴重錯誤", e, show_user=True)

        # 寫入錯誤日誌文件（向後相容）
        try:
            with open("error_log.txt", "w", encoding="utf-8") as f:
                f.write(f"An unexpected error occurred: {e}\n")
                f.write(traceback.format_exc())
        except Exception:
            pass

        sys.exit(1)

    finally:
        # 清理資源
        try:
            from core import get_resource_manager
            get_resource_manager().cleanup()
            log_info("應用程式資源清理完成")
        except Exception as e:
            log_error("清理資源時發生錯誤", e)

