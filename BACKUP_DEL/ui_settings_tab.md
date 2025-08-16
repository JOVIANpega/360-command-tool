# ui_settings_tab.py - 設定標籤頁

## 檔案概述
這是設定標籤頁的UI模組，負責提供應用程式的所有設定介面，包括基本設定、DUT控制設定、標籤頁名稱設定等。使用PanedWindow提供可調整的左右分隔佈局。

## 主要功能
- 應用程式基本設定管理
- DUT控制設定配置
- 標籤頁名稱自訂
- 手動輸入指令設定
- 即時設定更新和保存

## 程式碼結構

### 1. 導入模組和初始化

```python
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import json

# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from config_core import load_setup, save_setup
from ui_parts.tooltip import ToolTipManager
```

**說明：**
- 設定 UTF-8 編碼以支援中文字符
- 導入必要的 tkinter 元件和標準庫
- 將當前目錄加入 Python 路徑以確保模組能正確導入
- 導入配置核心模組和工具提示管理器

### 2. SettingsTab 類別定義

```python
class SettingsTab(ttk.Frame):
    def __init__(self, parent, on_save_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.parent_frame = self  # 設置parent_frame屬性供字體更新使用
        self.on_save_callback = on_save_callback
        self.setup_data = load_setup()
        self.vars = {}
        
        # 字體大小追蹤變數 (用於即時更新)
        self.font_size_trace_active = False
        
        # 初始化 ToolTip 管理器
        try:
            self.tooltip_manager = ToolTipManager()
        except Exception as e:
            print(f"初始化 ToolTip 管理器失敗: {e}")
            self.tooltip_manager = None
        
        self.create_widgets()
        self.setup_tooltips()
```

**說明：**
- 繼承自 `ttk.Frame` 以提供現代化的UI外觀
- 初始化父元件、回調函數、設定資料等屬性
- 設置字體大小追蹤變數用於即時更新
- 初始化工具提示管理器
- 創建UI元件和設置工具提示

### 3. UI元件創建

```python
def create_widgets(self):
    # 創建主容器，使用 PanedWindow 來提供可調整的左右分隔
    main_container = ttk.PanedWindow(self, orient='horizontal')
    main_container.pack(fill='both', expand=True, padx=10, pady=10)
    
    # 左側容器
    left_frame = ttk.Frame(main_container)
    main_container.add(left_frame, weight=1)
    
    # 右側容器
    right_frame = ttk.Frame(main_container)
    main_container.add(right_frame, weight=1)
    
    # 設定分隔位置為中間
    main_container.sashpos(0, 400)
```

**說明：**
- 使用 `PanedWindow` 創建可調整的左右分隔佈局
- 左側放置基本設定和DUT控制設定
- 右側放置標籤頁名稱設定和手動輸入指令設定
- 設定初始分隔位置為中間

### 4. 應用程式基本設定

```python
# 應用程式基本設定
basic_frame = ttk.LabelFrame(left_container, text="應用程式基本設定", padding=(10, 4))
basic_frame.pack(fill='x', pady=(0, 8))
basic_frame.columnconfigure(1, weight=1)

# 獲取版本號（用於後面的版本與路徑資訊區塊）
current_version = self.setup_data.get("version", "1.7.1")
self.vars["version"] = tk.StringVar(value=current_version)
print(f"[DEBUG] 設定頁面初始化版本號: {current_version}")

# 視窗標題 - width=40，最多50個字元
ttk.Label(basic_frame, text="視窗標題 (最多50字元):").grid(row=0, column=0, sticky="w", pady=4)
self.vars["Window_Title"] = tk.StringVar(value=self.setup_data.get("Window_Title", "指令通"))
self.title_entry = ttk.Entry(basic_frame, textvariable=self.vars["Window_Title"], width=40)
self.title_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)

# 綁定字元限制檢查
self.vars["Window_Title"].trace('w', self.on_title_changed)

# 添加字元計數標籤
self.title_count_label = ttk.Label(basic_frame, text=f"({len(self.vars['Window_Title'].get())}/50)",
                                  font=('Microsoft JhengHei UI', 9), foreground='gray')
self.title_count_label.grid(row=0, column=2, sticky="w", padx=(5, 0), pady=4)
```

**說明：**
- 創建應用程式基本設定區塊
- 包含版本號、視窗標題、指令傳輸方式等設定
- 視窗標題有50字元限制，並提供即時字元計數
- 使用 `trace` 方法綁定字元限制檢查

### 5. 視窗大小設定

```python
# 視窗大小 - 視窗寬度 width=20
size_frame = ttk.Frame(basic_frame)
size_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=4)
size_frame.columnconfigure(1, weight=1)
size_frame.columnconfigure(3, weight=1)

ttk.Label(size_frame, text="視窗寬度:").grid(row=0, column=0, sticky="w")
self.vars["Window_Width"] = tk.StringVar(value=self.setup_data.get("Window_Width", "1536"))
self.width_entry = ttk.Entry(size_frame, textvariable=self.vars["Window_Width"], width=20)
self.width_entry.grid(row=0, column=1, sticky="w", padx=(5, 10))

ttk.Label(size_frame, text="高度:").grid(row=0, column=2, sticky="w")
self.vars["Window_Height"] = tk.StringVar(value=self.setup_data.get("Window_Height", "793"))
self.height_entry = ttk.Entry(size_frame, textvariable=self.vars["Window_Height"], width=20)
self.height_entry.grid(row=0, column=3, sticky="w", padx=(5, 0))

# 添加同步當前視窗大小按鈕
sync_button = ttk.Button(size_frame, text="同步當前", command=self.sync_current_window_size)
sync_button.grid(row=0, column=4, sticky="w", padx=(10, 0))

# 啟動定時更新視窗大小
self.start_window_size_sync()
```

**說明：**
- 創建視窗大小設定區塊
- 包含寬度和高度輸入框
- 提供同步當前視窗大小按鈕
- 啟動定時更新視窗大小功能

### 6. DUT控制設定

```python
# DUT 控制設定
dut_frame = ttk.LabelFrame(left_container, text="DUT 控制設定", padding=(10, 4))
dut_frame.pack(fill='both', expand=True, pady=(0, 8))
dut_frame.columnconfigure(1, weight=1)

dut_settings = self.setup_data.get('DUT_Control', {})
dut_row = 0

# 串口設定 - width=20
ttk.Label(dut_frame, text="串口:").grid(row=dut_row, column=0, sticky="w", pady=4)
self.vars["DUT_Serial_COM_Port"] = tk.StringVar(value=dut_settings.get("Serial_COM_Port", "COM5"))
ttk.Entry(dut_frame, textvariable=self.vars["DUT_Serial_COM_Port"], width=20).grid(row=dut_row, column=1, sticky="w", padx=(10, 0), pady=4)
dut_row += 1

# 指令超時(秒) - width=20
ttk.Label(dut_frame, text="指令超時(秒):").grid(row=dut_row, column=0, sticky="w", pady=4)
self.vars["DUT_Command_Timeout_Seconds"] = tk.StringVar(value=dut_settings.get("Command_Timeout_Seconds", "30"))
ttk.Entry(dut_frame, textvariable=self.vars["DUT_Command_Timeout_Seconds"], width=20).grid(row=dut_row, column=1, sticky="w", padx=(10, 0), pady=4)
dut_row += 1

# 指令結束字串 - width=20
ttk.Label(dut_frame, text="指令結束字串:").grid(row=dut_row, column=0, sticky="w", pady=4)
self.vars["DUT_Command_End_String"] = tk.StringVar(value=dut_settings.get("Command_End_String", "root"))
ttk.Entry(dut_frame, textvariable=self.vars["DUT_Command_End_String"], width=20).grid(row=dut_row, column=1, sticky="w", padx=(10, 0), pady=4)
dut_row += 1
```

**說明：**
- 創建DUT控制設定區塊
- 包含串口、指令超時、指令結束字串等設定
- 使用網格佈局排列元件
- 自動計算行號以方便維護

### 7. 指令間隔符號設定

```python
# 指令間隔符號 - width=20，淡黃色底色
ttk.Label(dut_frame, text="指令間隔符號:").grid(row=dut_row, column=0, sticky="w", pady=4)

# 創建一個容器來放置輸入框和說明標籤
separator_container = ttk.Frame(dut_frame)
separator_container.grid(row=dut_row, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=4)
separator_container.columnconfigure(0, weight=0)
separator_container.columnconfigure(1, weight=1)

self.vars["DUT_Command_Separator"] = tk.StringVar(value=dut_settings.get("Command_Separator", "|"))
self.command_separator_entry = tk.Entry(separator_container, textvariable=self.vars["DUT_Command_Separator"],
                                       width=20, bg='#FFFACD', relief='solid', borderwidth=1)
self.command_separator_entry.grid(row=0, column=0, sticky="w")
self.command_separator_entry.bind('<KeyRelease>', self.on_command_separator_changed)
self.command_separator_entry.bind('<FocusOut>', self.on_command_separator_changed)

# 添加說明標籤
separator_label = ttk.Label(separator_container, text="<-- 從 command.txt 中決定多重指令的分隔符號",
                           font=('Microsoft JhengHei UI', 9), foreground='#666666')
separator_label.grid(row=0, column=1, sticky="w", padx=(10, 0))
dut_row += 1
```

**說明：**
- 創建指令間隔符號設定區塊
- 使用淡黃色底色突出顯示
- 綁定鍵盤釋放和失去焦點事件
- 提供說明標籤解釋功能

### 8. 版本與路徑資訊

```python
# 版本與路徑資訊區塊 - 放在一起顯示
info_frame = ttk.LabelFrame(dut_frame, text="版本與路徑資訊", padding=(10, 4))
info_frame.grid(row=dut_row, column=0, columnspan=3, sticky="ew", pady=4)
info_frame.columnconfigure(1, weight=1)

# 應用程式版本（移到這裡，改為可編輯）
ttk.Label(info_frame, text="應用程式版本:").grid(row=0, column=0, sticky="w", pady=2)
version_entry = ttk.Entry(info_frame, textvariable=self.vars["version"], width=15,
                         font=('Microsoft JhengHei UI', 10, 'bold'))
version_entry.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=2)

# 指令檔案路徑
ttk.Label(info_frame, text="指令檔案路徑:").grid(row=1, column=0, sticky="nw", pady=2)
path_container = ttk.Frame(info_frame)
path_container.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=2)
path_container.columnconfigure(0, weight=1)

# 設定預設路徑為 Command_TABLE\command.txt
default_path = os.path.join("Command_TABLE", "command.txt")
current_path = dut_settings.get("Command_File_Path", default_path)
self.vars["DUT_Command_File_Path"] = tk.StringVar(value=current_path)
path_entry = ttk.Entry(path_container, textvariable=self.vars["DUT_Command_File_Path"])
path_entry.grid(row=0, column=0, sticky="ew", pady=(0, 5))

# 瀏覽按鈕
self.browse_button = ttk.Button(path_container, text="瀏覽檔案", command=lambda: self.browse_file("DUT_Command_File_Path"))
self.browse_button.grid(row=1, column=0, sticky="w")
```

**說明：**
- 創建版本與路徑資訊區塊
- 包含應用程式版本和指令檔案路徑設定
- 提供檔案瀏覽功能
- 使用網格佈局排列元件

### 9. 手動保存設定

```python
# 添加手動保存按鈕
save_button_frame = ttk.Frame(info_frame)
save_button_frame.grid(row=dut_row, column=0, columnspan=2, sticky="ew", pady=(10, 5))

self.manual_save_button = ttk.Button(
    save_button_frame,
    text="💾 儲存設定並即刻生效",
    command=self.manual_save_settings,
    style="Accent.TButton"
)
self.manual_save_button.pack(side="left", padx=(0, 10))

# 添加說明標籤
save_help_label = ttk.Label(
    save_button_frame,
    text="點擊此按鈕保存所有設定變更並立即生效",
    font=('Microsoft JhengHei UI', 9),
    foreground='#0066CC'
)
save_help_label.pack(side="left", padx=(10, 0))
```

**說明：**
- 創建手動保存按鈕
- 使用表情符號和特殊樣式突出顯示
- 提供說明標籤解釋功能
- 支援即時生效設定變更

### 10. 標籤頁名稱設定

```python
# 標籤頁名稱設定
tab_frame = ttk.LabelFrame(right_container, text="標籤頁名稱設定", padding=(10, 4))
tab_frame.pack(fill='x', pady=(0, 8))
tab_frame.columnconfigure(1, weight=1)

# 獲取當前的標籤頁名稱
tab_names = self.setup_data.get('tab_names', {})
default_tab_names = ['DUT 控制', '治具控制', '手動輸入指令', 'DOS 工具', '設定']

# 創建標籤頁名稱輸入框 - 標籤頁1~5 width=20
for i in range(5):
    tab_key = f'tab{i}'
    tab_name = tab_names.get(tab_key, default_tab_names[i] if i < len(default_tab_names) else f'標籤頁 {i+1}')
    ttk.Label(tab_frame, text=f"標籤頁 {i+1}:").grid(row=i, column=0, sticky="w", pady=4)
    self.vars[f"tab_names_{tab_key}"] = tk.StringVar(value=tab_name)
    ttk.Entry(tab_frame, textvariable=self.vars[f"tab_names_{tab_key}"], width=20).grid(row=i, column=1, sticky="ew", padx=(10, 0), pady=4)
```

**說明：**
- 創建標籤頁名稱設定區塊
- 支援5個標籤頁的名稱自訂
- 使用預設名稱作為備選
- 使用迴圈創建多個輸入框

### 11. 手動輸入指令設定

```python
# 手動輸入指令提示文字設定
manual_frame = ttk.LabelFrame(right_container, text="手動輸入指令設定", padding=(10, 4))
manual_frame.pack(fill='x', pady=(8, 8))
manual_frame.columnconfigure(1, weight=1)

ttk.Label(manual_frame, text="提示文字:").grid(row=0, column=0, sticky="w", pady=4)
self.vars["Manual_Hint_Text"] = tk.StringVar(value=self.setup_data.get("Manual_Command", {}).get("Hint_Text", "請輸入指令並按執行"))
manual_hint_entry = ttk.Entry(manual_frame, textvariable=self.vars["Manual_Hint_Text"], width=30)
manual_hint_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)

# 添加說明標籤
manual_help_label = ttk.Label(manual_frame, text="此文字將顯示在手動輸入指令頁面的提示區域",
                             font=('Microsoft JhengHei UI', 9), foreground='#666666')
manual_help_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))
```

**說明：**
- 創建手動輸入指令設定區塊
- 包含提示文字設定
- 提供說明標籤解釋功能
- 使用網格佈局排列元件

### 12. 事件處理函數

```python
def on_title_changed(self, *args):
    """視窗標題變更時的處理，限制最多50個字元"""
    try:
        current_title = self.vars["Window_Title"].get()
        char_count = len(current_title)
        
        # 更新字元計數顯示
        if hasattr(self, 'title_count_label'):
            color = 'red' if char_count > 50 else 'gray'
            self.title_count_label.config(text=f"({char_count}/50)", foreground=color)
        
        # 如果超過50個字元，截斷並顯示警告
        if char_count > 50:
            truncated_title = current_title[:50]
            self.vars["Window_Title"].set(truncated_title)
            print(f"[WARNING] 視窗標題已截斷至50個字元: {truncated_title}")
            
            # 顯示提示訊息
            print("[NOTIFICATION] 視窗標題已限制為50個字元")
                
    except Exception as e:
        print(f"[ERROR] 處理視窗標題變更時發生錯誤: {e}")

def on_command_separator_changed(self, event=None):
    """指令間隔符號即時更新"""
    try:
        new_separator = self.vars["DUT_Command_Separator"].get()
        if new_separator:  # 確保不為空
            # 立即更新設定檔
            settings = load_setup()
            if 'DUT_Control' not in settings:
                settings['DUT_Control'] = {}
            settings['DUT_Control']['Command_Separator'] = new_separator
            save_setup(settings)
            
            print(f"[INFO] 指令間隔符號已更新為: '{new_separator}'")
            
            # 通知其他元件更新
            self.apply_separator_changes_immediately()
    except Exception as e:
        print(f"更新指令間隔符號時發生錯誤: {e}")
```

**說明：**
- `on_title_changed`：處理視窗標題變更，限制最多50個字元
- `on_command_separator_changed`：處理指令間隔符號變更，即時更新設定
- 包含完整的錯誤處理和日誌記錄

### 13. 設定保存功能

```python
def manual_save_settings(self):
    """手動保存設定到 setup.json"""
    import traceback
    try:
        print("[DEBUG] 開始手動保存設定...")

        # 生成設定字典
        settings_dict = self.generate_settings_dict()

        # 獲取當前視窗狀態並添加到設定中
        try:
            # 找到主視窗
            root = self.parent
            while root and not hasattr(root, 'winfo_exists'):
                root = getattr(root, 'master', None) or getattr(root, 'parent', None)

            if root and hasattr(root, 'winfo_exists') and root.winfo_exists():
                # 獲取當前視窗大小
                width = root.winfo_width()
                height = root.winfo_height()

                if width > 100 and height > 100:  # 確保視窗大小有效
                    settings_dict['Window_Width'] = str(width)
                    settings_dict['Window_Height'] = str(height)
                    settings_dict['DUT_Control']['Window_Width'] = str(width)
                    settings_dict['DUT_Control']['Window_Height'] = str(height)
                    print(f"[DEBUG] 手動保存：視窗大小 {width}x{height}")

                # 獲取當前視窗標題（去除版本號）
                current_title = root.title()
                window_title = current_title
                if "_" in current_title:
                    parts = current_title.split("_")
                    if len(parts) >= 2:
                        window_title = "_".join(parts[:-1])
                elif " V" in current_title:
                    window_title = current_title.split(" V")[0]

                settings_dict['Window_Title'] = window_title
                settings_dict['DUT_Control']['Window_Title'] = window_title
                print(f"[DEBUG] 手動保存：視窗標題 {window_title}")

        except Exception as e:
            print(f"[WARNING] 獲取視窗狀態失敗: {e}")

        # 手動保存設定（繞過自動保存限制）
        from config_core import save_setup
        from core.config_manager import get_config_manager

        # 使用config_core的手動保存
        save_setup(settings_dict, manual_save=True)

        # 同時使用ConfigManager的手動保存
        config_manager = get_config_manager()
        config_manager.save_config(settings_dict, manual_save=True)

        # 強制保存 SharedConfigManager 中的設定
        try:
            from ui_parts.shared_config import get_shared_config
            shared_config = get_shared_config()
            if hasattr(shared_config, 'force_save_all'):
                shared_config.force_save_all()
                print("[DEBUG] SharedConfigManager 強制保存完成")
        except Exception as e:
            print(f"[WARNING] SharedConfigManager 強制保存失敗: {e}")

        # 立即重新讀取setup.json的所有資料
        print("[DEBUG] 手動儲存完成，重新讀取setup.json...")
        updated_setup = load_setup()

        # 更新本地設定資料
        self.setup_data = updated_setup

        # 重新載入UI顯示的所有設定值
        self.update_ui_from_settings()

        # 調用回調函數通知其他組件設定已更新
        if self.on_save_callback:
            # 傳遞最新的設定資料
            self.on_save_callback(updated_setup)
        
        # 更新手動輸入指令設定
        try:
            # 找到主視窗的 TabManager
            root = self.parent
            while root and not hasattr(root, 'tab_manager'):
                root = getattr(root, 'master', None) or getattr(root, 'parent', None)
            
            if root and hasattr(root, 'tab_manager'):
                tab_manager = root.tab_manager
                if hasattr(tab_manager, 'update_manual_settings'):
                    tab_manager.update_manual_settings()
                    print("[DEBUG] 手動輸入指令設定已更新")
                
                # 即時更新手動輸入頁面的提示文字
                if hasattr(tab_manager, 'manual_ui'):
                    hint_text = self.vars["Manual_Hint_Text"].get()
                    tab_manager.manual_ui.update_hint_text(hint_text)
                    print(f"[DEBUG] 手動輸入頁面提示文字已更新為: {hint_text}")
                    
        except Exception as e:
            print(f"[WARNING] 更新手動輸入指令設定失敗: {e}")

        # 立即更新標籤頁名稱
        self.update_tab_names_immediately()

        # 顯示成功訊息
        messagebox.showinfo("成功", "設定已手動儲存並立即生效！\n包含視窗大小、分割位置等所有設定。")
        print("[DEBUG] 設定已手動儲存並重新載入完成")

    except Exception as e:
        print(f"[錯誤] 手動儲存設定失敗: {e}")
        traceback.print_exc()
        messagebox.showerror("錯誤", f"手動儲存設定時發生錯誤: {e}")
```

**說明：**
- 手動保存所有設定到 `setup.json`
- 獲取當前視窗狀態並保存
- 使用多種配置管理器確保設定正確保存
- 立即更新UI顯示和通知其他組件
- 包含完整的錯誤處理和用戶反饋

## 重要設計原則

1. **模組化設計**：將不同功能分離到不同的UI區塊
2. **即時更新**：支援設定的即時更新和保存
3. **用戶友善**：提供詳細的說明和錯誤訊息
4. **錯誤處理**：包含完整的錯誤處理機制
5. **向後相容**：保持與舊版本的相容性

## 依賴關係

- `config_core`：配置檔案管理
- `ui_parts.tooltip`：工具提示管理
- `tkinter`：GUI框架
- `os`, `sys`：系統操作

## 使用方式

1. **創建設定標籤頁**：`settings_tab = SettingsTab(parent, on_save_callback)`
2. **手動保存設定**：`settings_tab.manual_save_settings()`
3. **更新UI設定**：`settings_tab.update_ui_from_settings()`
4. **同步視窗大小**：`settings_tab.sync_current_window_size()`

## 注意事項

- 確保所有必要的設定檔案都存在
- 注意字元限制和格式驗證
- 處理檔案不存在的情況
- 定期備份設定檔案 