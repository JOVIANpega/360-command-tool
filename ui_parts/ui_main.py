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


        self.root.grid_columnconfigure(0, weight=1)


        


        # 初始化全局樣式


        self.init_global_styles()


        


        self.notebook = ttk.Notebook(root)


        self.notebook.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)


        


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


        


        # 初始化分頁內容


        self.init_dut_tab()


        self.init_fixture_tab()


        self.init_guide_tab()  # 改名為 init_guide_tab
        self.init_settings_tab() # 新增

        
        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        

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
        """根據設定檔中的區段標題更新 DUT 控制頁面的按鈕"""
        try:
            # 檢查 dut_ui 和 components 是否存在
            if not hasattr(self, 'dut_ui') or not hasattr(self.dut_ui, 'components'):
                print("[ERROR] dut_ui 或 components 不存在，無法更新按鈕")
                return
                
            # 獲取設定檔中的區段標題
            section_titles = self.dut_ui.setup.get("DUT_Control", {}).get("Section_Titles", [])
            print(f"[DEBUG] update_dut_buttons: 從設定檔中獲取的區段標題: {section_titles}")
            
            # 如果設定檔中沒有區段標題，嘗試從指令文件中讀取
            if not section_titles:
                print("[DEBUG] update_dut_buttons: 設定檔中沒有區段標題，嘗試從指令文件中讀取")
                
                # 從設定中獲取指令檔案路徑
                command_file_path = self.dut_ui.setup.get("DUT_Control", {}).get("Command_File_Path", "")
                print(f"[DEBUG] update_dut_buttons: 指令檔案路徑: {command_file_path}")
                
                if command_file_path and os.path.exists(command_file_path):
                    print(f"[DEBUG] update_dut_buttons: 使用設定中的指令檔案: {command_file_path}")
                    try:
                        section_titles = []
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
                    print(f"[DEBUG] update_dut_buttons: 指令檔案不存在或未指定，使用預設值")
            
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

    def update_all_settings(self):
        """Update both DUT and Fixture settings."""
        self.update_dut_settings()
        self.update_fixture_settings()
        self.update_window_title()  # 更新視窗標題
        self.update_tab_names()    # 更新標籤頁名稱

    


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
            if hasattr(self, 'dut_ui') and hasattr(self.dut_ui, 'handlers') and self.dut_ui.handlers.worker:
                try:
                    self.dut_ui.handlers.disconnect()
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