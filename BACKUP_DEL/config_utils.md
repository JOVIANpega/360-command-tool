# 配置工具模組 (config_utils.py)

## 檔案概述

這個檔案提供了配置相關的工具函數，包括通知訊息管理、應用程式版本管理、資源路徑處理等功能。它是整個應用程式配置管理的輔助工具，提供統一的配置存取介面。

## 主要功能

- **通知訊息管理**: 載入和管理應用程式的通知訊息
- **版本管理**: 獲取和管理應用程式版本號
- **資源路徑處理**: 處理開發環境和打包環境的資源路徑
- **目錄確保**: 確保必要的目錄存在
- **錯誤日誌**: 提供統一的錯誤日誌記錄功能

## 全域變數

### 通知訊息存儲

```python
NOTIFY_TEXTS = {}  # 全局變數，存儲通知訊息
APP_VERSION = ""   # 應用程式版本號
```

**功能說明**: 
- 使用全域字典存儲通知訊息
- 使用全域變數存儲版本號
- 提供模組級別的資料共享

## 主要函數

### load_notification_messages()

**功能說明**: 
從 `setup.json` 中讀取通知訊息和版本號。

**實現細節**:
- 自動判斷開發環境和打包環境
- 讀取 `setup.json` 檔案
- 提取通知訊息和版本號
- 更新全域變數
- 包含完整的錯誤處理

**路徑判斷邏輯**:
```python
if getattr(sys, 'frozen', False):
    # 如果是打包後的 EXE
    base_dir = os.path.dirname(sys.executable)
else:
    # 如果是開發環境
    base_dir = os.path.dirname(os.path.abspath(__file__))
```

**功能說明**: 
- 使用 `sys.frozen` 判斷是否為打包環境
- 在打包環境中使用執行檔目錄
- 在開發環境中使用當前檔案目錄

### get_notification_text()

**功能說明**: 
獲取指定鍵的通知訊息，並進行格式化。

**實現細節**:
- 自動載入通知訊息（如果尚未載入）
- 支援字串格式化
- 提供預設值機制
- 包含錯誤處理

**參數說明**:
- `key`: 通知訊息的鍵名
- `*args`: 格式化參數

**返回值**: 
- 格式化後的通知訊息字串

**使用範例**:
```python
# 基本使用
message = get_notification_text("app_started")

# 格式化使用
message = get_notification_text("cmd_reloaded", "command.txt")
```

### get_app_version()

**功能說明**: 
獲取應用程式版本號。

**實現細節**:
- 自動載入版本號（如果尚未載入）
- 從 `setup.json` 中讀取版本資訊
- 提供統一的版本存取介面

**返回值**: 
- 應用程式版本號字串

### resource_path()

**功能說明**: 
獲取資源的絕對路徑，支援開發環境和打包後的環境。

**實現細節**:
- 自動判斷執行環境
- 處理特殊檔案的路徑查找
- 提供多路徑備選機制
- 包含詳細的日誌記錄

**參數說明**:
- `relative_path`: 相對路徑

**返回值**: 
- 資源的絕對路徑

#### 特殊檔案處理

##### command.txt 檔案

```python
if relative_path == 'command.txt':
    possible_paths = [
        os.path.join(base_path, 'Command_TABLE', 'command.txt'),
        os.path.join(base_path, 'command.txt'),
        os.path.join(os.path.dirname(base_path), 'Command_TABLE', 'command.txt')
    ]
```

**功能說明**: 
- 優先查找 `Command_TABLE` 目錄
- 提供多個備選路徑
- 記錄找到的檔案路徑

##### Fixture_Command.txt 檔案

```python
if relative_path == 'Fixture_Command.txt' or relative_path == 'FIXTURE/Fixture_Command.txt':
    possible_paths = [
        os.path.join(base_path, 'FIXTURE', 'Fixture_Command.txt'),
        os.path.join(base_path, 'Fixture_Command.txt'),
        os.path.join(os.path.dirname(base_path), 'FIXTURE', 'Fixture_Command.txt')
    ]
```

**功能說明**: 
- 優先查找 `FIXTURE` 目錄
- 提供多個備選路徑
- 記錄找到的檔案路徑

##### setup.json 檔案

```python
if relative_path == 'setup.json' and not os.path.exists(os.path.join(base_path, relative_path)):
    print(f"[WARNING] 找不到設定檔，將創建默認設定檔")
    # 創建預設設定檔
```

**功能說明**: 
- 檢查設定檔是否存在
- 如果不存在則創建預設設定檔
- 確保應用程式能正常啟動

### ensure_directories_exist()

**功能說明**: 
確保必要的目錄存在。

**實現細節**:
- 檢查並創建必要的目錄
- 包含錯誤處理機制
- 記錄目錄創建過程

**必要目錄**:
- `backup`: 備份目錄
- `logs`: 日誌目錄
- `Command_TABLE`: 指令表目錄
- `FIXTURE`: 治具目錄

### log_error()

**功能說明**: 
提供統一的錯誤日誌記錄功能。

**實現細節**:
- 記錄錯誤訊息到日誌檔案
- 包含時間戳記
- 支援錯誤堆疊追蹤
- 提供統一的錯誤記錄格式

## 自動載入機制

### 模組初始化

```python
# 在模塊導入時自動載入通知訊息
load_notification_messages()
```

**功能說明**: 
- 模組導入時自動載入通知訊息
- 確保通知訊息立即可用
- 避免重複載入

## 路徑處理策略

### 開發環境 vs 打包環境

#### 開發環境

```python
base_path = os.path.abspath(".")
```

**功能說明**: 
- 使用當前工作目錄
- 適合開發和測試
- 支援相對路徑

#### 打包環境

```python
base_path = os.path.dirname(sys.executable)
```

**功能說明**: 
- 使用執行檔所在目錄
- 適合打包後的應用程式
- 確保資源檔案的正確位置

### 多路徑查找

#### 指令檔案查找

```python
possible_paths = [
    os.path.join(base_path, 'Command_TABLE', 'command.txt'),
    os.path.join(base_path, 'command.txt'),
    os.path.join(os.path.dirname(base_path), 'Command_TABLE', 'command.txt')
]
```

**功能說明**: 
- 按優先順序查找檔案
- 提供多個備選路徑
- 確保檔案能找到

#### 治具檔案查找

```python
possible_paths = [
    os.path.join(base_path, 'FIXTURE', 'Fixture_Command.txt'),
    os.path.join(base_path, 'Fixture_Command.txt'),
    os.path.join(os.path.dirname(base_path), 'FIXTURE', 'Fixture_Command.txt')
]
```

**功能說明**: 
- 優先查找 `FIXTURE` 目錄
- 提供多個備選路徑
- 記錄找到的檔案路徑

## 錯誤處理機制

### 檔案不存在處理

```python
if not os.path.exists(setup_path):
    print(f"[ERROR] 找不到設定檔：{setup_path}")
    return
```

**功能說明**: 
- 檢查檔案是否存在
- 提供明確的錯誤訊息
- 避免檔案讀取錯誤

### 格式化錯誤處理

```python
try:
    message = message.format(*args)
except Exception as e:
    print(f"[ERROR] 格式化通知訊息時發生錯誤：{e}, key={key}, args={args}")
```

**功能說明**: 
- 捕獲格式化異常
- 記錄詳細的錯誤資訊
- 確保程式穩定運行

### 目錄創建錯誤處理

```python
try:
    os.makedirs(directory, exist_ok=True)
except Exception as e:
    print(f"[ERROR] 創建目錄失敗：{directory}, 錯誤：{e}")
```

**功能說明**: 
- 捕獲目錄創建異常
- 記錄錯誤資訊
- 確保程式能繼續運行

## 日誌記錄

### 資訊日誌

```python
print(f"[INFO] 已載入 {len(messages)} 個通知訊息")
print(f"[INFO] 找到指令檔: {path}")
```

**功能說明**: 
- 記錄重要的操作資訊
- 提供操作狀態反饋
- 便於除錯和監控

### 警告日誌

```python
print("[WARNING] 設定檔中沒有通知訊息")
print(f"[WARNING] 無法找到指令檔，將使用預設路徑: {path}")
```

**功能說明**: 
- 記錄非致命的問題
- 提供警告資訊
- 指導用戶解決問題

### 錯誤日誌

```python
print(f"[ERROR] 載入通知訊息時發生錯誤：{e}")
print(f"[ERROR] 找不到設定檔：{setup_path}")
```

**功能說明**: 
- 記錄嚴重的錯誤
- 提供詳細的錯誤資訊
- 便於問題診斷

## 性能優化

### 延遲載入

- 通知訊息在首次使用時才載入
- 避免不必要的檔案讀取
- 提高模組載入速度

### 快取機制

- 使用全域變數快取通知訊息
- 避免重複的檔案讀取
- 提高存取效率

### 路徑快取

- 記錄找到的檔案路徑
- 避免重複的路徑查找
- 提高檔案存取效率

## 技術特點

### 模組化設計

- 清晰的職責分離
- 統一的配置存取介面
- 可重用的工具函數

### 跨平台支援

- 支援 Windows、macOS、Linux
- 處理平台特定的路徑差異
- 提供一致的執行體驗

### 錯誤恢復

- 完整的錯誤處理機制
- 提供預設值和備選方案
- 確保程式穩定運行

## 使用方式

### 獲取通知訊息

```python
from config_utils import get_notification_text

# 基本使用
message = get_notification_text("app_started")

# 格式化使用
message = get_notification_text("cmd_reloaded", "command.txt")
```

### 獲取版本號

```python
from config_utils import get_app_version

version = get_app_version()
print(f"應用程式版本: {version}")
```

### 獲取資源路徑

```python
from config_utils import resource_path

# 獲取指令檔案路徑
command_path = resource_path("command.txt")

# 獲取治具檔案路徑
fixture_path = resource_path("FIXTURE/Fixture_Command.txt")
```

### 確保目錄存在

```python
from config_utils import ensure_directories_exist

ensure_directories_exist()
```

## 注意事項

- 確保 `setup.json` 檔案存在且格式正確
- 注意檔案編碼（使用 UTF-8）
- 檢查檔案和目錄的權限
- 在打包前測試所有路徑
- 注意跨平台的路徑差異

## 相依性

### 標準庫

- `os`: 檔案和目錄操作
- `sys`: 系統資訊和執行環境
- `json`: JSON 檔案處理
- `datetime`: 日期時間處理

這個配置工具模組是整個應用程式配置管理的輔助工具，提供了統一且可靠的配置存取功能。 