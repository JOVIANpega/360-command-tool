# -*- coding: utf-8 -*-

import os


import sys


import tkinter as tk


from tkinter import ttk, scrolledtext, messagebox


import threading


import json


from datetime import datetime


import subprocess


import webbrowser


import logging


import config_core


import config_utils


from config_utils import get_notification_text, get_app_version


# 將當前目錄加入 Python 路徑


current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


if current_dir not in sys.path:


    sys.path.insert(0, current_dir)





# 導入配置模組


try:


    from config_core import load_setup, save_setup, list_com_ports, GUIDE_FILE, COMMAND_FILE, load_commands


except ImportError as e:


    print(f"導入 config_core 模組失敗: {e}")


    print(f"當前路徑: {sys.path}")


    sys.exit(1)





# 檢查 command.txt


try:


    commands = load_commands()


except Exception as e:


    messagebox.showerror('錯誤', str(e))


    sys.exit(1)





try:


    from serial_worker import SerialWorker


    from ui_parts.ui_components import UIComponents


    from ui_parts.ui_handlers import UIHandlers


    from ui_parts.ui_settings_tab import SettingsTab # 新增


except ImportError as e:


    print(f"導入模組失敗: {e}")


    sys.exit(1)





class TabManager:


    def __init__(self, root, highlight_keywords=None):


        self.root = root


        self.highlight_keywords = highlight_keywords or {}


        print(f"[DEBUG] TabManager 初始化，highlight_keywords={self.highlight_keywords}")
        
        # 初始化 DOS 視窗進程追蹤變數
        self.dos_process = None

        


        # 配置根窗口的 grid


        self.root.grid_rowconfigure(0, weight=1)


        self.root.grid_rowconfigure(1, weight=0)  # 通知區域不擴展


        self.root.grid_columnconfigure(0, weight=1)


        


        # 初始化全局樣式


        self.init_global_styles()


        


        # 創建主內容框架


        main_content_frame = ttk.Frame(root)


        main_content_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)


        main_content_frame.grid_rowconfigure(0, weight=1)


        main_content_frame.grid_columnconfigure(0, weight=1)


        


        # 創建Notebook


        self.notebook = ttk.Notebook(main_content_frame)


        self.notebook.grid(row=0, column=0, sticky='nsew')


        


        # 創建分頁


        self.dut_frame = ttk.Frame(self.notebook, style='Main.TFrame')


        self.fixture_frame = ttk.Frame(self.notebook, style='Main.TFrame')


        self.handover_frame = ttk.Frame(self.notebook, style='Main.TFrame')  # 新增第三個 tab


        


        # 配置分頁的 grid


        self.dut_frame.grid_rowconfigure(0, weight=1)


        self.dut_frame.grid_columnconfigure(0, weight=1)


        self.fixture_frame.grid_rowconfigure(0, weight=1)


        self.fixture_frame.grid_columnconfigure(0, weight=1)


        self.handover_frame.grid_rowconfigure(0, weight=1)


        self.handover_frame.grid_columnconfigure(0, weight=1)

        # 從設定檔讀取標籤名稱
        from config_core import load_setup
        setup = load_setup()
        tab_names = setup.get('tab_names', {})
        
        # 使用從設定檔中讀取的標籤名稱，如果不存在則使用預設值
        tab0_name = tab_names.get('tab0', 'DUT 控制')
        tab1_name = tab_names.get('tab1', '治具控制')
        tab2_name = tab_names.get('tab2', '使用說明')
        tab3_name = tab_names.get('tab3', '設定')
        
        print(f"[DEBUG] 從設定檔讀取的標籤名稱: {tab_names}")
        


        # 添加分頁到 notebook


        self.notebook.add(self.dut_frame, text=tab0_name)


        self.notebook.add(self.fixture_frame, text=tab1_name)


        self.notebook.add(self.handover_frame, text=tab2_name)  # 改名為使用說明
        
        # 新增設定分頁
        self.settings_frame = ttk.Frame(self.notebook, style='Main.TFrame')
        self.notebook.add(self.settings_frame, text=tab3_name)

        # 設置分頁切換事件
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)


        


        # 先創建全域通知區域 - 放在整個GUI的最底部
        self.init_global_notification_area(root, setup)
        
        # 初始化分頁內容（此時通知管理器已經可用）


        self.init_dut_tab()


        self.init_fixture_tab()


        self.init_guide_tab()  # 改名為 init_guide_tab
        self.init_settings_tab() # 新增
        
        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def init_global_notification_area(self, parent, setup):
        """初始化全域通知區域"""
        try:
            # 導入NotificationManager
            from ui_parts.notification_manager import NotificationManager
            
            # 創建通知管理器
            self.notification_manager = NotificationManager(parent, setup)
            
            # 創建全域變數方便其他模組使用
            self.notification_text = self.notification_manager.notification_text
            
            # 顯示啟動訊息
            app_version = config_utils.get_app_version()
            app_name = setup.get('Window_Title', setup.get('DUT_Control', {}).get('Window_Title', 'VALO360 指令通'))
            
            # 延遲1秒顯示啟動訊息
            self.root.after(1000, lambda: self.notification_manager.show_notification(
                f"{app_name} 已啟動 (版本：V{app_version})", "success"
            ))
            
            print("[DEBUG] 全域通知區域初始化完成")
            
        except Exception as e:
            print(f"[ERROR] 初始化全域通知區域失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def show_global_notification(self, message, message_type="info", duration=2000, callback=None):
        """顯示全域通知的快捷方法"""
        if hasattr(self, 'notification_manager'):
            self.notification_manager.show_notification(message, message_type)
        else:
            print(f"[WARNING] 通知管理器未初始化: {message}")
    
    def update_notification(self, message, message_type="info", duration=2000):
        """更新全域通知區域的內容（統一管理所有提示訊息）"""
        self.show_global_notification(message, message_type, duration)


    def update_dut_settings(self):
        """Callback function to update DUT tab settings."""
        print("[DEBUG] Received callback to update DUT settings.")
        if hasattr(self, 'dut_ui'):
            # 重新載入設定並更新所有 UI 元件
            self.dut_ui.setup = self.dut_ui.config.load_setup()
            self.dut_ui.handlers.reload_setup(self.dut_ui.setup)
            self.dut_ui.update_from_config()
            
            # 更新 DUT 控制頁面的按鈕
            self.update_dut_buttons()
            
            # 顯示通知給用戶 - 增加顯示時間到8秒，確保用戶能看到
            if hasattr(self.dut_ui.components, 'show_notification'):
                try:
                    # 使用更醒目的通知效果 - 背景閃爍、更大字體
                    settings_changed = [
                        get_notification_text("settings_updated"),
                        get_notification_text("cmd_reloaded"),
                        get_notification_text("com_updated"),
                        get_notification_text("end_string_updated"),
                        get_notification_text("ip_updated"),
                        get_notification_text("timeout_updated")
                    ]
                    
                    self.dut_ui.components.show_notification(
                        "\n".join(settings_changed), 
                        "green", 
                        8000,
                        callback=lambda: self.notebook.select(0)  # 回調函數：切換到DUT控制頁面
                    )
                except Exception as e:
                    print(f"[ERROR] 顯示通知時發生錯誤：{e}")
                    # 繼續執行，不讓通知錯誤影響其他功能
                
                # 強制切換到DUT控制頁面，確保用戶能看到更新效果
                self.notebook.select(0)  # 假設DUT控制頁面是第一個分頁
    
    def update_dut_buttons(self):
        """根據當前指令檔案動態更新 DUT 控制頁面的分類按鈕"""
        try:
            # 檢查 dut_ui 和 components 是否存在
            if not hasattr(self, 'dut_ui') or not hasattr(self.dut_ui, 'components'):
                print("[ERROR] dut_ui 或 components 不存在，無法更新按鈕")
                return
                
            # 直接從當前指令檔案中讀取區段標題，不依賴設定檔中的快取
            print("[DEBUG] update_dut_buttons: 從當前指令檔案中讀取區段標題")
            
            # 從設定中獲取指令檔案路徑
            command_file_path = self.dut_ui.setup.get("DUT_Control", {}).get("Command_File_Path", "")
            print(f"[DEBUG] update_dut_buttons: 指令檔案路徑: {command_file_path}")
            
            section_titles = []
            
            if command_file_path and os.path.exists(command_file_path):
                print(f"[DEBUG] update_dut_buttons: 使用設定中的指令檔案: {command_file_path}")
                try:
                    with open(command_file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith('==') and line.endswith('=='):
                                section_name = line.strip('=')
                                if section_name and section_name not in section_titles:
                                    section_titles.append(section_name)
                                    print(f"[DEBUG] update_dut_buttons: 從指令文件中找到區段: {section_name}")
                except Exception as e:
                    print(f"[ERROR] update_dut_buttons: 讀取指令文件時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                # 嘗試使用預設指令檔案
                print(f"[DEBUG] update_dut_buttons: 指令檔案不存在，嘗試使用預設檔案")
                from config_core import COMMAND_FILE
                if os.path.exists(COMMAND_FILE):
                    try:
                        with open(COMMAND_FILE, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line.startswith('==') and line.endswith('=='):
                                    section_name = line.strip('=')
                                    if section_name and section_name not in section_titles:
                                        section_titles.append(section_name)
                                        print(f"[DEBUG] update_dut_buttons: 從預設指令文件中找到區段: {section_name}")
                    except Exception as e:
                        print(f"[ERROR] update_dut_buttons: 讀取預設指令文件時發生錯誤: {e}")
            
            # 如果仍然沒有區段標題，使用預設值
            if not section_titles:
                print("[DEBUG] update_dut_buttons: 未找到區段標題，使用預設值")
                section_titles = ['全部指令']
                
            print(f"[DEBUG] update_dut_buttons: 最終使用的區段標題: {section_titles}")
            
            # 檢查是否有 section_frame 和 section_radiobuttons
            if not hasattr(self.dut_ui.components, 'section_frame') or not hasattr(self.dut_ui.components, 'section_radiobuttons'):
                print("[ERROR] section_frame 或 section_radiobuttons 不存在，無法更新按鈕")
                return
                
            # 清除現有的按鈕
            for rb in self.dut_ui.components.section_radiobuttons:
                rb.destroy()
            self.dut_ui.components.section_radiobuttons = []
            
            # 更新 sections 列表
            self.dut_ui.components.sections = section_titles
            
            # 設定預設選中的分類
            if section_titles:
                self.dut_ui.components.section_var.set(section_titles[0])
            
            # 限制每行最多顯示4個按鈕
            max_buttons_per_row = 4
            
            # 創建新按鈕
            for i, sec in enumerate(section_titles):
                # 計算行和列位置
                row = i // max_buttons_per_row
                col = i % max_buttons_per_row
                
                rb = tk.Radiobutton(
                    self.dut_ui.components.section_frame, 
                    text=sec, 
                    variable=self.dut_ui.components.section_var, 
                    value=sec, 
                    command=self.dut_ui.components.update_cmd_list,
                    bg='#d9d9d9', 
                    fg='black', 
                    selectcolor='#d9d9d9', 
                    activebackground='#2196f3', 
                    activeforeground='white',
                    indicatoron=0, 
                    relief='flat', 
                    borderwidth=1, 
                    width=8, 
                    height=1,
                    font=('Microsoft JhengHei UI', int(self.dut_ui.setup.get('UI_Font_Size', '12')))
                )
                rb.grid(row=row, column=col, padx=1, pady=1, sticky='ew')
                rb.bind("<Enter>", lambda e, b=rb: b.config(bg="#2196f3", fg='white'))
                rb.bind("<Leave>", lambda e, b=rb: self.dut_ui.components.update_radio_bg())
                self.dut_ui.components.section_radiobuttons.append(rb)
                
                # 設置列的權重，使按鈕平均分配空間
                self.dut_ui.components.section_frame.columnconfigure(col, weight=1)
            
            # 更新按鈕背景色
            self.dut_ui.components.update_radio_bg()
            
            # 更新指令下拉選單
            self.dut_ui.components.update_cmd_list()
            
            print(f"[DEBUG] update_dut_buttons: 已更新 {len(section_titles)} 個 DUT 按鈕")
            
        except Exception as e:
            print(f"[ERROR] 更新 DUT 按鈕時發生錯誤：{e}")
            import traceback
            traceback.print_exc()


    def update_tab_names(self):
        """根據設定檔中的標籤名稱更新 TAB 按鈕的名稱"""
        try:
            # 從設定檔讀取標籤名稱
            from config_core import load_setup
            setup = load_setup()
            tab_names = setup.get('tab_names', {})
            
            # 預設的 TAB 按鈕名稱
            default_tab_names = ['DUT 控制', '治具控制', '使用說明', '設定']
            
            # 更新標籤名稱
            for i in range(4):  # 目前有4個標籤頁
                tab_key = f'tab{i}'
                if tab_key in tab_names:
                    # 使用設定檔中的名稱
                    self.notebook.tab(i, text=tab_names[tab_key])
                    print(f"[DEBUG] 更新 TAB {i} 名稱為：{tab_names[tab_key]}（從設定檔）")
                else:
                    # 使用預設名稱
                    self.notebook.tab(i, text=default_tab_names[i])
                    print(f"[DEBUG] 更新 TAB {i} 名稱為：{default_tab_names[i]}（預設值）")
        
        except Exception as e:
            print(f"[ERROR] 更新 TAB 按鈕名稱時發生錯誤：{e}")
            import traceback
            traceback.print_exc()
            
            # 發生錯誤時，使用預設名稱
            default_tab_names = ['DUT 控制', '治具控制', '使用說明', '設定']
            for i, name in enumerate(default_tab_names):
                try:
                    self.notebook.tab(i, text=name)
                except Exception:
                    pass


    def update_fixture_settings(self):


        """Callback function to update Fixture tab settings."""


        print("[DEBUG] Received callback to update Fixture settings.")


        if hasattr(self, 'fixture_ui'):


            # 重新載入設定


            from config_core import load_setup


            setup = load_setup()


            fixture_setup = setup.get('Fixture_Control', {})


            


            # 更新治具UI元件


            if hasattr(self.fixture_ui, 'setup'):


                self.fixture_ui.setup = fixture_setup


            


            # 刷新串口列表和其他設定


            if hasattr(self.fixture_ui, 'refresh_ports'):


                self.fixture_ui.refresh_ports()


                


            # 更新測試類別勾選狀態


            if hasattr(self.fixture_ui, 'category_vars'):


                for cat, var in self.fixture_ui.category_vars.items():


                    if cat == 'MB':


                        var.set(fixture_setup.get('Test_Category_MB', True))


                    elif cat == 'FUNCTION':


                        var.set(fixture_setup.get('Test_Category_FUNCTION', False))


                    elif cat == '原始的指令':


                        var.set(fixture_setup.get('Test_Category_Original_Commands', False))


            


            # 更新字體大小


            if hasattr(self.fixture_ui, '_fixture_font_size') and 'Fixture_Font_Size' in fixture_setup:


                try:


                    new_size = int(fixture_setup['Fixture_Font_Size'])


                    if new_size != self.fixture_ui._fixture_font_size:


                        self.fixture_ui._fixture_font_size = new_size


                        # 應用新字體大小


                        if hasattr(self.fixture_ui, 'change_fixture_font'):


                            self.fixture_ui.change_fixture_font(0)  # 傳入0表示不增減，只套用當前大小


                except (ValueError, TypeError):


                    pass





    def update_window_title(self):
        """更新視窗標題（包含版本號）"""
        try:
            # 從設定檔讀取視窗標題 (優先使用頂層的 Window_Title)
            from config_core import load_setup
            setup = load_setup()
            
            # 優先使用頂層的 Window_Title，如果不存在則使用 DUT_Control 中的 Window_Title
            window_title = setup.get('Window_Title')
            if not window_title:
                window_title = setup.get('DUT_Control', {}).get('Window_Title')
            
            # 如果兩者都不存在，才使用預設值
            if not window_title:
                window_title = "VALO360 指令通"
            
            # 獲取版本號
            app_version = config_utils.get_app_version()
            
            # 設置新標題
            new_title = f"{window_title} V{app_version}"
            self.root.title(new_title)
            print(f"[DEBUG] 視窗標題已更新為：{new_title}")
        except Exception as e:
            print(f"[ERROR] 更新視窗標題時發生錯誤：{e}")
            import traceback
            traceback.print_exc()

    def update_all_settings(self, settings_dict=None):
        """更新所有設定，確保雙向同步"""
        try:
            print("[DEBUG] 開始更新所有設定...")
            
            # 如果有傳入設定字典，直接使用；否則重新載入
            if settings_dict:
                latest_setup = settings_dict
                print("[DEBUG] 使用傳入的設定字典")
            else:
                from config_core import load_setup
                latest_setup = load_setup()
                print("[DEBUG] 重新載入設定檔")
            
            # 更新DUT設定
            self.update_dut_settings()
            
            # 更新治具設定
            self.update_fixture_settings()
            
            # 更新視窗標題
            self.update_window_title()
            
            # 更新標籤頁名稱
            self.update_tab_names_from_settings()
            
            # 同步所有字體設定
            self.sync_font_settings(latest_setup)
            
            # 同步通知設定
            self.sync_notification_settings(latest_setup)
            
            # 顯示綜合更新通知
            self.show_global_notification(
                "所有設定已更新並同步\n✓ DUT控制設定\n✓ 治具控制設定\n✓ 界面設定\n✓ 標籤頁名稱", 
                "success", 
                5000
            )
            
            print("[DEBUG] 所有設定更新完成")
            
        except Exception as e:
            print(f"[ERROR] 更新所有設定時發生錯誤：{e}")
            import traceback
            traceback.print_exc()
            self.show_global_notification(f"設定更新失敗：{str(e)}", "error", 5000)
    
    def sync_font_settings(self, setup):
        """同步字體設定"""
        try:
            dut_settings = setup.get('DUT_Control', {})
            fixture_settings = setup.get('Fixture_Control', {})
            
            # 同步各種字體設定
            ui_font_size = dut_settings.get('UI_Font_Size', '13')
            content_font_size = dut_settings.get('Content_Font_Size', '11')
            notification_font_size = dut_settings.get('Notification_Font_Size', '10')
            fixture_font_size = fixture_settings.get('Fixture_Font_Size', '11')
            
            print(f"[DEBUG] 字體設定同步 - UI:{ui_font_size}, 內容:{content_font_size}, 通知:{notification_font_size}, 治具:{fixture_font_size}")
            
            # 更新DUT UI的字體設定
            if hasattr(self, 'dut_ui') and hasattr(self.dut_ui, 'components'):
                components = self.dut_ui.components
                
                # 更新字體大小變數
                if hasattr(components, 'font_size_var'):
                    components.font_size_var.set(ui_font_size)
                if hasattr(components, 'content_font_size_var'):
                    components.content_font_size_var.set(content_font_size)
                
                # 更新通知字體大小
                if hasattr(components, 'notification_font_size'):
                    components.notification_font_size = int(notification_font_size)
                
                # 更新標籤字體
                if hasattr(components, 'label_countdown'):
                    components.label_countdown.config(
                        font=('Microsoft JhengHei UI', int(notification_font_size), 'bold')
                    )
                
                # 觸發字體更新
                try:
                    components.update_ui_fonts(int(ui_font_size))
                    components.update_content_fonts(int(content_font_size))
                except Exception as e:
                    print(f"[WARNING] 更新 DUT UI 字體時發生錯誤: {e}")
            
            # 更新治具控制頁面的字體設定
            if hasattr(self, 'fixture_ui') and hasattr(self.fixture_ui, 'update_font_size'):
                try:
                    self.fixture_ui.update_font_size(int(fixture_font_size))
                    print(f"[DEBUG] 已更新治具控制頁面字體大小為: {fixture_font_size}")
                except Exception as e:
                    print(f"[WARNING] 更新治具字體時發生錯誤: {e}")
            
            # 同步系統字體設定到全域通知管理器
            if hasattr(self, 'notification_manager'):
                system_settings = setup.get('System', {})
                global_font_size = system_settings.get('Notification_Font_Size', notification_font_size)
                if hasattr(self.notification_manager, 'notification_text'):
                    try:
                        current_font = self.notification_manager.notification_text.cget("font")
                        if isinstance(current_font, tuple):
                            family, size, style = current_font
                        else:
                            family, size, style = 'Microsoft JhengHei UI', 12, 'bold'
                        
                        new_font = (family, int(global_font_size), style)
                        self.notification_manager.notification_text.config(font=new_font)
                    except Exception as e:
                        print(f"[WARNING] 更新通知管理器字體時發生錯誤: {e}")
                    
        except Exception as e:
            print(f"[ERROR] 同步字體設定時發生錯誤：{e}")
    
    def sync_notification_settings(self, setup):
        """同步通知設定"""
        try:
            # 同步通知相關設定
            system_settings = setup.get('System', {})
            notification_history_count = system_settings.get('Notification_History_Count', 20)
            
            if hasattr(self, 'notification_manager'):
                # 確保通知歷史不超過設定的數量
                if len(self.notification_manager.notification_log) > notification_history_count:
                    self.notification_manager.notification_log = self.notification_manager.notification_log[-notification_history_count:]
                    self.notification_manager.save_notification_history()
                    
                print(f"[DEBUG] 通知設定同步 - 歷史保留數量:{notification_history_count}")
                
        except Exception as e:
            print(f"[ERROR] 同步通知設定時發生錯誤：{e}")
    
    def on_setting_changed(self, setting_category, setting_key, new_value):
        """當任何設定被更改時調用此方法進行雙向同步"""
        try:
            # 載入當前設定
            from config_core import load_setup, save_setup
            setup = load_setup()
            
            # 確保設定類別存在
            if setting_category not in setup:
                setup[setting_category] = {}
            
            # 更新設定值
            old_value = setup[setting_category].get(setting_key, "未設定")
            setup[setting_category][setting_key] = new_value
            
            # 保存設定
            save_setup(setup)
            
            # 立即同步到相關UI組件
            self.sync_setting_to_ui(setting_category, setting_key, new_value)
            
            # 顯示變更通知
            self.show_global_notification(
                f"設定已更新\n分類: {setting_category}\n項目: {setting_key}\n舊值: {old_value}\n新值: {new_value}", 
                "info", 
                3000
            )
            
            print(f"[DEBUG] 設定同步完成 - {setting_category}.{setting_key}: {old_value} → {new_value}")
            
        except Exception as e:
            print(f"[ERROR] 設定變更同步失敗：{e}")
            import traceback
            traceback.print_exc()
    
    def sync_setting_to_ui(self, category, key, value):
        """將單一設定同步到UI組件"""
        try:
            if category == "DUT_Control":
                if hasattr(self, 'dut_ui') and hasattr(self.dut_ui, 'components'):
                    components = self.dut_ui.components
                    
                    # 同步COM口設定
                    if key == "Serial_COM_Port" and hasattr(components, 'combobox_com'):
                        components.combobox_com.set(value)
                        
                    # 同步IP地址設定
                    elif key == "Default_IP_Address" and hasattr(components, 'entry_ip'):
                        components.entry_ip.delete(0, tk.END)
                        components.entry_ip.insert(0, value)
                        
                    # 同步超時設定
                    elif key == "Command_Timeout_Seconds" and hasattr(components, 'entry_timeout'):
                        components.entry_timeout.delete(0, tk.END)
                        components.entry_timeout.insert(0, value)
                        
                    # 同步結束字串設定
                    elif key == "Command_End_String" and hasattr(components, 'combobox_end'):
                        components.combobox_end.set(value)
                        
                    # 同步字體設定
                    elif key == "Notification_Font_Size" and hasattr(components, 'notification_font_size'):
                        components.notification_font_size = int(value)
                        if hasattr(components, 'label_countdown'):
                            components.label_countdown.config(
                                font=('Microsoft JhengHei UI', int(value), 'bold')
                            )
                            
            elif category == "tab_names":
                # 同步標籤頁名稱
                tab_index = int(key.replace('tab', ''))
                if 0 <= tab_index < self.notebook.index('end'):
                    self.notebook.tab(tab_index, text=value)
                    
            elif category == "System":
                # 同步系統設定到全域通知管理器
                if hasattr(self, 'notification_manager'):
                    if key == "Notification_Font_Size":
                        # 更新全域通知字體
                        if hasattr(self.notification_manager, 'notification_text'):
                            current_font = self.notification_manager.notification_text.cget("font")
                            if isinstance(current_font, tuple):
                                family, size, style = current_font
                            else:
                                family, size, style = 'Microsoft JhengHei UI', 12, 'bold'
                            
                            new_font = (family, int(value), style)
                            self.notification_manager.notification_text.config(font=new_font)
                            
        except Exception as e:
            print(f"[ERROR] 同步設定到UI時發生錯誤：{e}")
            import traceback
            traceback.print_exc()
            
    def update_tab_names_from_settings(self):
        """從設定檔同步更新標籤頁名稱"""
        try:
            # 重新載入設定
            from config_core import load_setup
            setup = load_setup()
            tab_names = setup.get('tab_names', {})
            
            # 預設的標籤頁名稱
            default_tab_names = ['DUT 控制', '治具控制', '使用說明', '設定']
            
            # 更新每個標籤頁的名稱
            for i in range(min(4, self.notebook.index('end'))):
                tab_key = f'tab{i}'
                if tab_key in tab_names:
                    new_name = tab_names[tab_key]
                else:
                    new_name = default_tab_names[i] if i < len(default_tab_names) else f"標籤頁 {i+1}"
                
                # 只有當名稱實際改變時才更新
                current_name = self.notebook.tab(i, "text")
                if current_name != new_name:
                    self.notebook.tab(i, text=new_name)
                    print(f"[DEBUG] 標籤頁 {i} 名稱已更新: {current_name} → {new_name}")
            
            # 使用全域通知管理器顯示更新訊息
            self.show_global_notification("標籤頁名稱已同步更新", "success", 2000)
            
        except Exception as e:
            print(f"[ERROR] 更新標籤頁名稱時發生錯誤：{e}")
            import traceback
            traceback.print_exc()
            
    def on_tab_name_changed(self, tab_index, new_name):
        """當標籤頁名稱被手動更改時調用"""
        try:
            # 載入當前設定
            from config_core import load_setup, save_setup
            setup = load_setup()
            
            # 確保tab_names存在
            if 'tab_names' not in setup:
                setup['tab_names'] = {}
            
            # 更新指定標籤頁的名稱
            tab_key = f'tab{tab_index}'
            setup['tab_names'][tab_key] = new_name
            
            # 保存設定
            save_setup(setup)
            
            # 更新Notebook中的標籤頁名稱
            self.notebook.tab(tab_index, text=new_name)
            
            # 顯示更新通知
            self.show_global_notification(f"標籤頁 {tab_index + 1} 名稱已更新為: {new_name}", "info", 3000)
            
        except Exception as e:
            print(f"[ERROR] 更新標籤頁名稱時發生錯誤：{e}")
            import traceback
            traceback.print_exc()


    def init_global_styles(self):


        style = ttk.Style()


        style.theme_use('clam')


        style.configure('Main.TFrame', background='white')


        style.configure('TNotebook', background='white')


        # 分頁標籤字體、大小、padding，預設灰底黑字，選取為藍底白字


        style.configure('TNotebook.Tab', font=('Microsoft JhengHei UI', 13, 'bold'), padding=[16, 6], background='#d9d9d9', foreground='black')


        style.map('TNotebook.Tab',


            background=[('selected', '#2196f3'), ('active', '#0056d6'), ('!active', '#d9d9d9')],


            foreground=[('selected', 'white'), ('active', 'white'), ('!active', 'black')]


        )


        # HANDOVER 分頁綠底白字


        style.element_create('Green.Tab', 'from', 'default')


        style.layout('Green.TNotebook.Tab', style.layout('TNotebook.Tab'))


        style.configure('Green.TNotebook.Tab', background='#1abc1a', foreground='white')


        style.map('Green.TNotebook.Tab',


            background=[('selected', '#1abc1a'), ('active', '#1abc1a'), ('!active', '#d9d9d9')],


            foreground=[('selected', 'white'), ('active', 'white'), ('!active', 'black')]


        )


        # 一般TButton維持灰底黑字hover藍底白字


        style.configure('TButton', font=('Microsoft JhengHei UI', 12), padding=[8, 4])


        style.map('TButton',


            background=[('active', '#003a80'), ('!active', '#f5f5f5')],


            foreground=[('active', 'white'), ('!active', 'black')]


        )


    


    def init_dut_tab(self):
        # 初始化 DUT 控制分頁
        self.dut_ui = SerialUI(self.dut_frame, self.root, self.highlight_keywords)
        
        # 將全域通知管理器傳遞給DUT UI
        if hasattr(self, 'notification_manager'):
            self.dut_ui.global_notification_manager = self.notification_manager
            if hasattr(self.dut_ui, 'components'):
                self.dut_ui.components.global_notification_manager = self.notification_manager
        
        # 初始化完成後立即更新 DUT 按鈕
        self.update_dut_buttons()
        print("[DEBUG] DUT 控制分頁初始化完成，已更新按鈕")


    def init_fixture_tab(self):


        # 初始化治具控制分頁


        from FIXTURE.fixture13 import FixtureFrame


        self.fixture_ui = FixtureFrame(self.fixture_frame)


        self.fixture_ui.pack(fill='both', expand=True)


    def init_settings_tab(self):
        # 初始化設定分頁
        self.settings_ui = SettingsTab(self.settings_frame, on_save_callback=self.update_all_settings)
        self.settings_ui.pack(fill='both', expand=True)
    
    def init_guide_tab(self):
        # 初始化使用說明分頁
        # 創建主框架
        guide_main_frame = ttk.LabelFrame(
            self.handover_frame, 
            text="使用說明", 
            padding=20, 
            style="Main.TLabelframe"
        )
        guide_main_frame.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        
        # 獲取版本號
        app_version = config_utils.get_app_version()
        
        # 標題
        title_label = ttk.Label(
            guide_main_frame,
            text=f"VALO360 指令通 V{app_version} 使用說明",
            font=('Microsoft JhengHei UI', 18, 'bold'),
            style="TLabel"
        )
        title_label.grid(row=0, column=0, pady=(0, 20))


        


        # 說明文字


        desc_label = ttk.Label(


            guide_main_frame,


            text="點擊下方按鈕開啟詳細的使用說明文件",


            font=('Microsoft JhengHei UI', 14),


            style="TLabel"


        )


        desc_label.grid(row=1, column=0, pady=(0, 30))


        


        # 開啟使用說明按鈕


        def open_guide():


            try:


                # 獲取 EXE 目錄路徑


                if getattr(sys, 'frozen', False):


                    # 如果是打包後的 EXE


                    exe_dir = os.path.dirname(sys.executable)


                else:


                    # 如果是開發環境


                    exe_dir = os.path.dirname(os.path.abspath(__file__))


                    exe_dir = os.path.dirname(exe_dir)  # 回到上一層目錄


                


                guide_file = os.path.join(exe_dir, "VALO360 指令通使用指南.html")


                


                if not os.path.exists(guide_file):


                    messagebox.showerror("錯誤", f"找不到使用指南檔案：\n{guide_file}")


                    return


                


                # 嘗試用 Chrome 開啟


                chrome_paths = [


                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",


                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",


                    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")


                ]


                


                chrome_opened = False


                for chrome_path in chrome_paths:


                    if os.path.exists(chrome_path):


                        try:


                            subprocess.Popen([chrome_path, guide_file])


                            chrome_opened = True


                            break


                        except Exception:


                            continue


                


                # 如果 Chrome 開啟失敗，嘗試用預設瀏覽器


                if not chrome_opened:


                    try:


                        webbrowser.open(f"file:///{guide_file.replace(os.sep, '/')}")


                    except Exception as e:


                        messagebox.showerror("錯誤", f"無法開啟使用指南：\n{str(e)}")


                        


            except Exception as e:


                messagebox.showerror("錯誤", f"開啟使用指南時發生錯誤：\n{str(e)}")


        


        guide_button = tk.Button(


            guide_main_frame,


            text="開啟使用說明",


            command=open_guide,


            font=('Microsoft JhengHei UI', 16, 'bold'),


            width=20,


            height=3,


            bg='#cccccc',


            fg='black',


            relief='groove',


            borderwidth=2,


            highlightthickness=0


        )


        guide_button.grid(row=2, column=0, pady=20)


        


        # 按鈕 hover 效果


        guide_button.bind("<Enter>", lambda e: guide_button.config(bg="#4caf50", fg="white"))


        guide_button.bind("<Leave>", lambda e: guide_button.config(bg="#cccccc", fg="black"))


        # 添加「開啟 DOS 視窗」按鈕
        def open_dos_window():
            # 檢查是否已經開啟 DOS 視窗
            if self.dos_process is None or self.dos_process.poll() is not None:
                # 如果沒有開啟或已關閉，則開啟新的 DOS 視窗
                self.dos_process = subprocess.Popen(["cmd"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                print("[DEBUG] 已開啟 DOS 視窗")
            else:
                # 如果已經開啟，則顯示提示訊息
                messagebox.showinfo("提示", "DOS 視窗已經開啟")
        
        dos_button = tk.Button(
            guide_main_frame,
            text="開啟 DOS 視窗",
            command=open_dos_window,
            font=('Microsoft JhengHei UI', 16, 'bold'),
            width=20,
            height=3,
            bg='#cccccc',
            fg='black',
            relief='groove',
            borderwidth=2,
            highlightthickness=0
        )
        dos_button.grid(row=3, column=0, pady=20)
        
        # 按鈕 hover 效果
        dos_button.bind("<Enter>", lambda e: dos_button.config(bg="#4caf50", fg="white"))
        dos_button.bind("<Leave>", lambda e: dos_button.config(bg="#cccccc", fg="black"))





    def on_tab_changed(self, event):


        # 獲取當前選中的分頁


        selected_tab = self.notebook.select()


        tab_text = self.notebook.tab(selected_tab, "text")


        


        # 根據分頁切換處理資源


        if tab_text == 'DUT 控制':


            if hasattr(self, 'dut_ui'):


                self.dut_ui.activate()


        elif tab_text == '治具控制':


            # 治具控制分頁的處理邏輯


            if hasattr(self, 'fixture_ui'):


                # 更新治具設定並刷新串口


                self.update_fixture_settings()


                if hasattr(self.fixture_ui, 'refresh_ports'):


                    self.fixture_ui.refresh_ports()


        elif tab_text == '使用說明':


            # 使用說明分頁的處理邏輯


            pass


        elif tab_text == '設定':


            # 設定分頁的處理邏輯


            if hasattr(self, 'settings_ui'):


                print(f"DEBUG: settings_ui type: {type(self.settings_ui)}")


                print(f"DEBUG: settings_ui dir: {dir(self.settings_ui)}")


                try:


                    self.settings_ui.activate()


                except AttributeError:


                    print("[DEBUG] settings_ui 沒有 activate 方法，跳過。")


                    pass





    def get_dut_settings(self):


        # 假設 self.dut_frame 內有 SerialUI 或相關元件


        if hasattr(self, 'dut_ui') and hasattr(self.dut_ui, 'get_settings'):


            return self.dut_ui.get_settings()


        # 若無，請根據你的 DUT 分頁元件組合自行組 dict


        return {}





    def get_fixture_settings(self):


        # 假設 self.fixture_frame 內有 FixtureFrame 或相關元件


        if hasattr(self, 'fixture_ui') and hasattr(self.fixture_ui, 'get_settings'):


            return self.fixture_ui.get_settings()


        # 若無，請根據你的 FIXTURE 分頁元件組合自行組 dict


        return {}





    def on_close(self):
        """處理關閉視窗事件"""
        try:
            # 如果有開啟的 DOS 視窗，關閉它
            if self.dos_process and self.dos_process.poll() is None:  # 檢查進程是否仍在運行
                try:
                    self.dos_process.terminate()  # 嘗試終止進程
                    print("[DEBUG] 關閉 DOS 視窗進程")
                except Exception as e:
                    print(f"[WARNING] 無法關閉 DOS 視窗進程：{e}")
            
            # 儲存設定
            from config_core import load_setup, save_setup
            setup = load_setup()
            
            # 確保保存最新的標籤頁名稱
            if hasattr(self, 'notebook'):
                # 獲取當前標籤頁名稱
                tab_names = setup.get('tab_names', {})
                for i in range(min(4, self.notebook.index('end'))):
                    tab_names[f'tab{i}'] = self.notebook.tab(i, 'text')
                setup['tab_names'] = tab_names
                print(f"[DEBUG] 關閉時保存標籤頁名稱：{tab_names}")
            
            # 保存設定
            save_setup(setup)
            
            # 關閉其他組件
            if hasattr(self, 'dut_ui') and hasattr(self.dut_ui, 'on_close'):
                self.dut_ui.on_close()
            
            # 如果有串口連接，斷開它
            try:
                if (hasattr(self, 'dut_ui') and 
                    hasattr(self.dut_ui, 'handlers') and 
                    hasattr(self.dut_ui.handlers, 'worker') and 
                    self.dut_ui.handlers.worker is not None):
                    
                    self.dut_ui.handlers.disconnect()
                    print("[DEBUG] 關閉時斷開串口連接")
            except Exception as e:
                print(f"[WARNING] 關閉時斷開連接失敗：{e}")
            
            # 關閉根窗口
            self.root.destroy()
            
        except Exception as e:
            print(f"[ERROR] 關閉視窗時發生錯誤：{e}")
            import traceback
            traceback.print_exc()
            
            # 即使出錯，也要嘗試關閉窗口
            try:
                self.root.destroy()
            except:
                pass





class SerialUI:
    """主應用程式的序列通訊 UI 框架"""
    def __init__(self, parent, root, highlight_keywords=None):
        """
        初始化 SerialUI。
        parent: 父級 tk 元件。
        root: 根 tk 視窗。
        highlight_keywords: 要高亮的關鍵字字典。
        """
        self.parent = parent
        self.root = root
        logging.debug(f"[DEBUG] SerialUI 初始化，highlight_keywords={highlight_keywords}")

        # 初始化設定和處理器
        self.worker = None
        self.config = config_core
        
        # 載入設定檔 - 確保每次都從磁碟讀取最新設定
        self.setup = self.config.load_setup()
        print(f"[DEBUG] SerialUI 初始化，載入設定: {self.setup}")
        
        # 初始化處理器和元件
        self.handlers = UIHandlers(self, self.setup, highlight_keywords=highlight_keywords)
        self.components = UIComponents(self, self.handlers, self.root)

        # 初始化樣式
        self.init_styles()

        # 使用集中式方法更新所有 UI 元件
        try:
            self.update_from_config()
        except Exception as e:
            print(f"[ERROR] 載入設定時出錯: {e}")
            import traceback
            traceback.print_exc()

        # 啟動時自動連線（如果設定了）
        if self.setup.get("DUT_Control", {}).get('Auto_Connect_on_Startup', False):
            self.handlers.auto_connect()


    def init_styles(self):


        style = ttk.Style()


        # 設定進度條樣式


        style.configure("blue.Horizontal.TProgressbar",


                      foreground='blue',


                      background='blue')


        style.configure("gray.Horizontal.TProgressbar",


                      foreground='#d9d9d9',


                      background='#d9d9d9')


        # 設定 Frame 樣式


        style.configure("Main.TFrame",


                      background="white")


        # 設定 Label 樣式


        style.configure("Main.TLabel",


                      background="white",


                      foreground="black")


        # 設定 Labelframe 樣式


        style.configure("Main.TLabelframe",


                      background="white",


                      foreground="black")


        style.configure("Main.TLabelframe.Label",


                      background="white",


                      foreground="black")





    def activate(self):


        """當分頁被選中時調用"""


        # 更新串口列表


        self.handlers.refresh_com_ports()


        # 其他激活操作...





    def on_close(self):


        """程式關閉時保存所有設定"""


        try:


            print("[DEBUG] SerialUI.on_close: 程式關閉，正在保存設定...")


            


            # 收集當前所有設定


            current_settings = self.get_settings_from_ui()


            print(f"[DEBUG] SerialUI.on_close: 已收集UI設定: {list(current_settings.keys())}")


            


            # 保存 PanedWindow 分割位置


            try:


                if hasattr(self.components, 'main_frame'):


                    sash_position = self.components.main_frame.sashpos(0)


                    if sash_position > 0:  # 確保分割位置有效


                        current_settings['Pane_Sash_Position'] = str(sash_position)


                        print(f"[DEBUG] SerialUI.on_close: 保存分割位置: {sash_position}")


            except Exception as e:


                print(f"[DEBUG] SerialUI.on_close: 獲取分割位置失敗: {e}")


                import traceback


                traceback.print_exc()


            


            # 保存當前視窗大小


            try:


                width = self.root.winfo_width()


                height = self.root.winfo_height()


                if width > 100 and height > 100:  # 確保視窗大小有效


                    current_settings['Window_Width'] = str(width)


                    current_settings['Window_Height'] = str(height)


                    print(f"[DEBUG] SerialUI.on_close: 保存視窗大小: {width}x{height}")


            except Exception as e:


                print(f"[DEBUG] SerialUI.on_close: 獲取視窗大小失敗: {e}")


            


            # 讀取完整的 setup 資料


            full_setup = load_setup()
            
            # 獲取當前視窗標題 (不包含版本號)
            current_title = self.root.title()
            window_title = current_title
            if " V" in current_title:
                window_title = current_title.split(" V")[0]
            
            # 更新頂層和DUT_Control中的視窗標題
            full_setup['Window_Title'] = window_title
            print(f"[DEBUG] SerialUI.on_close: 保存頂層視窗標題: {window_title}")
            
            # 更新 DUT_Control 層的設定
            if 'DUT_Control' not in full_setup:
                full_setup['DUT_Control'] = {}
            
            # 確保DUT_Control中的Window_Title與頂層一致
            full_setup['DUT_Control']['Window_Title'] = window_title
            
            # 更新所有設定字段
            for key, value in current_settings.items():
                full_setup['DUT_Control'][key] = value
                print(f"[DEBUG] SerialUI.on_close: 保存設定 {key} = {value}")
            
            # 保存到檔案
            save_setup(full_setup)
            print(f"[DEBUG] SerialUI.on_close: 設定已保存到 setup.json")
            
            # 停止所有執行緒
            if hasattr(self, 'stop_event') and self.stop_event:
                self.stop_event.set()
                print("[DEBUG] SerialUI.on_close: 已停止所有執行緒")
                
            # 關閉程式
            self.root.destroy()
            
        except Exception as e:


            print(f'[ERROR] SerialUI.on_close: 關閉程式時發生錯誤: {e}')


            import traceback


            traceback.print_exc()


            # 即使發生錯誤也要關閉程式


            self.root.destroy()





    def get_settings_from_ui(self):


        """從 UI 元件獲取當前設定"""


        settings = {}


        c = self.components


        # 基本設定


        settings['Serial_COM_Port'] = c.combobox_com.get()


        settings['Command_Timeout_Seconds'] = c.entry_timeout.get()


        settings['Command_End_String'] = c.combobox_end.get()


        settings['UI_Font_Size'] = str(c.ui_font_scale.get())


        settings['Content_Font_Size'] = str(c.content_font_scale.get())


        settings['Default_IP_Address'] = c.entry_ip.get()


        settings['Last_Selected_Command_Section'] = c.section_var.get()


        


        # 可用結束字串


        try:


            settings['Available_End_Strings'] = list(c.combobox_end['values'])


        except Exception:


            settings['Available_End_Strings'] = ["root"]





        # 視窗大小


        settings['Window_Width'] = str(self.root.winfo_width())


        settings['Window_Height'] = str(self.root.winfo_height())




        
        # 自動執行


        if hasattr(c, 'auto_exec_var'):


            settings['Auto_Execute'] = c.auto_exec_var.get()


        else:


            settings['Auto_Execute'] = self.setup.get('Auto_Execute', False)


            


        return settings





    def get_settings(self):


        """回傳 DUT_Control 分頁所有設定"""


        return self.get_settings_from_ui()





    def reload_and_apply_settings(self):
        """重新載入並應用設定"""
        print("[DEBUG] Reloading and applying settings for DUT Control tab...")
        
        # 1. 重新載入設定
        from config_core import load_setup
        self.setup = load_setup()
        
        # 2. 刷新 COM 口列表
        if hasattr(self, 'handlers') and hasattr(self.handlers, 'refresh_com_ports'):
            self.handlers.refresh_com_ports()
        else:
            print("[WARNING] handlers 不存在或沒有 refresh_com_ports 方法")
        
        # 3. 使用集中式方法更新所有 UI 元件
        self.update_from_config()
        
        print("[DEBUG] DUT Control settings applied successfully.")
    
    def update_from_config(self):
        """集中管理所有 UI 元件的設定同步
        
        此方法負責將 setup.json 中的設定值同步到 UI 元件。
        當設定變更時，只需呼叫此方法即可更新所有相關 UI 元件。
        """
        c = self.components
        dut_setup = self.setup.get("DUT_Control", {})
        
        # 1. 更新 COM 口設定
        if hasattr(c, 'combobox_com'):
            com_port = dut_setup.get('Serial_COM_Port', '')
            if com_port and com_port in c.combobox_com['values']:
                c.combobox_com.set(com_port)
        
        # 2. 更新超時設定
        if hasattr(c, 'entry_timeout'):
            timeout = dut_setup.get('Command_Timeout_Seconds', '30')
            c.entry_timeout.delete(0, tk.END)
            c.entry_timeout.insert(0, timeout)
        
        # 3. 更新結束字串設定
        if hasattr(c, 'combobox_end'):
            # 先更新可用的結束字串列表
            end_strings = dut_setup.get('Available_End_Strings', ['root'])
            if isinstance(end_strings, str):
                try:
                    end_strings = json.loads(end_strings)
                except:
                    end_strings = ['root']
            c.combobox_end['values'] = end_strings
            
            # 再設定當前選中的結束字串
            end_string = dut_setup.get('Command_End_String', 'root')
            c.combobox_end.set(end_string)
        
        # 4. 更新 IP 地址設定
        if hasattr(c, 'entry_ip'):
            default_ip = dut_setup.get('Default_IP_Address', '192.168.11.143')
            c.entry_ip.delete(0, tk.END)
            c.entry_ip.insert(0, default_ip)
        
        # 5. 更新自動執行設定
        if hasattr(c, 'auto_exec_var'):
            auto_execute = dut_setup.get('Auto_Execute', False)
            c.auto_exec_var.set(auto_execute)
        
        # 6. 更新字體大小設定
        ui_font_size = int(dut_setup.get('UI_Font_Size', 12))
        content_font_size = int(dut_setup.get('Content_Font_Size', 12))
        
        # 更新 UI 元件字體
        if hasattr(c, 'ui_font_scale'):
            c.ui_font_scale.set(ui_font_size)
        
        # 更新內容字體
        if hasattr(c, 'content_font_scale'):
            c.content_font_scale.set(content_font_size)
        
        # 應用字體設定到樣式
        style = ttk.Style()
        style.configure('Main.TFrame.Label', font=('Microsoft JhengHei', ui_font_size))
        style.configure('Command.TRadiobutton', font=('Microsoft JhengHei', ui_font_size))
        
        # 更新文字輸出區域字體
        if hasattr(c, 'text_output'):
            c.text_output.config(font=('Microsoft JhengHei', content_font_size))
        
        # 7. 更新指令相關設定
        # 重新解析指令文件
        if hasattr(self.handlers, 'parse_commands_by_section'):
            self.commands_by_section = self.handlers.parse_commands_by_section()
            
            # 更新指令下拉選單
            if hasattr(c, 'update_cmd_list'):
                c.update_cmd_list()
                
            # 設定上次選擇的指令分類
            last_section = dut_setup.get('Last_Selected_Command_Section', '全部指令')
            if hasattr(c, 'section_var') and last_section in c.sections:
                c.section_var.set(last_section)
                c.update_cmd_list()  # 更新指令列表以匹配選定的分類


    def _safe_execute_command(self):
        """安全地在背景執行指令"""
        if self.worker and self.worker.is_alive():
            print("[DEBUG] 自動執行指令")
            self.handlers.on_execute()
        else:
            print("[ERROR] handlers 不存在或沒有 on_execute 方法")


# 若有 FixtureFrame 也在這裡加 get_settings


from FIXTURE.fixture13 import FixtureFrame





def fixtureframe_get_settings(self):


    data = {}


    data['COM'] = self.com_port_var.get()


    data['CMD'] = self.command_var.get()


    for cat, var in self.category_vars.items():


        data[cat] = var.get()


    data['FixtureFontSize'] = str(self._fixture_font_size)


    return data


FixtureFrame.get_settings = fixtureframe_get_settings