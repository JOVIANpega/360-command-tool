# ui_main.py - 主UI模組

## 檔案概述
這是主UI模組，負責創建和管理整個應用程式的圖形化使用者介面。包含標籤頁管理器、序列埠UI、設定管理等核心功能。

## 主要功能
- 標籤頁管理和切換
- 序列埠通訊介面
- 設定管理和同步
- 全域樣式管理
- 通知系統整合

## 程式碼結構

### 1. 導入模組和初始化

```python
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
    from ui_parts.ui_settings_tab import SettingsTab
except ImportError as e:
    print(f"導入模組失敗: {e}")
    sys.exit(1)
```

**說明：**
- 設定 UTF-8 編碼以支援中文字符
- 導入必要的標準庫和第三方模組
- 將當前目錄加入 Python 路徑以確保模組能正確導入
- 檢查和載入必要的配置檔案
- 導入自定義的UI模組

### 2. TabManager 類別定義

```python
class TabManager:
    def __init__(self, root, highlight_keywords=None):
        self.root = root
        # 將自己設置為root的tab_manager屬性，供其他元件使用
        self.root.tab_manager = self

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
```

**說明：**
- 繼承自 `object`，作為主要的標籤頁管理器
- 初始化根窗口和標籤頁管理器
- 設置全域樣式和主內容框架
- 創建 Notebook 用於管理多個標籤頁

### 3. 全域樣式初始化

```python
def init_global_styles(self):
    """初始化全域樣式"""
    style = ttk.Style()
    
    # 設置主題
    try:
        style.theme_use('clam')
    except:
        try:
            style.theme_use('default')
        except:
            pass

    # 定義自定義樣式
    style.configure('Title.TLabel', font=('Microsoft JhengHei UI', 12, 'bold'))
    style.configure('Subtitle.TLabel', font=('Microsoft JhengHei UI', 10, 'bold'))
    style.configure('Normal.TLabel', font=('Microsoft JhengHei UI', 9))
    style.configure('Small.TLabel', font=('Microsoft JhengHei UI', 8))
    
    # 按鈕樣式
    style.configure('Accent.TButton', 
                   background='#0078d4', 
                   foreground='white',
                   font=('Microsoft JhengHei UI', 9, 'bold'))
    
    # 框架樣式
    style.configure('Card.TFrame', relief='solid', borderwidth=1)
```

**說明：**
- 初始化 ttk 樣式系統
- 設置預設主題（clam 或 default）
- 定義自定義樣式用於標題、按鈕、框架等
- 使用微軟正黑體字體以支援中文顯示

### 4. 標籤頁初始化

```python
def init_dut_tab(self):
    """初始化 DUT 控制分頁"""
    # 初始化 DUT 控制分頁
    self.dut_ui = SerialUI(self.notebook, self.root, self.highlight_keywords)
    self.notebook.add(self.dut_ui, text="DUT 控制")

def init_fixture_tab(self):
    """初始化治具控制分頁"""
    # 初始化治具控制分頁
    from ui_parts.ui_components import FixtureFrame
    self.fixture_ui = FixtureFrame(self.notebook, self.root, self.highlight_keywords)
    self.notebook.add(self.fixture_ui, text="治具控制")

def init_manual_tab(self):
    """初始化手動輸入指令分頁"""
    # 初始化手動輸入指令分頁
    from ui_parts.ui_manual_command import ManualCommandUI
    self.manual_ui = ManualCommandUI(self.notebook, self.root, self.highlight_keywords)
    self.notebook.add(self.manual_ui, text="手動輸入指令")

def init_settings_tab(self):
    """初始化設定分頁"""
    # 初始化設定分頁
    self.settings_ui = SettingsTab(self.notebook, on_save_callback=self.on_setting_changed)
    self.notebook.add(self.settings_ui, text="設定")

def init_dos_tab(self):
    """初始化DOS工具分頁"""
    # 初始化DOS工具分頁
    from ui_parts.ui_dos_tab import DosTab
    self.dos_ui = DosTab(self.notebook, self.root)
    self.notebook.add(self.dos_ui, text="DOS 工具")
```

**說明：**
- 初始化各個標籤頁的UI元件
- 包含 DUT 控制、治具控制、手動輸入指令、設定、DOS 工具等標籤頁
- 每個標籤頁都有獨立的UI類別
- 支援關鍵字高亮功能

### 5. 標籤頁切換處理

```python
def on_tab_changed(self, event):
    """標籤頁切換事件處理"""
    # 獲取當前選中的分頁
    current_tab = self.notebook.select()
    tab_id = self.notebook.index(current_tab)
    
    # 根據標籤頁索引執行相應操作
    if tab_id == 0:  # DUT 控制
        if hasattr(self, 'dut_ui'):
            self.dut_ui.activate()
    elif tab_id == 1:  # 治具控制
        if hasattr(self, 'fixture_ui'):
            self.fixture_ui.activate()
    elif tab_id == 2:  # 手動輸入指令
        if hasattr(self, 'manual_ui'):
            self.manual_ui.activate()
    elif tab_id == 3:  # DOS 工具
        if hasattr(self, 'dos_ui'):
            self.dos_ui.activate()
    elif tab_id == 4:  # 設定
        if hasattr(self, 'settings_ui'):
            self.settings_ui.activate()
```

**說明：**
- 處理標籤頁切換事件
- 根據當前選中的標籤頁執行相應的激活操作
- 確保每個標籤頁都能正確響應切換事件

### 6. 設定管理

```python
def update_all_settings(self, settings_dict=None):
    """更新所有設定"""
    try:
        if settings_dict is None:
            settings_dict = load_setup()
        
        # 更新視窗標題
        self.update_window_title_from_setup(settings_dict)
        
        # 更新標籤頁名稱
        self.update_tab_names_from_settings()
        
        # 更新 DUT 設定
        if hasattr(self, 'dut_ui'):
            self.dut_ui.update_from_config()
        
        # 更新治具設定
        if hasattr(self, 'fixture_ui'):
            self.fixture_ui.update_from_config()
        
        # 更新手動輸入指令設定
        if hasattr(self, 'manual_ui'):
            self.manual_ui.update_from_config()
        
        # 更新啟動標籤
        self.update_startup_label_from_settings(settings_dict)
        
        # 同步字體設定
        self.sync_font_settings(settings_dict)
        
        # 同步通知設定
        self.sync_notification_settings(settings_dict)
        
        print("[DEBUG] 所有設定已更新")
        
    except Exception as e:
        print(f"[ERROR] 更新設定時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
```

**說明：**
- 統一管理所有設定的更新
- 包含視窗標題、標籤頁名稱、DUT設定、治具設定等
- 支援從設定檔案或字典更新設定
- 包含完整的錯誤處理

### 7. SerialUI 類別

```python
class SerialUI:
    def __init__(self, parent, root, highlight_keywords=None):
        super().__init__(parent)
        self.parent = parent
        self.root = root
        self.highlight_keywords = highlight_keywords or {}
        
        # 初始化序列埠相關變數
        self.serial_worker = None
        self.stop_event = threading.Event()
        
        # 初始化UI元件
        self.init_ui()
        self.init_styles()
        
        # 載入設定
        self.load_settings()

    def init_styles(self):
        """初始化樣式"""
        style = ttk.Style()
        
        # 定義自定義樣式
        style.configure('SerialUI.Title.TLabel', 
                       font=('Microsoft JhengHei UI', 12, 'bold'),
                       foreground='#2c3e50')
        
        style.configure('SerialUI.Subtitle.TLabel',
                       font=('Microsoft JhengHei UI', 10, 'bold'),
                       foreground='#34495e')
        
        style.configure('SerialUI.Normal.TLabel',
                       font=('Microsoft JhengHei UI', 9),
                       foreground='#2c3e50')
```

**說明：**
- 序列埠UI類別，負責序列埠通訊介面
- 初始化序列埠相關變數和UI元件
- 定義自定義樣式以提供一致的外觀
- 支援關鍵字高亮功能

### 8. 設定同步

```python
def sync_font_settings(self, setup):
    """同步字體設定"""
    try:
        # 獲取字體設定
        font_settings = setup.get('Font_Settings', {})
        
        # 更新全域字體設定
        if hasattr(self, 'dut_ui'):
            self.dut_ui.update_font_settings(font_settings)
        
        if hasattr(self, 'fixture_ui'):
            self.fixture_ui.update_font_settings(font_settings)
        
        if hasattr(self, 'manual_ui'):
            self.manual_ui.update_font_settings(font_settings)
        
        print("[DEBUG] 字體設定已同步")
        
    except Exception as e:
        print(f"[ERROR] 同步字體設定時發生錯誤: {e}")

def sync_notification_settings(self, setup):
    """同步通知設定"""
    try:
        # 獲取通知設定
        notification_settings = setup.get('Notification_Settings', {})
        
        # 更新通知設定
        if hasattr(self, 'dut_ui'):
            self.dut_ui.update_notification_settings(notification_settings)
        
        if hasattr(self, 'fixture_ui'):
            self.fixture_ui.update_notification_settings(notification_settings)
        
        print("[DEBUG] 通知設定已同步")
        
    except Exception as e:
        print(f"[ERROR] 同步通知設定時發生錯誤: {e}")
```

**說明：**
- 同步字體設定到各個UI元件
- 同步通知設定到各個UI元件
- 確保設定的一致性
- 包含完整的錯誤處理

### 9. 資源清理

```python
def on_close(self):
    """程式關閉時的清理工作"""
    try:
        # 停止序列埠工作器
        if hasattr(self, 'dut_ui') and hasattr(self.dut_ui, 'stop_serial_worker'):
            self.dut_ui.stop_serial_worker()
        
        # 停止治具工作器
        if hasattr(self, 'fixture_ui') and hasattr(self.fixture_ui, 'stop_worker'):
            self.fixture_ui.stop_worker()
        
        # 關閉 DOS 進程
        if hasattr(self, 'dos_process') and self.dos_process:
            try:
                self.dos_process.terminate()
                self.dos_process.wait(timeout=5)
            except:
                try:
                    self.dos_process.kill()
                except:
                    pass
        
        # 保存設定
        try:
            self.save_all_settings()
        except Exception as e:
            print(f"[WARNING] 保存設定時發生錯誤: {e}")
        
        print("[DEBUG] 程式關閉清理完成")
        
    except Exception as e:
        print(f"[ERROR] 程式關閉時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
```

**說明：**
- 程式關閉時執行清理工作
- 停止所有工作器和進程
- 保存所有設定
- 確保資源正確釋放

## 重要設計原則

1. **模組化設計**：將不同功能分離到不同的UI類別
2. **設定管理**：統一的設定管理和同步機制
3. **資源管理**：正確的資源清理和釋放
4. **錯誤處理**：完整的錯誤處理機制
5. **用戶體驗**：一致的外觀和操作體驗

## 依賴關係

- `tkinter`：GUI框架
- `config_core`：配置管理
- `serial_worker`：序列埠通訊
- `ui_parts`：UI元件模組

## 使用方式

1. **創建主UI**：
   ```python
   root = tk.Tk()
   app = TabManager(root, highlight_keywords)
   ```

2. **更新設定**：
   ```python
   app.update_all_settings(settings_dict)
   ```

3. **切換標籤頁**：
   ```python
   app.notebook.select(0)  # 切換到第一個標籤頁
   ```

4. **程式關閉**：
   ```python
   app.on_close()
   ```

## 注意事項

- 確保所有必要的模組都已正確導入
- 注意資源的清理和釋放
- 處理設定同步的錯誤情況
- 確保UI元件的一致性 