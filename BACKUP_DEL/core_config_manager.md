# 配置管理器 (core/config_manager.py)

## 檔案概述

這個檔案實現了統一的配置管理器，提供配置的載入、保存、快取和同步功能。它是整個應用程式配置管理的核心，確保設定的可靠性和一致性。

## 主要功能

- **配置載入**: 從 JSON 檔案載入配置，支援快取機制
- **配置保存**: 安全地保存配置到檔案，包含備份功能
- **配置快取**: 使用記憶體快取提高讀取效率
- **自動備份**: 自動備份配置檔案並清理舊備份
- **配置驗證**: 確保配置的完整性和正確性
- **執行緒安全**: 使用鎖機制確保多執行緒環境下的安全性

## 核心類別

### ConfigManager 類別

統一的配置管理器，負責所有配置相關的操作。

#### 初始化方法

```python
def __init__(self, config_file: str = "setup.json"):
```

**功能說明**: 
- 初始化配置管理器
- 設置配置檔案路徑
- 初始化快取和鎖機制
- 設置預設配置
- 確保必要目錄存在

**參數說明**:
- `config_file`: 配置檔案名稱，預設為 "setup.json"

**初始化流程**:
1. 設置配置檔案路徑
2. 初始化錯誤處理器
3. 創建快取字典和鎖機制
4. 設置備份目錄
5. 定義預設配置
6. 確保必要目錄存在

#### 預設配置結構

```python
self.default_config = {
    'version': '1.6.3.3',
    'Window_Title': '指令通',
    'Window_Width': '1536',
    'Window_Height': '793',
    'DUT_Control': {
        'Serial_COM_Port': '',
        'Command_Timeout_Seconds': '30',
        'Command_End_String': 'root',
        # ... 其他 DUT 控制設定
    },
    'Fixture_Control': {
        'Fixture_COM_Port': '',
        'Current_Command': '',
        # ... 其他治具控制設定
    },
    'tab_names': {
        'tab0': 'DUT 控制',
        'tab1': '治具控制',
        'tab2': '使用說明',
        'tab3': '設定'
    },
    'UI_Settings': {
        'ToolTip_Enabled': False
    },
    'notification_messages': {
        # ... 通知訊息設定
    }
}
```

**功能說明**: 
- 定義完整的預設配置結構
- 包含所有必要的設定項目
- 提供合理的預設值
- 確保配置的完整性

## 主要方法

### _ensure_directories()

**功能說明**: 
確保必要的目錄存在。

**實現細節**:
- 檢查備份目錄是否存在
- 如果不存在則創建目錄
- 包含錯誤處理機制

### _get_config_path()

**功能說明**: 
獲取配置檔案的完整路徑。

**實現細節**:
- 支援開發環境和打包環境
- 使用 `sys.frozen` 判斷是否為打包環境
- 返回絕對路徑

### _is_config_modified()

**功能說明**: 
檢查配置檔案是否被外部修改。

**實現細節**:
- 比較檔案的修改時間
- 如果無法檢查則假設已修改
- 用於決定是否需要重新載入配置

### _backup_config()

**功能說明**: 
備份配置檔案。

**實現細節**:
- 使用時間戳命名備份檔案
- 保存到備份目錄
- 使用 JSON 格式保存
- 自動清理舊備份

### _cleanup_old_backups()

**功能說明**: 
清理舊的備份檔案。

**實現細節**:
- 保留指定數量的最新備份
- 按修改時間排序
- 刪除過期的備份檔案
- 包含錯誤處理

### load_config()

**功能說明**: 
載入配置檔案。

**實現細節**:
- 支援強制重新載入
- 使用快取機制提高效率
- 檢查檔案是否被修改
- 確保配置的完整性
- 包含重試機制

**參數說明**:
- `force_reload`: 是否強制重新載入，預設為 False

**返回值**: 
- 配置字典

### _ensure_required_fields()

**功能說明**: 
確保配置包含所有必要的欄位。

**實現細節**:
- 遞迴合併預設配置和載入的配置
- 確保所有必要欄位都存在
- 保持現有配置不丟失
- 提供完整的配置結構

### save_config()

**功能說明**: 
保存配置到檔案。

**實現細節**:
- 支援手動保存和自動保存
- 自動備份當前配置
- 使用原子寫入確保安全性
- 包含重試機制
- 更新快取和修改時間

**參數說明**:
- `config`: 要保存的配置字典
- `manual_save`: 是否為手動保存，預設為 False

**返回值**: 
- 保存是否成功

### get_section()

**功能說明**: 
獲取指定區段的配置。

**實現細節**:
- 從配置字典中提取指定區段
- 如果區段不存在則返回空字典
- 提供安全的存取方式

### update_section()

**功能說明**: 
更新指定區段的配置。

**實現細節**:
- 更新指定區段的配置
- 支援手動保存控制
- 保持其他區段不變
- 返回更新是否成功

### get_value()

**功能說明**: 
獲取指定路徑的配置值。

**實現細節**:
- 支援點分隔的路徑（如 "DUT_Control.Serial_COM_Port"）
- 提供預設值機制
- 安全的存取方式
- 支援巢狀配置存取

### set_value()

**功能說明**: 
設置指定路徑的配置值。

**實現細節**:
- 支援點分隔的路徑
- 自動創建不存在的路徑
- 支援手動保存控制
- 返回設置是否成功

### disable_auto_save()

**功能說明**: 
禁用自動保存功能。

**實現細節**:
- 設置自動保存標誌為 False
- 防止頻繁的檔案寫入
- 提高程式性能

### enable_auto_save()

**功能說明**: 
啟用自動保存功能。

**實現細節**:
- 設置自動保存標誌為 True
- 恢復自動保存機制
- 確保配置的即時保存

## 全域函數

### get_config_manager()

**功能說明**: 
獲取全域的配置管理器實例。

**實現細節**:
- 使用單例模式
- 確保全域只有一個配置管理器實例
- 提供統一的配置存取介面

## 快取機制

### 快取結構

```python
self._config_cache = {}  # 配置快取
self._cache_lock = threading.RLock()  # 快取鎖
self._last_modified = 0  # 最後修改時間
```

**功能說明**: 
- 使用字典快取配置資料
- 使用可重入鎖確保執行緒安全
- 記錄檔案最後修改時間

### 快取策略

- **讀取快取**: 優先從快取讀取，提高效率
- **修改檢查**: 檢查檔案是否被外部修改
- **強制重新載入**: 支援強制重新載入配置
- **自動更新**: 檔案修改時自動更新快取

## 備份機制

### 備份策略

- **自動備份**: 每次保存時自動備份
- **時間戳命名**: 使用時間戳避免檔案名衝突
- **自動清理**: 保留指定數量的最新備份
- **錯誤處理**: 備份失敗不影響主操作

### 備份檔案命名

```python
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = os.path.join(self._backup_dir, f'setup_backup_{timestamp}.json')
```

## 錯誤處理

### 重試機制

使用 `@retry_on_failure` 裝飾器：

```python
@retry_on_failure(max_retries=3, delay=0.5)
def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
```

**功能說明**: 
- 最多重試 3 次
- 每次重試間隔 0.5 秒
- 提高配置操作的可靠性

### 安全執行

使用 `@safe_execute` 裝飾器：

```python
@safe_execute(get_error_handler(), show_user_error=False)
def _backup_config(self, config_data: Dict[str, Any]):
```

**功能說明**: 
- 自動捕獲和記錄異常
- 不顯示用戶錯誤訊息（內部操作）
- 確保程式穩定運行

## 執行緒安全

### 鎖機制

```python
self._cache_lock = threading.RLock()
```

**功能說明**: 
- 使用可重入鎖保護快取
- 支援同一執行緒多次獲取鎖
- 確保多執行緒環境下的安全性

### 原子操作

- 使用臨時檔案進行原子寫入
- 確保檔案寫入的完整性
- 防止寫入過程中的檔案損壞

## 性能優化

### 快取優化

- 記憶體快取減少檔案讀取
- 修改時間檢查避免不必要的重新載入
- 延遲寫入減少檔案 I/O

### 備份優化

- 自動清理舊備份節省磁碟空間
- 限制備份數量避免磁碟空間耗盡
- 非阻塞備份不影響主操作

## 技術特點

### 模組化設計

- 清晰的職責分離
- 使用裝飾器模式進行錯誤處理
- 統一的配置存取介面

### 可靠性

- 多重錯誤處理機制
- 自動備份和恢復
- 執行緒安全的操作

### 可擴展性

- 支援巢狀配置結構
- 靈活的配置路徑存取
- 可配置的預設值

## 使用方式

### 基本使用

```python
# 獲取配置管理器
config_manager = get_config_manager()

# 載入配置
config = config_manager.load_config()

# 獲取配置值
com_port = config_manager.get_value("DUT_Control.Serial_COM_Port", "COM5")

# 設置配置值
config_manager.set_value("DUT_Control.Serial_COM_Port", "COM6", manual_save=True)

# 保存配置
config_manager.save_config(config, manual_save=True)
```

### 區段操作

```python
# 獲取區段配置
dut_config = config_manager.get_section("DUT_Control")

# 更新區段配置
dut_config["Serial_COM_Port"] = "COM7"
config_manager.update_section("DUT_Control", dut_config, manual_save=True)
```

## 注意事項

- 確保備份目錄有足夠的磁碟空間
- 定期檢查備份檔案的完整性
- 在修改配置前先備份
- 注意配置檔案的路徑和權限

這個配置管理器是整個應用程式的配置管理基礎，提供了可靠且高效的配置處理功能。 