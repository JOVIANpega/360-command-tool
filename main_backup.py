# -*- coding: utf-8 -*-
"""
360指令通 主程式
一個基於 Python tkinter 開發的網路工具和串口通訊工具

主要功能：
- DUT控制分頁：Ping 網路連通性測試、串口通訊監控
- 治具控制分頁：治具設備控制和測試
- 使用說明分頁：HTML使用指南開啟
- 設定參數保存和管理

作者：Jovian
版本：v1.12
"""

import tkinter as tk
from tkinter import ttk
import threading
import json
import os
import sys
import webbrowser
from tkinter import messagebox

# 添加當前目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import load_setup, save_setup, create_default_files
from ui_handlers import UIHandlers

class Main_Application:
    def __init__(self):
        """初始化主應用程式"""
        self.root = tk.Tk()
        self.root.title("VALO360 指令通 v1.12")
        
        # 設定視窗大小和位置（置中顯示）
        self.setup_window()
        
        # 載入設定
        self.setup = load_setup()
        
        # 創建預設檔案
        create_default_files()
        
        # 初始化事件
        self.stop_event = threading.Event()
        self.guide_window = None
        
        # 初始化 UI 組件
        self.init_ui_components()
        
        # 初始化事件處理器
        self.handlers = UIHandlers(self)
        
        # 設定視窗關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 使視窗可調整大小
        self.root.resizable(True, True)
        
    def setup_window(self):
        """設定視窗大小和位置"""
        width = int(self.setup.get('WindowWidth', '900')) if hasattr(self, 'setup') else 900
        height = int(self.setup.get('WindowHeight', '700')) if hasattr(self, 'setup') else 700
        
        # 計算置中位置
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def init_ui_components(self):
        """初始化 UI 組件"""
        # 創建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 設定網格權重
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # 創建分頁控制器
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # 創建三個分頁
        self.create_dut_control_tab()
        self.create_fixture_control_tab()
        self.create_manual_tab()
        
    def create_dut_control_tab(self):
        """創建DUT控制分頁"""
        dut_frame = ttk.Frame(self.notebook)
        self.notebook.add(dut_frame, text="DUT控制")
        
        # 設定框架權重
        dut_frame.grid_rowconfigure(0, weight=1)
        dut_frame.grid_columnconfigure(0, weight=1)
        
        # 創建主要內容區域
        content_frame = ttk.Frame(dut_frame)
        content_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        content_frame.grid_rowconfigure(2, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # COM口設定區域
        com_frame = ttk.LabelFrame(content_frame, text="COM口設定")
        com_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(com_frame, text="COM口:").grid(row=0, column=0, padx=5, pady=5)
        self.com_var = tk.StringVar()
        com_combo = ttk.Combobox(com_frame, textvariable=self.com_var, width=10)
        com_combo.grid(row=0, column=1, padx=5, pady=5)
        
        refresh_btn = self.create_hover_button(com_frame, "刷新", 0, 2, width=8)
        
        # 指令控制區域
        cmd_frame = ttk.LabelFrame(content_frame, text="指令控制")
        cmd_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(cmd_frame, text="指令分類:").grid(row=0, column=0, padx=5, pady=5)
        self.cmd_category_var = tk.StringVar()
        cmd_category_combo = ttk.Combobox(cmd_frame, textvariable=self.cmd_category_var, 
                                        values=["全部指令", "單板指令", "整機指令", "出貨指令"])
        cmd_category_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(cmd_frame, text="指令:").grid(row=1, column=0, padx=5, pady=5)
        self.cmd_var = tk.StringVar()
        cmd_combo = ttk.Combobox(cmd_frame, textvariable=self.cmd_var, width=30)
        cmd_combo.grid(row=1, column=1, padx=5, pady=5)
        
        execute_btn = self.create_hover_button(cmd_frame, "執行指令", 1, 2, width=10)
        
        # Ping測試區域
        ping_frame = ttk.LabelFrame(cmd_frame, text="Ping測試")
        ping_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
        ttk.Label(ping_frame, text="IP地址:").grid(row=0, column=0, padx=5, pady=5)
        self.ip_var = tk.StringVar()
        ip_entry = ttk.Entry(ping_frame, textvariable=self.ip_var, width=15)
        ip_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ping_btn = self.create_hover_button(ping_frame, "Ping", 0, 2, width=8)
        
        # 回應顯示區域
        response_frame = ttk.LabelFrame(content_frame, text="回應內容")
        response_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        response_frame.grid_rowconfigure(0, weight=1)
        response_frame.grid_columnconfigure(0, weight=1)
        
        # 創建文字顯示區域
        self.response_text = tk.Text(response_frame, wrap=tk.WORD, font=('Consolas', 10))
        scrollbar = ttk.Scrollbar(response_frame, orient="vertical", command=self.response_text.yview)
        self.response_text.configure(yscrollcommand=scrollbar.set)
        
        self.response_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 按鈕區域
        button_frame = ttk.Frame(content_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        clear_btn = self.create_hover_button(button_frame, "清空回應", 0, 0, width=10)
        backup_btn = self.create_hover_button(button_frame, "備份Log", 0, 1, width=10)
        
    def create_fixture_control_tab(self):
        """創建治具控制分頁"""
        fixture_frame = ttk.Frame(self.notebook)
        self.notebook.add(fixture_frame, text="治具控制")
        
        # 設定框架權重
        fixture_frame.grid_rowconfigure(0, weight=1)
        fixture_frame.grid_columnconfigure(0, weight=1)
        
        # 創建主要內容區域
        content_frame = ttk.Frame(fixture_frame)
        content_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        content_frame.grid_rowconfigure(2, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # 治具操作提示區域
        tip_frame = ttk.LabelFrame(content_frame, text="治具操作區")
        tip_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        tip_label = tk.Label(tip_frame, text="⚠️ 治具控制提示：請確認治具設備已正確連接，選擇對應的COM口和測試類別", 
                           bg='#fff3cd', fg='#856404', font=('TkDefaultFont', 10), 
                           wraplength=600, justify='left')
        tip_label.pack(fill='x', padx=10, pady=10)
        
        # 治具串口設定區域
        fixture_com_frame = ttk.LabelFrame(content_frame, text="治具串口設定")
        fixture_com_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(fixture_com_frame, text="治具COM口:").grid(row=0, column=0, padx=5, pady=5)
        self.fixture_com_var = tk.StringVar()
        fixture_com_combo = ttk.Combobox(fixture_com_frame, textvariable=self.fixture_com_var, width=10)
        fixture_com_combo.grid(row=0, column=1, padx=5, pady=5)
        
        fixture_refresh_btn = self.create_hover_button(fixture_com_frame, "刷新", 0, 2, width=8)
        
        # 測試類別選擇
        ttk.Label(fixture_com_frame, text="測試類別:").grid(row=1, column=0, padx=5, pady=5)
        
        category_frame = ttk.Frame(fixture_com_frame)
        category_frame.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        
        self.function_var = tk.BooleanVar()
        self.mb_var = tk.BooleanVar()
        self.original_var = tk.BooleanVar()
        
        ttk.Checkbutton(category_frame, text="FUNCTION", variable=self.function_var).pack(side='left', padx=5)
        ttk.Checkbutton(category_frame, text="MB", variable=self.mb_var).pack(side='left', padx=5)
        ttk.Checkbutton(category_frame, text="原始的指令", variable=self.original_var).pack(side='left', padx=5)
        
        # 治具指令控制
        ttk.Label(fixture_com_frame, text="治具指令:").grid(row=2, column=0, padx=5, pady=5)
        self.fixture_cmd_var = tk.StringVar()
        fixture_cmd_combo = ttk.Combobox(fixture_com_frame, textvariable=self.fixture_cmd_var, width=30)
        fixture_cmd_combo.grid(row=2, column=1, padx=5, pady=5)
        
        fixture_execute_btn = self.create_hover_button(fixture_com_frame, "發送治具控制指令", 2, 2, width=15)
        
        # 治具回應顯示區域
        fixture_response_frame = ttk.LabelFrame(content_frame, text="治具回應內容")
        fixture_response_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        fixture_response_frame.grid_rowconfigure(0, weight=1)
        fixture_response_frame.grid_columnconfigure(0, weight=1)
        
        # 創建治具文字顯示區域
        self.fixture_response_text = tk.Text(fixture_response_frame, wrap=tk.WORD, font=('Consolas', 10))
        fixture_scrollbar = ttk.Scrollbar(fixture_response_frame, orient="vertical", command=self.fixture_response_text.yview)
        self.fixture_response_text.configure(yscrollcommand=fixture_scrollbar.set)
        
        self.fixture_response_text.grid(row=0, column=0, sticky="nsew")
        fixture_scrollbar.grid(row=0, column=1, sticky="ns")
        
    def create_manual_tab(self):
        """創建使用說明分頁"""
        manual_frame = ttk.Frame(self.notebook)
        self.notebook.add(manual_frame, text="使用說明")
        
        # 設定框架權重
        manual_frame.grid_rowconfigure(0, weight=1)
        manual_frame.grid_columnconfigure(0, weight=1)
        
        # 創建主要內容區域
        content_frame = ttk.Frame(manual_frame)
        content_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # 標題區域
        title_frame = ttk.Frame(content_frame)
        title_frame.grid(row=0, column=0, pady=20)
        
        title_label = ttk.Label(title_frame, text="📖 VALO360 指令通使用說明", 
                               font=('TkDefaultFont', 16, 'bold'))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="點擊下方按鈕開啟完整的HTML使用指南", 
                                  font=('TkDefaultFont', 12))
        subtitle_label.pack(pady=10)
        
        # 按鈕區域
        button_frame = ttk.Frame(content_frame)
        button_frame.grid(row=1, column=0)
        
        # 創建使用說明按鈕（符合 hover style 要求）
        manual_btn = self.create_hover_button(button_frame, "使用說明", 0, 0, width=15, height=3)
        manual_btn.config(command=self.open_html_manual)
        
        # 說明文字
        info_frame = ttk.Frame(content_frame)
        info_frame.grid(row=2, column=0, pady=20)
        
        info_text = """
        📋 功能說明：
        • 點擊「使用說明」按鈕會開啟詳細的HTML使用指南
        • 使用指南包含完整的操作說明、故障排除和快捷鍵說明
        • 支援圖片、樣式和互動功能，提供更好的閱讀體驗
        • 文件位於EXE同目錄下：VALO360 指令通使用指南.html
        """
        
        info_label = ttk.Label(info_frame, text=info_text, 
                              font=('TkDefaultFont', 10), justify='left')
        info_label.pack()
        
    def create_hover_button(self, parent, text, row, col, width=10, height=2):
        """創建具有 hover 效果的按鈕"""
        btn = tk.Button(parent, text=text, 
                       bg='#d9d9d9', fg='black',  # 預設：灰色底黑色文字
                       font=('TkDefaultFont', 10),
                       width=width, height=height,
                       relief='raised', bd=2)
        btn.grid(row=row, column=col, padx=5, pady=5)
        
        # 綁定 hover 事件
        btn.bind("<Enter>", lambda e: btn.config(bg='#006400', fg='black'))  # 深綠色底黑色文字
        btn.bind("<Leave>", lambda e: btn.config(bg='#d9d9d9', fg='black'))  # 恢復灰色底黑色文字
        
        return btn
    
    def open_html_manual(self):
        """開啟HTML使用指南"""
        try:
            # 獲取EXE所在目錄
            if getattr(sys, 'frozen', False):
                # 如果是打包後的EXE
                exe_dir = os.path.dirname(sys.executable)
            else:
                # 如果是Python腳本
                exe_dir = os.path.dirname(os.path.abspath(__file__))
            
            # HTML文件路徑
            html_file = os.path.join(exe_dir, "VALO360 指令通使用指南.html")
            
            # 檢查文件是否存在
            if os.path.exists(html_file):
                # 使用系統預設瀏覽器開啟HTML文件
                webbrowser.open(f"file:///{html_file.replace(os.sep, '/')}")
                messagebox.showinfo("提示", "使用指南已在瀏覽器中開啟")
            else:
                messagebox.showerror("錯誤", f"找不到使用指南文件：\n{html_file}")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"開啟使用指南時發生錯誤：\n{str(e)}")
        
    def on_closing(self):
        """視窗關閉事件處理"""
        # 保存視窗大小
        self.setup['WindowWidth'] = str(self.root.winfo_width())
        self.setup['WindowHeight'] = str(self.root.winfo_height())
        save_setup(self.setup)
        
        # 設定停止事件
        self.stop_event.set()
        
        # 關閉說明視窗
        if self.guide_window and self.guide_window.winfo_exists():
            self.guide_window.destroy()
            
        # 關閉主視窗
        self.root.destroy()
        
    def run(self):
        """啟動應用程式"""
        self.root.mainloop()

def main():
    """主函數"""
    try:
        app = Main_Application()
        app.run()
    except Exception as e:
        print(f"應用程式啟動錯誤: {e}")
        input("按 Enter 鍵退出...")

if __name__ == "__main__":
    main() 