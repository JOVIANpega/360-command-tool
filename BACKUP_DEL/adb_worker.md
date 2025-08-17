# adb_worker.py - ADB 工作器模組

## 檔案概述
這是 ADB 工作器模組，負責使用 ADB（Android Debug Bridge）執行指令。提供與 Android 設備的通訊功能，支援指令執行、狀態監控和錯誤處理。

## 主要功能
- ADB 設備連接檢查
- 指令執行和回應處理
- 特殊指令處理（DELAY、SHOW等）
- 異步執行和進度回報
- 錯誤處理和狀態監控

## 程式碼結構

### 1. 導入模組和初始化

```python
# -*- coding: utf-8 -*-
"""
ADB 工作器模組
負責使用 ADB 執行指令
"""

import subprocess
import threading
import time
import re
from typing import List, Callable, Optional

# 導入核心模組
from core import (
    get_error_handler, get_async_manager, safe_execute,
    log_debug, log_info, log_error, profile
)
```

**說明：**
- 設定 UTF-8 編碼以支援中文字符
- 導入必要的標準庫和第三方模組
- 導入自定義的核心模組，包括錯誤處理、異步管理等

### 2. ADBWorker 類別定義

```python
class ADBWorker(threading.Thread):
    """ADB 工作器 - 使用 adb shell 執行指令"""

    def __init__(self, cmd_list: List[str], end_str: str, timeout: float,
                 on_data: Callable, on_status: Callable, on_progress: Callable,
                 on_finish: Callable, stop_event: threading.Event):
        super().__init__()

        # 初始化核心組件
        self.error_handler = get_error_handler()
        self.async_manager = get_async_manager()

        # ADB 參數
        self.cmd_list = cmd_list
        self.end_str = end_str
        self.timeout = timeout

        # 回調函數
        self.on_data = on_data
        self.on_status = on_status
        self.on_progress = on_progress
        self.on_finish = on_finish
        self.stop_event = stop_event

        # 設置為守護線程
        self.daemon = True

        # 用於顯示訊息的回調函數
        self.show_message_callback: Optional[Callable] = None

        log_debug(f"ADBWorker 初始化: 指令數={len(cmd_list)}, 超時={timeout}s")
```

**說明：**
- 繼承自 `threading.Thread` 以支援異步執行
- 初始化錯誤處理器和異步管理器
- 設置 ADB 參數和回調函數
- 使用守護線程確保程式關閉時線程也會結束
- 記錄初始化資訊

### 3. ADB 連接檢查

```python
def check_adb_connection(self):
    """檢查 ADB 連接狀態"""
    try:
        # 在 Windows 上隱藏 DOS 視窗
        startupinfo = None
        if subprocess.sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        result = subprocess.run(['adb', 'devices'],
                              capture_output=True, text=True, timeout=5,
                              startupinfo=startupinfo)
        if result.returncode == 0:
            devices = result.stdout.strip().split('\n')[1:]  # 跳過標題行
            connected_devices = [line for line in devices if line.strip() and 'device' in line]
            return len(connected_devices) > 0
        return False
    except Exception as e:
        log_error(f"檢查 ADB 連接時發生錯誤: {e}")
        return False
```

**說明：**
- 使用 `adb devices` 指令檢查設備連接狀態
- 在 Windows 上隱藏 DOS 視窗以提供更好的用戶體驗
- 解析設備列表並檢查是否有已連接的設備
- 包含完整的錯誤處理

### 4. ADB 指令執行

```python
def execute_adb_command(self, command: str) -> tuple:
    """執行單個 ADB 指令"""
    try:
        # 構建 adb shell 指令
        adb_cmd = ['adb', 'shell', command]

        # 在 Windows 上隱藏 DOS 視窗
        startupinfo = None
        if subprocess.sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        # 執行指令
        result = subprocess.run(adb_cmd, capture_output=True, text=True, timeout=30,
                              startupinfo=startupinfo)

        return result.returncode, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        return -1, "", "指令執行超時"
    except Exception as e:
        return -1, "", str(e)
```

**說明：**
- 構建 `adb shell` 指令並執行
- 在 Windows 上隱藏 DOS 視窗
- 捕獲指令的輸出和錯誤
- 處理超時和異常情況
- 返回執行結果的元組（返回碼、標準輸出、標準錯誤）

### 5. 主執行方法

```python
@profile("ADBWorker.run")
def run(self):
    """主執行方法"""
    start_time = time.time()
    log_info("開始執行 ADB 任務")

    try:
        # 檢查 ADB 連接
        if not self.check_adb_connection():
            self.on_data("\n[錯誤] 沒有檢測到 ADB 設備連接\n", "error")
            self.on_data("請確認：\n", "error")
            self.on_data("1. 設備已連接並開啟 USB 調試\n", "error")
            self.on_data("2. ADB 驅動已正確安裝\n", "error")
            self.on_data("3. 執行 'adb devices' 可以看到設備\n", "error")
            return

        self.on_status(True)
        finished = False

        # 執行所有指令
        for i, cmd in enumerate(self.cmd_list):
            if self.stop_event.is_set() or finished:
                break

            cmd = cmd.strip()
            if not cmd:
                continue

            # 處理特殊指令: DELAY
            delay_match = re.match(r'^DELAY:(\d+)$', cmd)
            if delay_match:
                delay_seconds = int(delay_match.group(1))
                self.on_data(f'\n[系統] 延遲 {delay_seconds} 秒...\n', "purple")
                
                # 分段延遲，每秒更新一次進度
                for j in range(delay_seconds):
                    if self.stop_event.is_set() or finished:
                        break
                    time.sleep(1)
                    progress = ((j + 1) / delay_seconds) * 100
                    self.on_progress(progress)
                    self.on_data(f'剩餘 {delay_seconds - j - 1} 秒...\r', "purple")
                
                self.on_data(f'\n[系統] 延遲結束\n', "purple")
                continue

            # 處理特殊指令: SHOW
            show_match = re.match(r'^SHOW:(.+)$', cmd)
            if show_match:
                message = show_match.group(1)
                self.on_data(f'\n[顯示] {message}\n', "purple")
                
                if self.show_message_callback:
                    try:
                        self.show_message_callback("提示", message)
                    except Exception as e:
                        self.on_data(f'[錯誤] 顯示消息框時發生錯誤: {e}\n', "error")
                else:
                    self.on_data(f'[警告] 無法顯示消息框，因為未設置回調函數\n', "error")
                
                continue

            # 正常指令處理
            self.on_data(f'\n[ADB 發送] {cmd}\n', "send")
            
            # 執行 ADB 指令
            returncode, stdout, stderr = self.execute_adb_command(cmd)
            
            # 處理執行結果
            if returncode == 0:
                if stdout:
                    self.on_data(stdout, None)
                
                # 檢查是否收到結束字串
                if self.end_str and self.end_str in stdout:
                    if i == len(self.cmd_list) - 1:
                        self.on_data(f'\n[結束] 收到指定結束字串 {self.end_str}\n', "end")
                        finished = True
            else:
                # 指令執行失敗
                if stderr:
                    self.on_data(f'\n[錯誤] {stderr}\n', "error")
                else:
                    self.on_data(f'\n[錯誤] 指令執行失敗 (返回碼: {returncode})\n', "error")

            # 更新進度
            progress = ((i + 1) / len(self.cmd_list)) * 100
            self.on_progress(progress)

            # 指令間隔1秒
            if i < len(self.cmd_list) - 1:  # 不是最後一個指令
                time.sleep(1)

        # 如果沒有在執行指令時接收到結束字串，則標記完成
        if not finished and not self.stop_event.is_set():
            self.on_data(f'\n[系統] 所有 ADB 指令已執行完成\n', "purple")

    except Exception as e:
        self.on_data(f'\n[錯誤] ADB 執行時發生錯誤: {e}\n', "error")
        log_error(f"ADB 執行錯誤: {e}")

    finally:
        # 更新狀態
        self.on_status(False)
        self.on_finish()
```

**說明：**
- 使用 `@profile` 裝飾器進行性能監控
- 檢查 ADB 連接狀態
- 遍歷所有指令並執行
- 處理特殊指令如 DELAY 和 SHOW
- 處理正常 ADB 指令的執行結果
- 更新進度和狀態
- 包含完整的錯誤處理

### 6. 特殊指令處理

#### DELAY 指令處理

```python
# 處理特殊指令: DELAY
delay_match = re.match(r'^DELAY:(\d+)$', cmd)
if delay_match:
    delay_seconds = int(delay_match.group(1))
    self.on_data(f'\n[系統] 延遲 {delay_seconds} 秒...\n', "purple")
    
    # 分段延遲，每秒更新一次進度
    for j in range(delay_seconds):
        if self.stop_event.is_set() or finished:
            break
        time.sleep(1)
        progress = ((j + 1) / delay_seconds) * 100
        self.on_progress(progress)
        self.on_data(f'剩餘 {delay_seconds - j - 1} 秒...\r', "purple")
    
    self.on_data(f'\n[系統] 延遲結束\n', "purple")
    continue
```

**說明：**
- 使用正則表達式匹配 DELAY 指令格式
- 解析延遲秒數
- 分段延遲，每秒更新進度
- 支援中斷和停止事件

#### SHOW 指令處理

```python
# 處理特殊指令: SHOW
show_match = re.match(r'^SHOW:(.+)$', cmd)
if show_match:
    message = show_match.group(1)
    self.on_data(f'\n[顯示] {message}\n', "purple")
    
    if self.show_message_callback:
        try:
            self.show_message_callback("提示", message)
        except Exception as e:
            self.on_data(f'[錯誤] 顯示消息框時發生錯誤: {e}\n', "error")
    else:
        self.on_data(f'[警告] 無法顯示消息框，因為未設置回調函數\n', "error")
    
    continue
```

**說明：**
- 使用正則表達式匹配 SHOW 指令格式
- 提取要顯示的訊息內容
- 使用回調函數顯示訊息框
- 包含錯誤處理

### 7. 回調函數設置

```python
def set_show_message_callback(self, callback: Callable):
    """設置顯示訊息的回調函數"""
    self.show_message_callback = callback
```

**說明：**
- 提供設置顯示訊息回調函數的方法
- 用於顯示 SHOW 指令的訊息框
- 支援自定義訊息顯示邏輯

## 重要設計原則

1. **異步執行**：使用執行緒進行異步操作，避免阻塞主UI
2. **錯誤處理**：完整的錯誤處理和狀態監控機制
3. **用戶體驗**：隱藏 DOS 視窗，提供友善的錯誤訊息
4. **資源管理**：正確的資源清理和狀態更新
5. **進度回報**：即時回報執行進度和狀態

## 依賴關係

- `subprocess`：外部程式執行
- `threading`：多執行緒支援
- `core`：錯誤處理、異步管理、日誌記錄
- `re`：正則表達式處理

## 使用方式

1. **創建 ADB 工作器**：
   ```python
   worker = ADBWorker(cmd_list, end_str, timeout, on_data, on_status, on_progress, on_finish, stop_event)
   ```

2. **設置訊息回調**：
   ```python
   worker.set_show_message_callback(show_message_function)
   ```

3. **啟動執行**：
   ```python
   worker.start()
   ```

4. **停止執行**：
   ```python
   stop_event.set()
   ```

## 注意事項

- 確保 ADB 已正確安裝並在 PATH 中
- 檢查設備連接和 USB 調試設定
- 注意指令的超時設定
- 處理 ADB 連接失敗的情況
- 正確清理資源避免記憶體洩漏 