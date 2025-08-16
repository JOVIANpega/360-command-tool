# serial_worker.py - 序列埠工作器

## 檔案概述
這是序列埠工作器模組，負責處理序列埠通訊和指令執行。使用新的異步處理和錯誤處理機制，提供更穩定和高效的序列埠操作。

## 主要功能
- 序列埠連接和通訊管理
- 指令執行和回應處理
- 特殊指令處理（DELAY、SHOW等）
- 異步執行和進度回報
- 錯誤處理和資源清理

## 程式碼結構

### 1. 導入模組和初始化

```python
# -*- coding: utf-8 -*-
"""
序列埠工作器 - 重構版本
使用新的異步處理和錯誤處理機制
"""
import serial
import threading
import time
import re
import tkinter as tk
from tkinter import messagebox
from typing import List, Callable, Optional

# 導入核心模組
from core import (
    get_error_handler, get_async_manager, safe_execute,
    log_debug, log_info, log_error, profile
)
```

**說明：**
- 設定 UTF-8 編碼以支援中文字符
- 導入必要的序列埠、執行緒、時間等模組
- 導入自定義的核心模組，包括錯誤處理、異步管理等

### 2. SerialWorker 類別定義

```python
class SerialWorker(threading.Thread):
    """序列埠工作器 - 重構版本"""

    def __init__(self, com: str, cmd_list: List[str], end_str: str, timeout: float,
                 on_data: Callable, on_status: Callable, on_progress: Callable,
                 on_finish: Callable, stop_event: threading.Event):
        super().__init__()

        # 初始化核心組件
        self.error_handler = get_error_handler()
        self.async_manager = get_async_manager()

        # 序列埠參數
        self.com = com
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

        # 序列埠連接（簡化版本）
        self.serial_connection: Optional[serial.Serial] = None

        log_debug(f"SerialWorker 初始化: COM={com}, 指令數={len(cmd_list)}, 超時={timeout}s")
```

**說明：**
- 繼承自 `threading.Thread` 以支援異步執行
- 初始化錯誤處理器和異步管理器
- 設置序列埠參數和回調函數
- 使用守護線程確保程式關閉時線程也會結束
- 記錄初始化資訊

### 3. 主執行方法

```python
@profile("SerialWorker.run")
def run(self):
    """主執行方法"""
    start_time = time.time()
    log_info(f"開始執行序列埠任務: {self.com}")

    try:
        # 創建序列埠連接
        ser = serial.Serial(self.com, 115200, timeout=0.1)
        self.serial_connection = ser  # 保存引用以便強制停止時使用

        self.on_status(True)

        buffer = ""

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
                for i in range(delay_seconds):
                    if self.stop_event.is_set() or finished:
                        break
                    time.sleep(1)
                    progress = ((i + 1) / delay_seconds) * 100
                    self.on_progress(progress)
                    self.on_data(f'剩餘 {delay_seconds - i - 1} 秒...\r', "purple")
                
                self.on_data(f'\n[系統] 延遲結束\n', "purple")
                continue
            
            # 處理特殊指令: SHOW
            show_match = re.match(r'^SHOW:(.+)$', cmd)
            if show_match:
                message = show_match.group(1)
                self.on_data(f'\n[系統] 顯示訊息: {message}\n', "purple")
                
                # 使用事件來協調主線程和工作線程
                message_confirmed = threading.Event()
                
                # 如果設置了回調函數，則使用它來顯示消息框
                if hasattr(self, 'show_message_callback') and self.show_message_callback:
                    # 在主線程中顯示消息框，並在用戶確認後設置事件
                    def confirm_callback():
                        # 標記訊息已確認
                        message_confirmed.set()
                        # 記錄確認訊息
                        self.on_data(f'\n[系統] 訊息已確認\n', "purple")
                        
                    # 顯示訊息並設置回調
                    self.show_message_callback(f"系統訊息: {message}", confirm_callback)
                    
                    # 等待最多3秒
                    wait_start = time.time()
                    while not message_confirmed.is_set() and not self.stop_event.is_set() and not finished:
                        time.sleep(0.1)
                        # 如果等待超過3秒，自動確認
                        if time.time() - wait_start > 3:
                            break
                    
                    continue
```

**說明：**
- 使用 `@profile` 裝飾器進行性能監控
- 創建序列埠連接並設置參數
- 遍歷所有指令並執行
- 處理特殊指令如 DELAY 和 SHOW
- 使用事件機制協調主線程和工作線程

### 4. 特殊指令處理

#### DELAY 指令處理

```python
# 處理特殊指令: DELAY
delay_match = re.match(r'^DELAY:(\d+)$', cmd)
if delay_match:
    delay_seconds = int(delay_match.group(1))
    self.on_data(f'\n[系統] 延遲 {delay_seconds} 秒...\n', "purple")
    
    # 分段延遲，每秒更新一次進度
    for i in range(delay_seconds):
        if self.stop_event.is_set() or finished:
            break
        time.sleep(1)
        progress = ((i + 1) / delay_seconds) * 100
        self.on_progress(progress)
        self.on_data(f'剩餘 {delay_seconds - i - 1} 秒...\r', "purple")
    
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
    self.on_data(f'\n[系統] 顯示訊息: {message}\n', "purple")
    
    # 使用事件來協調主線程和工作線程
    message_confirmed = threading.Event()
    
    # 如果設置了回調函數，則使用它來顯示消息框
    if hasattr(self, 'show_message_callback') and self.show_message_callback:
        # 在主線程中顯示消息框，並在用戶確認後設置事件
        def confirm_callback():
            # 標記訊息已確認
            message_confirmed.set()
            # 記錄確認訊息
            self.on_data(f'\n[系統] 訊息已確認\n', "purple")
            
        # 顯示訊息並設置回調
        self.show_message_callback(f"系統訊息: {message}", confirm_callback)
        
        # 等待最多3秒
        wait_start = time.time()
        while not message_confirmed.is_set() and not self.stop_event.is_set() and not finished:
            time.sleep(0.1)
            # 如果等待超過3秒，自動確認
            if time.time() - wait_start > 3:
                break
        
        continue
```

**說明：**
- 使用正則表達式匹配 SHOW 指令格式
- 提取要顯示的訊息內容
- 使用事件機制協調主線程和工作線程
- 支援超時自動確認

### 5. 序列埠通訊處理

```python
# 發送指令
self.on_data(f'\n[發送] {cmd}\n', "blue")
ser.write((cmd + '\n').encode('utf-8'))
ser.flush()

# 等待回應
start_time = time.time()
buffer = ""
while True:
    if self.stop_event.is_set() or finished:
        break
    
    # 檢查超時
    if time.time() - start_time > self.timeout:
        self.on_data(f'\n[錯誤] 指令超時: {cmd}\n', "red")
        break
    
    # 讀取序列埠資料
    if ser.in_waiting:
        data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        buffer += data
        self.on_data(data, "black")
    
    # 檢查是否收到結束字串
    if self.end_str in buffer:
        self.on_data(f'\n[完成] 指令執行完成: {cmd}\n', "green")
        break
    
    time.sleep(0.1)
```

**說明：**
- 發送指令到序列埠
- 等待回應並檢查超時
- 使用緩衝區累積回應資料
- 檢查結束字串以判斷指令是否完成
- 支援中斷和停止事件

### 6. 錯誤處理和資源清理

```python
try:
    # 序列埠操作
    pass
except serial.SerialException as e:
    log_error(f"序列埠錯誤: {e}")
    self.on_data(f'\n[錯誤] 序列埠錯誤: {e}\n', "red")
    self.on_status(False)
except Exception as e:
    log_error(f"執行錯誤: {e}")
    self.on_data(f'\n[錯誤] 執行錯誤: {e}\n', "red")
    self.on_status(False)
finally:
    # 清理資源
    if self.serial_connection:
        try:
            self.serial_connection.close()
        except Exception as e:
            log_error(f"關閉序列埠時發生錯誤: {e}")
    
    # 通知完成
    self.on_finish()
```

**說明：**
- 使用 try-except-finally 結構確保錯誤處理
- 捕獲序列埠異常和一般異常
- 在 finally 區塊中清理資源
- 通知完成回調函數

## 重要設計原則

1. **異步執行**：使用執行緒進行異步操作，避免阻塞主UI
2. **錯誤處理**：完整的錯誤處理和資源清理機制
3. **事件驅動**：使用事件機制協調主線程和工作線程
4. **資源管理**：確保序列埠連接正確關閉
5. **進度回報**：即時回報執行進度和狀態

## 依賴關係

- `serial`：序列埠通訊
- `threading`：多執行緒支援
- `core`：錯誤處理、異步管理、日誌記錄
- `tkinter`：GUI相關功能

## 使用方式

1. **創建序列埠工作器**：
   ```python
   worker = SerialWorker(com, cmd_list, end_str, timeout, on_data, on_status, on_progress, on_finish, stop_event)
   ```

2. **啟動執行**：
   ```python
   worker.start()
   ```

3. **停止執行**：
   ```python
   stop_event.set()
   ```

4. **設置訊息回調**：
   ```python
   worker.show_message_callback = show_message_function
   ```

## 注意事項

- 確保序列埠參數正確設置
- 注意超時時間的設定
- 處理序列埠連接失敗的情況
- 正確清理資源避免記憶體洩漏
- 使用適當的編碼處理中文字符 