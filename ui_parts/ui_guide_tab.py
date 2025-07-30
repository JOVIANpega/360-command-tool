# -*- coding: utf-8 -*-
"""
使用說明標籤頁模組
提供嵌入式HTML顯示功能
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import webbrowser
import subprocess
import re

class GuideTab:
    """使用說明標籤頁類"""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.guide_text = None
        self.dos_process = None
        self.init_guide_tab()
    
    def init_guide_tab(self):
        """初始化使用說明分頁 - 嵌入式HTML顯示"""
        self.parent_frame.grid_rowconfigure(0, weight=1)
        self.parent_frame.grid_columnconfigure(0, weight=1)
        
        # 創建主框架
        guide_main_frame = ttk.Frame(self.parent_frame)
        guide_main_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        guide_main_frame.grid_rowconfigure(1, weight=1)
        guide_main_frame.grid_columnconfigure(0, weight=1)
        
        # 獲取版本號
        try:
            from config_utils import get_app_version
            app_version = get_app_version()
        except:
            app_version = "1.7.1"
        
        # 標題框架
        title_frame = ttk.Frame(guide_main_frame)
        title_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        title_frame.grid_columnconfigure(0, weight=1)
        
        # 標題
        title_label = ttk.Label(
            title_frame,
            text=f"VALO360 指令通 V{app_version} 使用說明",
            font=('Microsoft JhengHei UI', 16, 'bold'),
            style="TLabel"
        )
        title_label.grid(row=0, column=0)
        
        # 創建HTML內容顯示區域
        content_frame = ttk.LabelFrame(guide_main_frame, text="使用說明內容", padding=10)
        content_frame.grid(row=1, column=0, sticky='nsew', pady=(0, 10))
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # 創建滾動文本區域
        self.guide_text = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            font=('Microsoft JhengHei UI', 11),
            bg='#FAFAFA',
            fg='#333333',
            relief='flat',
            borderwidth=1,
            state='disabled'
        )
        self.guide_text.grid(row=0, column=0, sticky='nsew')
        
        # 載入使用說明內容
        self.load_guide_content()
        
        # 按鈕區域
        button_frame = ttk.Frame(guide_main_frame)
        button_frame.grid(row=2, column=0, pady=10)
        
        # 重新載入按鈕
        reload_button = ttk.Button(
            button_frame,
            text="重新載入內容",
            command=self.load_guide_content
        )
        reload_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 開啟外部檔案按鈕
        external_button = ttk.Button(
            button_frame,
            text="開啟外部HTML檔案",
            command=self.open_external_guide
        )
        external_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加「開啟 DOS 視窗」按鈕
        dos_button = ttk.Button(
            button_frame,
            text="開啟 DOS 視窗",
            command=self.open_dos_window
        )
        dos_button.pack(side=tk.LEFT)
    
    def load_guide_content(self):
        """載入使用說明內容到文本區域"""
        try:
            # 獲取檔案路徑
            if getattr(sys, 'frozen', False):
                # 打包後的環境
                base_dir = os.path.dirname(sys.executable)
            else:
                # 開發環境
                base_dir = os.path.dirname(os.path.abspath(__file__))
                base_dir = os.path.dirname(base_dir)  # 回到上一層目錄
            
            # 嘗試載入HTML文件
            html_file = os.path.join(base_dir, "VALO360 指令通使用指南.html")
            
            if os.path.exists(html_file):
                content = self._load_html_content(html_file)
            else:
                # 如果HTML文件不存在，載入文本版本的使用說明
                content = self._load_text_guide()
            
            # 更新文本區域
            self.guide_text.config(state='normal')
            self.guide_text.delete(1.0, tk.END)
            self.guide_text.insert(1.0, content)
            self.guide_text.config(state='disabled')
            
        except Exception as e:
            error_content = f"載入使用說明時發生錯誤：{str(e)}\n\n請檢查檔案是否存在或聯繫技術支援。"
            self.guide_text.config(state='normal')
            self.guide_text.delete(1.0, tk.END)
            self.guide_text.insert(1.0, error_content)
            self.guide_text.config(state='disabled')
    
    def _load_html_content(self, html_file):
        """從HTML文件載入內容並轉換為純文本"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 簡單的HTML標籤移除（基本的文本提取）
            # 移除HTML標籤
            text_content = re.sub(r'<[^>]+>', '', html_content)
            
            # 解碼HTML實體
            text_content = text_content.replace('&nbsp;', ' ')
            text_content = text_content.replace('&lt;', '<')
            text_content = text_content.replace('&gt;', '>')
            text_content = text_content.replace('&amp;', '&')
            
            # 清理多餘的空白行
            lines = text_content.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    cleaned_lines.append(line)
                elif cleaned_lines and cleaned_lines[-1] != '':
                    cleaned_lines.append('')
            
            return '\n'.join(cleaned_lines)
            
        except Exception as e:
            return f"無法載入HTML內容：{str(e)}"
    
    def _load_text_guide(self):
        """載入文本版本的使用說明"""
        return """VALO360 指令通 使用說明

=== 基本功能 ===

1. DUT 控制
   - 選擇COM口連接設備
   - 執行AT指令和系統指令
   - 查看執行結果和日誌

2. 治具控制
   - 控制測試治具
   - 執行測試序列
   - 監控測試狀態

3. 設定管理
   - 調整字體大小
   - 設定COM口參數
   - 配置指令超時時間
   - 自訂視窗標題

=== 使用步驟 ===

1. 啟動程式後，先到「設定」標籤頁配置基本參數
2. 在「DUT 控制」標籤頁選擇正確的COM口
3. 選擇要執行的指令或輸入自訂指令
4. 點擊「執行」按鈕開始執行
5. 在輸出區域查看執行結果

=== 注意事項 ===

- 確保設備已正確連接到指定的COM口
- 執行指令前請確認設備狀態
- 如遇到問題，請檢查COM口設定和設備連接
- 可在設定頁面調整字體大小以獲得更好的顯示效果

=== 技術支援 ===

如有任何問題，請聯繫技術支援團隊。

版本：1.7.1
更新日期：2025-07-30"""
    
    def open_external_guide(self):
        """開啟外部HTML檔案"""
        try:
            # 獲取檔案路徑
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
            else:
                exe_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            guide_file = os.path.join(exe_dir, "VALO360 指令通使用指南.html")
            
            if os.path.exists(guide_file):
                # 使用預設瀏覽器開啟
                webbrowser.open(f"file:///{guide_file.replace(os.sep, '/')}")
            else:
                messagebox.showinfo("提示", "外部HTML檔案不存在，請查看上方的內嵌說明內容。")
        except Exception as e:
            messagebox.showerror("錯誤", f"開啟使用指南時發生錯誤：\n{str(e)}")
    
    def open_dos_window(self):
        """開啟DOS視窗"""
        try:
            # 檢查是否已經開啟 DOS 視窗
            if self.dos_process is None or self.dos_process.poll() is not None:
                # 如果沒有開啟或已關閉，則開啟新的 DOS 視窗
                self.dos_process = subprocess.Popen(["cmd"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                print("[DEBUG] 已開啟 DOS 視窗")
            else:
                # 如果已經開啟，則顯示提示訊息
                messagebox.showinfo("提示", "DOS 視窗已經開啟")
        except Exception as e:
            messagebox.showerror("錯誤", f"開啟DOS視窗時發生錯誤：\n{str(e)}")
