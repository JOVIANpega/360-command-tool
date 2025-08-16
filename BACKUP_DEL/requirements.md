# 依賴套件清單 (requirements.txt)

## 檔案概述

這個檔案定義了應用程式運行所需的所有 Python 套件及其版本要求。它確保了開發環境和部署環境的一致性，並提供了清晰的依賴管理。

## 主要功能

- **依賴管理**: 列出所有必要的 Python 套件
- **版本控制**: 指定套件的最低版本要求
- **環境一致性**: 確保不同環境下的套件版本一致
- **部署支援**: 支援自動化部署和環境設置

## 套件清單

### pyserial>=3.5

**功能說明**: 
序列埠通訊套件，提供跨平台的序列埠存取功能。

**主要用途**:
- 建立和管理序列埠連接
- 發送和接收序列埠資料
- 支援多種序列埠參數設定
- 提供錯誤處理和狀態監控

**版本要求**: 
- 最低版本：3.5
- 確保穩定的序列埠通訊功能
- 支援最新的序列埠標準

**使用場景**:
- DUT 控制頁面的序列埠通訊
- 治具控制頁面的序列埠通訊
- 指令執行和資料接收

### tkinter

**功能說明**: 
Python 的標準 GUI 套件，提供圖形使用者介面功能。

**主要用途**:
- 創建應用程式視窗和對話框
- 提供各種 GUI 元件（按鈕、標籤、輸入框等）
- 處理使用者事件和互動
- 支援佈局管理和樣式設定

**版本要求**: 
- 內建於 Python 標準庫
- 無需額外安裝
- 確保跨平台相容性

**使用場景**:
- 主應用程式視窗
- 設定對話框
- 錯誤訊息顯示
- 檔案選擇對話框

### pyinstaller>=5.6.2

**功能說明**: 
Python 應用程式打包工具，將 Python 程式打包成執行檔。

**主要用途**:
- 將 Python 應用程式打包成 Windows 執行檔
- 包含所有必要的依賴和資源檔案
- 支援單檔案和多檔案打包模式
- 提供版本資訊和圖示設定

**版本要求**: 
- 最低版本：5.6.2
- 確保穩定的打包功能
- 支援最新的 Python 版本

**使用場景**:
- 應用程式發布和分發
- 建立可執行檔案
- 整合版本資訊和圖示
- 優化檔案大小和啟動速度

### psutil

**功能說明**: 
跨平台的系統和進程監控套件，提供系統資源資訊。

**主要用途**:
- 監控系統資源使用情況
- 管理進程和執行緒
- 獲取系統資訊（CPU、記憶體、磁碟等）
- 支援跨平台系統監控

**版本要求**: 
- 最新版本
- 確保穩定的系統監控功能
- 支援多種作業系統

**使用場景**:
- 系統資源監控
- 進程管理
- 性能監控
- 系統資訊顯示

## 安裝方式

### 使用 pip 安裝

```bash
pip install -r requirements.txt
```

**功能說明**: 
- 自動安裝所有列出的套件
- 確保版本要求符合
- 處理套件依賴關係

### 個別安裝

```bash
pip install pyserial>=3.5
pip install pyinstaller>=5.6.2
pip install psutil
```

**功能說明**: 
- 可以個別安裝特定套件
- 便於除錯和測試
- 支援自定義安裝選項

### 虛擬環境安裝

```bash
# 創建虛擬環境
python -m venv venv

# 啟動虛擬環境
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# 安裝套件
pip install -r requirements.txt
```

**功能說明**: 
- 創建獨立的 Python 環境
- 避免套件版本衝突
- 便於環境管理和部署

## 版本管理策略

### 版本號格式

```
套件名稱>=最低版本
```

**格式說明**:
- **>=**: 大於等於指定版本
- **==**: 等於指定版本
- **~=**: 相容版本（允許修訂號更新）

### 版本選擇原則

- **穩定性**: 選擇經過驗證的穩定版本
- **相容性**: 確保與其他套件的相容性
- **功能**: 確保包含所需的功能
- **安全性**: 選擇修復了安全漏洞的版本

## 開發環境設置

### 基本環境

```bash
# 安裝 Python 3.8+
# 安裝 pip
# 安裝 Git（可選）

# 克隆專案
git clone <repository_url>
cd <project_directory>

# 安裝依賴
pip install -r requirements.txt
```

### 開發工具

```bash
# 安裝開發工具（可選）
pip install black  # 程式碼格式化
pip install flake8  # 程式碼檢查
pip install pytest  # 單元測試
```

## 部署環境設置

### 生產環境

```bash
# 在生產伺服器上
python -m venv production_env
source production_env/bin/activate
pip install -r requirements.txt
```

### 打包環境

```bash
# 在打包機器上
pip install pyinstaller>=5.6.2
python build_spec.py
```

## 套件更新策略

### 定期更新

- **每月檢查**: 檢查套件是否有安全更新
- **季度更新**: 評估新版本的功能和穩定性
- **年度審查**: 全面評估套件依賴

### 更新流程

1. **測試環境**: 在測試環境中驗證新版本
2. **功能測試**: 確保所有功能正常運作
3. **性能測試**: 檢查性能是否有影響
4. **相容性測試**: 確保與其他套件相容
5. **生產部署**: 在生產環境中部署

## 故障排除

### 常見問題

#### 套件安裝失敗

```bash
# 更新 pip
pip install --upgrade pip

# 清除快取
pip cache purge

# 使用國內鏡像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

#### 版本衝突

```bash
# 檢查套件版本
pip list

# 解決衝突
pip install --upgrade <package_name>
```

#### 權限問題

```bash
# 使用用戶安裝
pip install --user -r requirements.txt

# 或使用虛擬環境
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 注意事項

### 版本相容性

- 確保所有套件版本相容
- 測試新版本的功能
- 記錄版本變更的影響

### 安全性

- 定期更新套件以修復安全漏洞
- 使用可信的套件來源
- 檢查套件的安全記錄

### 性能影響

- 監控套件對應用程式性能的影響
- 選擇輕量級的套件
- 避免不必要的依賴

## 相依性圖

```
應用程式
├── pyserial (序列埠通訊)
├── tkinter (GUI 介面)
├── pyinstaller (打包工具)
└── psutil (系統監控)
```

這個依賴套件清單是整個應用程式開發和部署的基礎，確保了環境的一致性和功能的完整性。 