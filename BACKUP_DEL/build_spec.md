# PyInstaller 打包規格檔案 (build_spec.py)

## 檔案概述

這個檔案定義了 PyInstaller 的打包規格，用於將 Python 應用程式打包成 Windows 執行檔。它包含了所有必要的設定，包括主程式、資料檔案、隱藏導入、排除模組等。

## 主要功能

- **打包配置**: 定義 PyInstaller 的打包參數
- **資源管理**: 指定需要包含的資料檔案和資源
- **模組控制**: 管理隱藏導入和排除的模組
- **版本整合**: 整合版本資訊到打包過程
- **輸出設定**: 配置執行檔的輸出格式和屬性

## 導入和初始化

### 基本導入

```python
import os
import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE
from PyInstaller.building.datastruct import Tree
```

**功能說明**: 
- 導入必要的系統模組
- 導入 PyInstaller 的核心類別
- 設置路徑和環境

### 路徑設置

```python
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
```

**功能說明**: 
- 獲取當前檔案目錄
- 將當前目錄加入 Python 路徑
- 確保模組能正確導入

### 版本資訊導入

```python
from version_info import APP_NAME, APP_VERSION
```

**功能說明**: 
- 導入應用程式名稱和版本號
- 用於動態生成執行檔名稱
- 整合版本資訊到打包過程

## 打包配置

### 主程式檔案

```python
main_script = 'main.py'
```

**功能說明**: 
- 指定應用程式的主入口點
- PyInstaller 將從此檔案開始分析依賴

### 資料檔案配置

```python
datas = [
    ('assets', 'assets'),
    ('Command_TABLE', 'Command_TABLE'),
    ('setup.json', '.'),
    ('version_info.py', '.'),
]
```

**功能說明**: 
- 指定需要包含在執行檔中的資料檔案
- 格式為 (來源路徑, 目標路徑)
- 確保應用程式運行時能找到必要檔案

**包含的資料**:
- **assets**: 圖示和其他資源檔案
- **Command_TABLE**: 指令表目錄
- **setup.json**: 設定檔案
- **version_info.py**: 版本資訊檔案

### 隱藏導入

```python
hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'serial',
    'threading',
    'json',
    'os',
    'sys',
    'time',
    'datetime',
    'logging',
    'subprocess',
    're',
    'configparser',
    'pathlib',
]
```

**功能說明**: 
- 指定 PyInstaller 無法自動檢測到的模組
- 確保所有必要的依賴都被包含
- 避免執行時出現模組缺失錯誤

**包含的模組類型**:
- **GUI 模組**: tkinter 相關模組
- **通訊模組**: serial 序列埠通訊
- **系統模組**: os, sys, threading
- **資料處理**: json, datetime, logging
- **工具模組**: subprocess, re, configparser

### 排除模組

```python
excludes = [
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'PIL',
    'cv2',
    'tensorflow',
    'torch',
    'sklearn',
]
```

**功能說明**: 
- 指定不需要包含的模組
- 減少執行檔大小
- 避免不必要的依賴

**排除的模組類型**:
- **科學計算**: matplotlib, numpy, pandas, scipy
- **圖像處理**: PIL, cv2
- **機器學習**: tensorflow, torch, sklearn

## 打包過程

### Analysis 階段

```python
a = Analysis(
    [main_script],
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
```

**功能說明**: 
- 分析主程式和其依賴
- 確定需要包含的檔案和模組
- 生成打包計劃

**參數說明**:
- **pathex**: Python 路徑列表
- **binaries**: 二進制檔案列表
- **datas**: 資料檔案列表
- **hiddenimports**: 隱藏導入列表
- **excludes**: 排除模組列表
- **cipher**: 加密設定（None 表示不加密）

### PYZ 階段

```python
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
```

**功能說明**: 
- 將 Python 模組打包成 PYZ 檔案
- 壓縮模組以減少檔案大小
- 準備執行檔的模組部分

### EXE 階段

```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=f'指令通_v{APP_VERSION}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不顯示控制台
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
    version='version_info.py',
)
```

**功能說明**: 
- 生成最終的執行檔
- 設定執行檔的屬性和行為
- 整合所有必要的檔案和資源

**重要參數**:
- **name**: 執行檔名稱（包含版本號）
- **console**: 是否顯示控制台（False = 隱藏）
- **icon**: 應用程式圖示
- **version**: 版本資訊檔案
- **upx**: 是否使用 UPX 壓縮

## 輸出配置

### 執行檔名稱

```python
name=f'指令通_v{APP_VERSION}'
```

**功能說明**: 
- 動態生成執行檔名稱
- 包含版本號以便識別
- 使用中文名稱符合產品定位

### 圖示設定

```python
icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None
```

**功能說明**: 
- 設定應用程式圖示
- 檢查圖示檔案是否存在
- 如果不存在則不使用圖示

### 版本資訊

```python
version='version_info.py'
```

**功能說明**: 
- 指定版本資訊檔案
- 將版本資訊嵌入執行檔
- 在 Windows 檔案屬性中顯示

## 打包選項

### 控制台設定

```python
console=False  # 不顯示控制台
```

**功能說明**: 
- 隱藏控制台視窗
- 提供純 GUI 應用程式體驗
- 避免顯示不必要的控制台

### 壓縮設定

```python
upx=True,  # 使用 UPX 壓縮
strip=False,  # 不剝離符號
```

**功能說明**: 
- 使用 UPX 進一步壓縮執行檔
- 保留除錯符號以便問題診斷
- 平衡檔案大小和除錯能力

### 除錯設定

```python
debug=False,  # 非除錯模式
disable_windowed_traceback=False,  # 啟用錯誤追蹤
```

**功能說明**: 
- 非除錯模式減少檔案大小
- 保留錯誤追蹤功能
- 提供錯誤診斷能力

## 輸出資訊

### 打包狀態

```python
print(f"✅ PyInstaller 規格文件已創建")
print(f"📦 應用程式名稱：{APP_NAME}")
print(f"🔢 版本號：{APP_VERSION}")
print(f"📁 輸出檔案：指令通_v{APP_VERSION}.exe")
```

**功能說明**: 
- 顯示打包配置狀態
- 確認應用程式資訊
- 預告輸出檔案名稱

## 使用方式

### 直接執行

```bash
python build_spec.py
```

### 使用 PyInstaller

```bash
pyinstaller build_spec.py
```

### 一鍵打包

```bash
pyinstaller --onefile --windowed build_spec.py
```

## 注意事項

### 檔案依賴

- 確保所有資料檔案都存在
- 檢查圖示檔案路徑
- 驗證版本資訊檔案

### 模組依賴

- 確認隱藏導入列表完整
- 檢查排除模組是否正確
- 測試打包後的執行檔

### 路徑設定

- 確保相對路徑正確
- 檢查檔案權限
- 驗證輸出目錄

## 技術特點

### 動態配置

- 使用版本資訊動態生成檔案名
- 根據環境調整路徑
- 靈活的模組管理

### 優化設定

- 排除不必要的模組
- 使用 UPX 壓縮
- 隱藏控制台視窗

### 完整性保證

- 包含所有必要的資料檔案
- 確保模組依賴完整
- 提供版本資訊整合

## 相依性

### PyInstaller

- **PyInstaller**: 主要的打包工具
- **UPX**: 可選的壓縮工具
- **pywin32**: Windows 版本資訊支援

### 應用程式檔案

- **main.py**: 主程式檔案
- **version_info.py**: 版本資訊檔案
- **setup.json**: 設定檔案
- **assets/**: 資源檔案目錄

這個打包規格檔案是整個應用程式發布流程的核心，確保了打包過程的可靠性和一致性。 