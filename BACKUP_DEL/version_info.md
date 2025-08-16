# 版本資訊模組 (version_info.py)

## 檔案概述

這個檔案定義了應用程式的版本資訊和相關元資料，包括檔案版本資訊、應用程式資訊、更新日誌等。它主要用於打包時的版本資訊設定和應用程式內部的版本管理。

## 主要功能

- **檔案版本資訊**: 定義 Windows 執行檔的版本資訊
- **應用程式資訊**: 提供應用程式的基本資訊
- **版本管理**: 統一管理版本號和相關資訊
- **更新日誌**: 記錄各版本的更新內容

## 檔案版本資訊

### VSVersionInfo 結構

```python
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 9, 3, 0),
    prodvers=(1, 9, 3, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'VALO360 開發團隊'),
         StringStruct(u'FileDescription', u'VALO360 指令通 - 串口指令執行工具'),
         StringStruct(u'FileVersion', u'1.9.3.0'),
         StringStruct(u'InternalName', u'VALO360_CommandTool'),
         StringStruct(u'LegalCopyright', u'Copyright © 2024-2025 VALO360'),
         StringStruct(u'OriginalFilename', u'指令通_v1.9.3.exe'),
         StringStruct(u'ProductName', u'VALO360 指令通'),
         StringStruct(u'ProductVersion', u'1.9.3.0'),
         StringStruct(u'Comments', u'V1.9.3 新增手動輸入指令，手動輸入頁顯示速度優化、字體大小與DUT控制聯動')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1028, 1200])])
  ]
)
```

**功能說明**: 
定義 Windows 執行檔的版本資訊結構。

#### FixedFileInfo 參數

- **filevers**: 檔案版本號 (1, 9, 3, 0)
- **prodvers**: 產品版本號 (1, 9, 3, 0)
- **mask**: 版本資訊遮罩 (0x3f)
- **flags**: 版本標誌 (0x0)
- **OS**: 作業系統識別碼 (0x40004 = Windows NT)
- **fileType**: 檔案類型 (0x1 = 應用程式)
- **subtype**: 子類型 (0x0)
- **date**: 建立日期 (0, 0)

#### StringFileInfo 內容

- **CompanyName**: 公司名稱
- **FileDescription**: 檔案描述
- **FileVersion**: 檔案版本
- **InternalName**: 內部名稱
- **LegalCopyright**: 版權資訊
- **OriginalFilename**: 原始檔案名
- **ProductName**: 產品名稱
- **ProductVersion**: 產品版本
- **Comments**: 版本註解

#### VarFileInfo 設定

- **Translation**: 語言設定 (1028 = 繁體中文, 1200 = Unicode)

## 應用程式資訊

### 基本資訊

```python
APP_NAME = "VALO360 指令通"
APP_VERSION = "1.9.3"
APP_DESCRIPTION = "串口指令執行工具 - V1.9.3 新增手動輸入指令，手動輸入頁顯示速度優化、字體大小與DUT控制聯動"
APP_AUTHOR = "VALO360 開發團隊"
APP_COPYRIGHT = "Copyright © 2024-2025 VALO360"
```

**功能說明**: 
定義應用程式的基本資訊。

**資訊內容**:
- **APP_NAME**: 應用程式名稱
- **APP_VERSION**: 應用程式版本號
- **APP_DESCRIPTION**: 應用程式描述
- **APP_AUTHOR**: 開發團隊
- **APP_COPYRIGHT**: 版權資訊

## 更新日誌

### 版本 1.9.3 更新內容

```python
CHANGELOG_V1_9_3 = """
版本 1.9.3 更新內容：

• 新增手動輸入指令頁面，顯示速度大幅優化，執行結果即時顯示。
• 手動輸入頁所有元件字體大小與 DUT 控制設定完全聯動。
• 介面細節優化，提升用戶體驗。
"""
```

**功能說明**: 
記錄版本 1.9.3 的更新內容。

**更新項目**:
1. **新增手動輸入指令頁面**: 提供手動輸入指令的功能
2. **顯示速度優化**: 大幅提升執行結果的顯示速度
3. **字體大小聯動**: 手動輸入頁的字體大小與 DUT 控制設定同步
4. **介面優化**: 改善使用者體驗

## 版本號格式

### 版本號結構

```
主版本號.次版本號.修訂號.建置號
例如: 1.9.3.0
```

**版本號說明**:
- **主版本號 (1)**: 重大功能更新或架構變更
- **次版本號 (9)**: 新功能添加
- **修訂號 (3)**: 錯誤修正和小幅改進
- **建置號 (0)**: 建置編號

### 版本命名規則

- **穩定版本**: 使用完整版本號 (如 1.9.3.0)
- **開發版本**: 可添加後綴 (如 1.9.3-dev)
- **預覽版本**: 可添加後綴 (如 1.9.3-beta)

## 使用方式

### 在應用程式中使用

```python
from version_info import APP_NAME, APP_VERSION, APP_DESCRIPTION

print(f"應用程式名稱: {APP_NAME}")
print(f"版本號: {APP_VERSION}")
print(f"描述: {APP_DESCRIPTION}")
```

### 在打包腳本中使用

```python
# 在 PyInstaller 打包腳本中使用
version_info = "version_info.py"
```

### 在設定檔案中使用

```python
# 在 setup.json 中引用版本資訊
{
  "version": "1.9.3",
  "app_name": "VALO360 指令通"
}
```

## 版本管理策略

### 版本更新流程

1. **開發階段**: 使用開發版本號
2. **測試階段**: 使用測試版本號
3. **發布階段**: 使用正式版本號
4. **維護階段**: 發布修訂版本

### 版本號更新規則

- **主版本號**: 重大架構變更或不相容的 API 變更
- **次版本號**: 新功能添加，向後相容
- **修訂號**: 錯誤修正，向後相容
- **建置號**: 每次建置遞增

## 檔案用途

### Windows 執行檔資訊

- **檔案屬性**: 在 Windows 檔案總管中顯示版本資訊
- **相容性**: 提供應用程式相容性資訊
- **識別**: 幫助系統識別應用程式

### 應用程式內部使用

- **版本檢查**: 檢查應用程式版本
- **更新提示**: 顯示更新資訊
- **錯誤報告**: 包含版本資訊的錯誤報告

## 技術特點

### 標準化格式

- 使用標準的 Windows 版本資訊格式
- 符合 Windows 應用程式開發規範
- 提供完整的應用程式識別資訊

### 多語言支援

- 支援繁體中文 (1028)
- 使用 Unicode 編碼 (1200)
- 提供本地化的應用程式資訊

### 版本追蹤

- 詳細的版本更新記錄
- 清晰的版本號命名規則
- 完整的變更日誌

## 注意事項

### 版本號同步

- 確保所有檔案中的版本號一致
- 更新時同步修改所有相關檔案
- 檢查版本號格式的正確性

### 打包設定

- 確保 PyInstaller 正確使用版本資訊
- 檢查打包後的執行檔版本資訊
- 驗證版本資訊的顯示

### 更新日誌

- 及時記錄版本更新內容
- 保持更新日誌的準確性
- 提供詳細的功能說明

## 相依性

### 打包工具

- **PyInstaller**: 使用版本資訊進行打包
- **pywin32**: 提供 Windows 版本資訊支援

### 應用程式模組

- **config_core**: 讀取版本資訊
- **config_utils**: 提供版本號存取
- **main.py**: 顯示版本資訊

這個版本資訊模組是整個應用程式版本管理的核心，提供了完整的版本資訊定義和管理功能。 