# 動態版本號打包系統 - 更新說明

## 📋 更新日期
2026-02-11

## ✅ 完成項目

### 1. 動態版本號讀取功能

#### 新增檔案：`get_version.py`
- **功能**：從 `setup.json` 讀取版本號
- **用途**：供 BAT 檔案呼叫，實現動態版本號
- **容錯**：讀取失敗時返回預設版本號 2.5.0

#### 修改檔案：`build_PEGA_final.bat`
**修改內容**：
1. **初始化階段**（第 4-10 行）
   - 新增版本號讀取邏輯
   - 使用 `python get_version.py` 獲取版本號
   - 設定環境變數 `%APP_VERSION%`
   - 包含容錯處理

2. **標題顯示**（第 14 行）
   ```batch
   echo    PEGA指令通 V%APP_VERSION% 打包程序
   ```

3. **PyInstaller 命令**（第 79 行）
   ```batch
   --name "PEGA指令通_V%APP_VERSION%" ^
   ```

4. **檢查結果**（第 100、105、106 行）
   ```batch
   if exist "dist\PEGA指令通_V%APP_VERSION%.exe" (
       echo 輸出文件: dist\PEGA指令通_V%APP_VERSION%.exe
       dir "dist\PEGA指令通_V%APP_VERSION%.exe"
   ```

### 2. GUI 架構圖

#### 新增檔案：`GUI_ARCHITECTURE.txt`
- **格式**：ASCII 藝術圖
- **內容**：
  - 完整的模組架構圖
  - 5 個主要標籤頁說明
  - UI 組件模組分類
  - 功能處理模組
  - 輔助功能模組
  - 傳輸層模組（Console/ADB/SSH）
  - 設定與資料檔案
  - 資料流向圖
  - 關鍵特性列表

## 🎯 使用方式

### 更新版本號
只需修改 `setup.json` 中的版本號：
```json
{
  "version": "2.5.5",
  ...
}
```

### 執行打包
直接執行 `build_PEGA_final.bat`，會自動：
1. 讀取 setup.json 的版本號
2. 顯示版本號在打包標題
3. 使用版本號命名 EXE 檔案
4. 檢查對應版本號的 EXE 是否生成成功

### 範例輸出
```
[初始化] 讀取版本號...

========================================
   PEGA指令通 V2.5.4 打包程序
========================================

...

輸出文件: dist\PEGA指令通_V2.5.4.exe
```

## 📊 架構圖說明

### 主要模組層級
```
main.py
  └─ core/ (核心模組)
      ├─ config_manager.py
      ├─ error_handler.py
      ├─ resource_manager.py
      ├─ async_manager.py
      └─ performance_monitor.py
  
  └─ ui_parts/ (UI 模組)
      ├─ ui_main.py (主介面管理器)
      ├─ 標籤頁模組 (5 個)
      │   ├─ ui_components.py (TAB 1: DUT 控制)
      │   ├─ ui_manual_command.py (TAB 2: 手打指令)
      │   ├─ ui_dos_tab.py (TAB 3: DOS 批次檔)
      │   ├─ ui_settings_tab.py (TAB 4: 設定我)
      │   └─ ui_startup_label.py (啟動標籤)
      ├─ UI 組件模組
      │   ├─ ui_components_base.py
      │   ├─ ui_components_input.py
      │   ├─ ui_components_output.py
      │   └─ ui_components_settings.py
      ├─ 功能處理模組
      │   ├─ ui_handlers.py
      │   ├─ command_processor.py
      │   └─ ui_handlers_core.py
      └─ 輔助功能模組
          ├─ tooltip.py
          ├─ notification_manager.py
          ├─ font_manager.py
          ├─ shared_config.py
          └─ ui_tab_manager.py
  
  └─ 傳輸層模組
      ├─ serial_worker.py (Console 模式)
      ├─ adb_worker.py (ADB 模式)
      └─ ssh_worker.py (SSH 模式)
```

## 🔄 資料流向
```
使用者操作
  ↓
UI 元件
  ↓
事件處理器 (ui_handlers.py)
  ↓
指令處理器 (command_processor.py)
  ↓
傳輸層 (serial/adb/ssh_worker.py)
  ↓
裝置/系統回應
  ↓
結果處理與顯示
  ↓
UI 更新 & 設定儲存
```

## 💡 優點

### 動態版本號系統
✓ 單一來源真實（setup.json）
✓ 自動同步，無需手動修改多處
✓ 減少人為錯誤
✓ 容錯機制完善

### 架構圖
✓ 清晰的模組關係
✓ 完整的功能說明
✓ 易於理解和維護
✓ 便於新成員快速上手

## 📝 注意事項

1. **版本號格式**：建議使用 `X.Y.Z` 格式（如 2.5.4）
2. **setup.json 編碼**：必須使用 UTF-8 編碼
3. **Python 環境**：確保 Python 在系統 PATH 中
4. **檔案完整性**：打包前確認 get_version.py 存在

## 🚀 下次打包流程

1. 修改 `setup.json` 中的 `version` 欄位
2. 執行 `build_PEGA_final.bat`
3. 等待打包完成
4. 在 `dist/` 目錄找到對應版本的 EXE

---
**建立者**: Antigravity AI
**更新日期**: 2026-02-11
