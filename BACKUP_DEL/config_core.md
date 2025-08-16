# config_core.py - 配置核心模組

## 檔案概述
這是配置核心模組，負責管理應用程式的所有配置檔案，包括指令檔案、設定檔案、日誌檔案等。使用新的核心模組提供更好的錯誤處理和性能。

## 主要功能
- 載入和管理指令檔案
- 處理設定檔案的讀取和保存
- 管理COM口列表
- 處理關鍵字高亮設定
- 提供檔案備份和清理功能

## 程式碼結構

### 1. 導入模組和初始化

```python
# -*- coding: utf-8 -*-
"""
配置核心模組 - 重構版本
使用新的核心模組提供更好的錯誤處理和性能
"""
import json
import os
import sys
import re
import platform
import time
from datetime import datetime
from tkinter import messagebox
from typing import Dict, Any, List, Optional

# 導入新的核心模組
from core import (
    get_error_handler, get_config_manager, get_resource_manager,
    safe_execute, log_debug, log_info, log_warning, log_error
)
```

**說明：**
- 設定 UTF-8 編碼以支援中文字符
- 導入必要的標準庫和第三方模組
- 導入自定義的核心模組，包括錯誤處理、配置管理、資源管理等

### 2. 核心組件初始化

```python
# 初始化核心組件
error_handler = get_error_handler()
config_manager = get_config_manager()
resource_manager = get_resource_manager()

# 確保必要的目錄存在
resource_manager.ensure_directory('backup')
resource_manager.ensure_directory('logs')
```

**說明：**
- 初始化錯誤處理器、配置管理器和資源管理器
- 確保備份和日誌目錄存在，避免檔案操作錯誤

### 3. 檔案路徑定義

```python
# 定義檔案路徑 - 使用新的資源管理器
COMMAND_FILE = resource_manager.get_resource_path('command.txt')
SETUP_FILE = resource_manager.get_resource_path('setup.json')
GUIDE_FILE = resource_manager.get_resource_path('user_guide.txt')
ERROR_LOG_FILE = resource_manager.get_resource_path('error_log.txt')
RUN_LOG_FILE = resource_manager.get_resource_path('run_log.txt')

# 當前日期的日誌文件
today = datetime.now().strftime('%Y%m%d')
TODAY_LOG_FILE = resource_manager.get_resource_path(f'logs/log_{today}.txt')
```

**說明：**
- 使用資源管理器統一管理檔案路徑
- 支援開發環境和打包環境的不同路徑
- 自動生成當前日期的日誌檔案路徑

### 4. 指令檔案載入

```python
@safe_execute(error_handler, show_user_error=True)
def load_commands() -> Dict[str, str]:
    """載入指令檔案，使用新的錯誤處理和快取機制"""
    commands = {}

    try:
        # 檢查檔案是否存在
        if not os.path.exists(COMMAND_FILE):
            error_msg = f'找不到指令檔 (command.txt)\n路徑: {COMMAND_FILE}'
            log_error(error_msg, show_user=True)
            sys.exit(1)

        # 使用資源管理器載入內容（支援快取）
        content = resource_manager.load_file_content(COMMAND_FILE)
        if content is None:
            error_msg = f'無法讀取指令檔: {COMMAND_FILE}'
            log_error(error_msg, show_user=True)
            sys.exit(1)

        # 解析指令格式
        has_valid_commands = False
        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('#'):
                continue

            if '=' in line:
                try:
                    k, v = line.split('=', 1)
                    k, v = k.strip(), v.strip()
                    if k and v:  # 確保鍵值都不為空
                        commands[k] = v
                        has_valid_commands = True
                except ValueError:
                    log_warning(f"指令檔第 {line_num} 行格式錯誤: {line}")
                    continue

        if not has_valid_commands:
            error_msg = '指令檔中沒有有效的指令格式'
            log_error(error_msg, show_user=True)
            sys.exit(1)

        log_info(f"成功載入 {len(commands)} 個指令")
        return commands

    except Exception as e:
        error_msg = f'讀取指令檔時發生錯誤: {e}\n路徑: {COMMAND_FILE}'
        log_error(error_msg, e, show_user=True)
        sys.exit(1)
```

**說明：**
- 使用 `@safe_execute` 裝飾器確保錯誤被正確處理
- 檢查指令檔案是否存在和可讀
- 解析指令檔案格式，支援註解和空行
- 驗證指令格式的正確性
- 記錄載入結果和錯誤資訊

### 5. 設定檔案管理

```python
def load_setup() -> Dict[str, Any]:
    """載入設定檔 - 使用新的配置管理器"""
    return config_manager.load_config()

def save_setup(setup_data: Dict[str, Any], manual_save=False) -> bool:
    """保存設定檔 - 使用新的配置管理器"""
    # 如果不是手動保存，則跳過（暫時禁用自動保存）
    if not manual_save:
        print("[DEBUG] 自動保存已禁用，請使用手動保存")
        return False
    return config_manager.save_config(setup_data)
```

**說明：**
- 使用配置管理器統一管理設定檔案的讀取和保存
- 支援手動保存和自動保存模式
- 提供向後相容性

### 6. 備份功能

```python
# 備份功能已整合到 ConfigManager 中
def backup_setup(setup_data):
    """備份設定檔 - 向後相容性包裝"""
    config_manager._backup_config(setup_data)

def cleanup_old_backups():
    """清理舊備份 - 向後相容性包裝"""
    config_manager._cleanup_old_backups()
```

**說明：**
- 提供設定檔案的備份和清理功能
- 使用配置管理器的內建備份機制
- 保持向後相容性

### 7. COM口管理

```python
@safe_execute(error_handler)
def list_com_ports() -> List[str]:
    """列出可用的COM口，只對特定類型顯示描述"""
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        com_ports = []

        for port in ports:
            # 基本 COM 口名稱
            port_name = port.device

            # 獲取描述信息
            description = port.description.upper() if port.description else ""

            # 只對特定類型的 COM 口顯示描述
            display_name = port_name  # 預設只顯示 COM 口名稱

            # 檢查是否包含特定的描述關鍵字
            if "USB DM PORT" in description or "DM PORT" in description:
                display_name = f"{port_name} - DM PORT"
            elif "USB AT PORT" in description or "AT PORT" in description:
                display_name = f"{port_name} - AT PORT"
            elif "USB NMEA PORT" in description or "NMEA PORT" in description:
                display_name = f"{port_name} - NMEA PORT"
            # 其他類型的 COM 口只顯示名稱，不顯示描述

            com_ports.append(display_name)

        log_debug(f"找到 {len(com_ports)} 個COM口: {com_ports}")
        return com_ports
    except Exception as e:
        log_error("獲取COM口列表時發生錯誤", e)
        return []

def extract_com_port_name(display_name: str) -> str:
    """從顯示名稱中提取實際的 COM 口名稱"""
    if " - " in display_name:
        return display_name.split(" - ")[0]
    return display_name
```

**說明：**
- 列出系統中可用的COM口
- 只對特定類型的COM口顯示描述資訊
- 提供從顯示名稱提取實際COM口名稱的功能
- 包含完整的錯誤處理

### 8. 關鍵字高亮設定

```python
def load_highlight_keywords():
    """載入關鍵字高亮設定"""
    highlight_keywords = {}
    
    try:
        print(f"[DEBUG] 開始載入關鍵字高亮設定...")
        with open(COMMAND_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 尋找關鍵字高亮區段
        print(f"[DEBUG] 搜尋關鍵字高亮區段...")
        keyword_section = re.search(r'\[關鍵字高亮\](.*?)(?=\[|\Z)', content, re.DOTALL)
        if not keyword_section:
            keyword_section = re.search(r'==關鍵字高亮==(.*?)(?===|\Z)', content, re.DOTALL)
            
        if keyword_section:
            keyword_content = keyword_section.group(1).strip()
            print(f"[DEBUG] 找到關鍵字高亮區段: {keyword_content}")
            for line in keyword_content.split('\n'):
                line = line.strip()
                if line and '=' in line:
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        keyword, color = parts
                        keyword = keyword.strip()
                        color = color.strip()
                        
                        # 檢查顏色名稱是否有效
                        valid_colors = ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'black', 'white', 'gray', 'pink', 'brown', 'cyan', 'magenta']
                        
                        # 如果顏色名稱不在有效顏色列表中，使用預設顏色
                        if color.lower() not in valid_colors and not color.startswith('#'):
                            print(f"[WARNING] 無效的顏色名稱: {color}，使用預設顏色 'blue'")
                            color = 'blue'
                        
                        if keyword and color:
                            highlight_keywords[keyword] = color
                            print(f"[INFO] 載入關鍵字高亮: {keyword} -> {color}")
        else:
            print(f"[WARNING] 找不到關鍵字高亮區段")
                        
        print(f"[INFO] 總共載入了 {len(highlight_keywords)} 個關鍵字高亮設定")
        return highlight_keywords
    except Exception as e:
        print(f"[ERROR] 載入關鍵字高亮設定時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return {}
```

**說明：**
- 從指令檔案中載入關鍵字高亮設定
- 支援多種格式的關鍵字高亮區段標記
- 驗證顏色名稱的有效性
- 提供詳細的除錯資訊

### 9. 顏色關鍵字管理

```python
def load_color_word():
    """
    從 color_word.txt 讀取關鍵字與顏色對應，回傳 dict。
    檔案格式：keyword=color，每行一組。
    支援顏色名稱與 #HEX，遇到錯誤自動略過。
    """
    color_word_file = resource_manager.get_resource_path('color_word.txt')
    color_dict = {}
    valid_colors = [
        'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'black', 'white', 'gray', 'pink', 'brown', 'cyan', 'magenta'
    ]
    try:
        if not os.path.exists(color_word_file):
            print(f"[WARNING] 找不到 color_word.txt：{color_word_file}")
            return color_dict
        with open(color_word_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    keyword, color = line.split('=', 1)
                    keyword = keyword.strip()
                    color = color.strip()
                    if not keyword or not color:
                        continue
                    # 檢查顏色是否合法
                    if color.lower() not in valid_colors and not color.startswith('#'):
                        print(f"[WARNING] color_word.txt 無效顏色：{color}，自動略過")
                        continue
                    color_dict[keyword] = color
        print(f"[INFO] color_word.txt 載入 {len(color_dict)} 組關鍵字高亮")
    except Exception as e:
        print(f"[ERROR] 讀取 color_word.txt 發生錯誤: {e}")
    return color_dict

def reload_color_word():
    """
    重新載入 color_word.txt，用於即時更新關鍵字高亮設定
    """
    print("[INFO] 重新載入 color_word.txt...")
    return load_color_word()

def open_color_word_editor():
    """
    開啟 color_word.txt 進行編輯
    """
    color_word_file = resource_manager.get_resource_path('color_word.txt')
    try:
        if platform.system() == 'Windows':
            os.startfile(color_word_file)
        elif platform.system() == 'Darwin':  # macOS
            os.system(f'open "{color_word_file}"')
        else:  # Linux
            os.system(f'xdg-open "{color_word_file}"')
        print(f"[INFO] 已開啟關鍵字設定檔：{color_word_file}")
        return True
    except Exception as e:
        print(f"[ERROR] 無法開啟關鍵字設定檔：{e}")
        return False
```

**說明：**
- 從 `color_word.txt` 檔案載入關鍵字與顏色對應
- 支援顏色名稱和十六進位顏色代碼
- 提供重新載入功能，支援即時更新
- 提供編輯器開啟功能，支援多平台

## 重要設計原則

1. **錯誤處理**：使用 `@safe_execute` 裝飾器確保所有函數都有適當的錯誤處理
2. **資源管理**：使用資源管理器統一管理檔案路徑和內容
3. **向後相容性**：保持與舊版本的相容性
4. **模組化設計**：將不同功能分離到不同模組中
5. **日誌記錄**：詳細記錄操作過程和錯誤資訊

## 依賴關係

- `core` 模組：提供錯誤處理、配置管理、資源管理等功能
- `serial` 模組：COM口管理
- `tkinter`：GUI相關功能
- `platform`：平台相關功能

## 使用方式

1. **載入指令**：`load_commands()` 載入指令檔案
2. **載入設定**：`load_setup()` 載入設定檔案
3. **保存設定**：`save_setup(setup_data, manual_save=True)` 保存設定檔案
4. **列出COM口**：`list_com_ports()` 獲取可用COM口列表
5. **載入關鍵字高亮**：`load_highlight_keywords()` 載入關鍵字高亮設定

## 注意事項

- 確保所有必要的檔案都存在且可讀
- 注意檔案編碼為 UTF-8
- 檢查顏色名稱的有效性
- 處理檔案不存在的情況 