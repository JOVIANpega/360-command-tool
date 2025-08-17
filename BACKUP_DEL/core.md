# core/__init__.py - 核心模組

## 檔案概述
這是核心模組的初始化檔案，提供統一的錯誤處理、配置管理和資源管理功能。作為整個應用程式的核心基礎，提供穩定可靠的基礎服務。

## 主要功能
- 錯誤處理和日誌記錄
- 配置管理和設定同步
- 資源管理和快取機制
- 異步任務管理
- 性能監控和優化

## 程式碼結構

### 1. 模組導入和初始化

```python
# -*- coding: utf-8 -*-
"""
核心模組 - 提供統一的錯誤處理、配置管理和資源管理功能
"""

from .error_handler import (
    ErrorHandler, 
    get_error_handler,
    safe_execute,
    retry_on_failure,
    log_debug,
    log_info, 
    log_warning,
    log_error
)

from .config_manager import (
    ConfigManager,
    get_config_manager
)

from .resource_manager import (
    ResourceManager,
    ResourceCache,
    get_resource_manager
)

from .async_manager import (
    AsyncManager,
    TaskStatus,
    Task,
    get_async_manager,
    run_async,
    wait_for_result
)

from .performance_monitor import (
    PerformanceMonitor,
    PerformanceMetrics,
    FunctionProfile,
    get_performance_monitor,
    profile
)
```

**說明：**
- 設定 UTF-8 編碼以支援中文字符
- 導入所有核心子模組的功能
- 提供統一的介面供其他模組使用
- 確保模組的完整性和一致性

### 2. 錯誤處理模組

```python
from .error_handler import (
    ErrorHandler, 
    get_error_handler,
    safe_execute,
    retry_on_failure,
    log_debug,
    log_info, 
    log_warning,
    log_error
)
```

**說明：**
- `ErrorHandler`：錯誤處理器類別，提供統一的錯誤處理機制
- `get_error_handler`：獲取全域錯誤處理器實例
- `safe_execute`：安全執行裝飾器，確保函數執行時有適當的錯誤處理
- `retry_on_failure`：失敗重試裝飾器，支援自動重試機制
- `log_debug`、`log_info`、`log_warning`、`log_error`：不同級別的日誌記錄函數

### 3. 配置管理模組

```python
from .config_manager import (
    ConfigManager,
    get_config_manager
)
```

**說明：**
- `ConfigManager`：配置管理器類別，負責設定檔案的讀取、保存和管理
- `get_config_manager`：獲取全域配置管理器實例
- 提供統一的配置管理介面
- 支援設定的自動保存和同步

### 4. 資源管理模組

```python
from .resource_manager import (
    ResourceManager,
    ResourceCache,
    get_resource_manager
)
```

**說明：**
- `ResourceManager`：資源管理器類別，負責檔案和目錄的管理
- `ResourceCache`：資源快取類別，提供檔案內容的快取機制
- `get_resource_manager`：獲取全域資源管理器實例
- 支援資源的快取和重用

### 5. 異步管理模組

```python
from .async_manager import (
    AsyncManager,
    TaskStatus,
    Task,
    get_async_manager,
    run_async,
    wait_for_result
)
```

**說明：**
- `AsyncManager`：異步管理器類別，負責異步任務的管理
- `TaskStatus`：任務狀態列舉，定義任務的不同狀態
- `Task`：任務類別，表示一個異步任務
- `get_async_manager`：獲取全域異步管理器實例
- `run_async`：執行異步任務的函數
- `wait_for_result`：等待異步任務結果的函數

### 6. 性能監控模組

```python
from .performance_monitor import (
    PerformanceMonitor,
    PerformanceMetrics,
    FunctionProfile,
    get_performance_monitor,
    profile
)
```

**說明：**
- `PerformanceMonitor`：性能監控器類別，負責性能指標的收集和分析
- `PerformanceMetrics`：性能指標類別，定義各種性能指標
- `FunctionProfile`：函數性能分析類別，提供函數級別的性能分析
- `get_performance_monitor`：獲取全域性能監控器實例
- `profile`：性能分析裝飾器，用於分析函數性能

### 7. 模組匯出

```python
__all__ = [
    'ErrorHandler',
    'get_error_handler',
    'safe_execute',
    'retry_on_failure',
    'log_debug',
    'log_info',
    'log_warning',
    'log_error',
    'ConfigManager',
    'get_config_manager',
    'ResourceManager',
    'ResourceCache',
    'get_resource_manager',
    'AsyncManager',
    'TaskStatus',
    'Task',
    'get_async_manager',
    'run_async',
    'wait_for_result',
    'PerformanceMonitor',
    'PerformanceMetrics',
    'FunctionProfile',
    'get_performance_monitor',
    'profile'
]
```

**說明：**
- 定義模組的公開介面
- 確保只有必要的功能被匯出
- 提供清晰的模組使用指南
- 避免內部實作細節的洩露

## 重要設計原則

1. **模組化設計**：將不同功能分離到不同的子模組
2. **統一介面**：提供一致的API介面
3. **錯誤處理**：完整的錯誤處理和日誌記錄機制
4. **資源管理**：自動的資源管理和清理
5. **性能優化**：內建的性能監控和優化功能

## 依賴關係

- `error_handler`：錯誤處理和日誌記錄
- `config_manager`：配置管理
- `resource_manager`：資源管理
- `async_manager`：異步任務管理
- `performance_monitor`：性能監控

## 使用方式

1. **錯誤處理**：
   ```python
   from core import safe_execute, log_info
   
   @safe_execute
   def my_function():
       log_info("執行函數")
   ```

2. **配置管理**：
   ```python
   from core import get_config_manager
   
   config_manager = get_config_manager()
   value = config_manager.get_value('key')
   ```

3. **資源管理**：
   ```python
   from core import get_resource_manager
   
   resource_manager = get_resource_manager()
   content = resource_manager.load_file_content('file.txt')
   ```

4. **異步任務**：
   ```python
   from core import run_async, wait_for_result
   
   task = run_async(my_async_function)
   result = wait_for_result(task)
   ```

5. **性能監控**：
   ```python
   from core import profile
   
   @profile
   def my_function():
       pass
   ```

## 注意事項

- 確保所有子模組都已正確實現
- 注意模組間的依賴關係
- 處理模組初始化失敗的情況
- 確保資源的正確清理和釋放 