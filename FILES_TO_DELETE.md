# 🗑️ 可以刪除的檔案清單

## 📋 分析結果

經過檢查，以下是可以安全刪除或移動的檔案：

---

## ✅ 可以安全刪除的檔案

### 1. 備份檔案（已過時）
```
❌ config.py.bak                          (13,019 bytes)
   → 原因：舊的 config.py 備份，現在已改用 config_core.py
   → 建議：刪除

❌ setup.json.backup_before_ssh_20250909_115312  (2,066 bytes)
   → 原因：2025年9月的舊備份，已經過時
   → 建議：刪除
```

### 2. 舊版本 spec 檔案（保留最新即可）
```
❌ PEGA指令通_V2.1.5.spec                (1,134 bytes)
   → 原因：舊版本
   → 建議：刪除或移至 build_scripts/archive/

❌ PEGA指令通_V2.5.0.spec                (1,134 bytes)
   → 原因：舊版本
   → 建議：刪除或移至 build_scripts/archive/

❌ PEGA指令通_V2.5.1.spec                (1,134 bytes)
   → 原因：舊版本
   → 建議：刪除或移至 build_scripts/archive/

✅ PEGA指令通_V2.5.41.spec               (1,135 bytes)
   → 原因：最新版本
   → 建議：保留並移至 build_scripts/
```

### 3. 臨時/測試檔案
```
❌ temp_line.txt                          (104 bytes)
   → 原因：臨時檔案
   → 建議：刪除

❌ error_log.txt                          (334 bytes)
   → 原因：舊的錯誤日誌，現在使用 logs/ 目錄
   → 建議：刪除或移至 logs/
```

### 4. 重複的文件檔案
```
❌ VALO360 指令 - 複製.txt               (3,328 bytes)
   → 原因：檔名有「複製」，可能是重複檔案
   → 建議：檢查內容後刪除
```

---

## 📁 建議移動的檔案

### 移至 docs/
```
→ GUI_ARCHITECTURE.txt                   (27,779 bytes)
→ GUI_ARCHITECTURE_SIMPLE.txt            (3,505 bytes)
→ PEGA指令通使用說明.html               (18,249 bytes)
→ version_info_zh.txt                    (864 bytes)
→ ssh_handler_patch.txt                  (5,086 bytes)
→ build_manual_commands.txt              (1,971 bytes)
→ REFACTORING_COMPARISON.txt             (18,565 bytes)
→ VALO360 指令 - 複製.txt               (3,328 bytes) - 檢查後
```

### 移至 build_scripts/
```
→ build_PEGA_final.bat
→ PEGA指令通_V2.5.41.spec               (最新版本)
```

### 移至 build_scripts/archive/（舊版本）
```
→ PEGA指令通_V2.1.5.spec
→ PEGA指令通_V2.5.0.spec
→ PEGA指令通_V2.5.1.spec
```

### 移至 logs/（如果要保留）
```
→ error_log.txt
→ run_log.txt
```

---

## ⚠️ 需要保留的檔案

### 程式運行必需
```
✅ command.txt                            (9,896 bytes) - 指令檔案
✅ color_word.txt                         (507 bytes) - 顏色設定
✅ sign_DOC.txt                           (11 bytes) - 簽名文件
✅ user_guide.txt                         (2,063 bytes) - 使用指南
✅ readROVO.txt                           (5,521 bytes) - 讀取設定
✅ tooltip_config.txt                     (4,447 bytes) - 提示設定
✅ requirements.txt                       (134 bytes) - Python 依賴
✅ .gitignore                             (696 bytes) - Git 設定
```

### 文件和指南
```
✅ README_FOR_AI.md                       (4,715 bytes) - AI 指南
✅ REFACTORED_WARNING.txt                 (7,976 bytes) - 重構警告
```

---

## 🎯 建議的清理步驟

### 步驟 1: 刪除確定不需要的檔案
```powershell
# 刪除舊備份
Remove-Item "config.py.bak"
Remove-Item "setup.json.backup_before_ssh_20250909_115312"

# 刪除臨時檔案
Remove-Item "temp_line.txt"

# 刪除舊 spec 檔案（或移至 archive）
Remove-Item "PEGA指令通_V2.1.5.spec"
Remove-Item "PEGA指令通_V2.5.0.spec"
Remove-Item "PEGA指令通_V2.5.1.spec"
```

### 步驟 2: 移動文件到 docs/
```powershell
Move-Item "GUI_ARCHITECTURE.txt" "docs\"
Move-Item "GUI_ARCHITECTURE_SIMPLE.txt" "docs\"
Move-Item "PEGA指令通使用說明.html" "docs\"
Move-Item "version_info_zh.txt" "docs\"
Move-Item "ssh_handler_patch.txt" "docs\"
Move-Item "build_manual_commands.txt" "docs\"
Move-Item "REFACTORING_COMPARISON.txt" "docs\"
```

### 步驟 3: 建立並移動到 build_scripts/
```powershell
New-Item -ItemType Directory -Path "build_scripts"
Move-Item "build_PEGA_final.bat" "build_scripts\"
Move-Item "PEGA指令通_V2.5.41.spec" "build_scripts\"
```

### 步驟 4: 移動日誌（可選）
```powershell
# 如果要整理日誌
Move-Item "error_log.txt" "logs\" -ErrorAction SilentlyContinue
Move-Item "run_log.txt" "logs\" -ErrorAction SilentlyContinue
```

---

## 📊 清理效果預估

### 刪除檔案
- **數量**: 6-7 個檔案
- **大小**: ~20 KB

### 移動檔案
- **移至 docs/**: 7-8 個檔案 (~75 KB)
- **移至 build_scripts/**: 5 個檔案 (~5 KB)

### 最終根目錄
- **保留**: ~15 個必要檔案
- **清理度**: 減少 50% 的檔案數量

---

## ✅ 最終根目錄結構

```
360-command-tool/
├── MAIN.PY                       ← 主程式
├── README_FOR_AI.md              ← AI 指南
├── REFACTORED_WARNING.txt        ← 重構警告
├── requirements.txt              ← 依賴清單
├── .gitignore                    ← Git 設定
│
├── command.txt                   ← 指令檔案
├── color_word.txt                ← 顏色設定
├── sign_DOC.txt                  ← 簽名文件
├── user_guide.txt                ← 使用指南
├── readROVO.txt                  ← 讀取設定
├── tooltip_config.txt            ← 提示設定
│
├── setup.json                    ← 設定檔案
├── tooltips.ini                  ← 提示配置
│
├── docs/                         ← 所有文件
├── build_scripts/                ← 建置腳本
├── logs/                         ← 日誌檔案
├── transport/                    ← Worker 模組
├── ui_parts/                     ← UI 模組
└── ... (其他目錄)
```

---

## 🎯 總結

### 可以刪除
- ✅ `config.py.bak` - 舊備份
- ✅ `setup.json.backup_before_ssh_20250909_115312` - 舊備份
- ✅ `temp_line.txt` - 臨時檔案
- ✅ `PEGA指令通_V2.1.5.spec` - 舊版本
- ✅ `PEGA指令通_V2.5.0.spec` - 舊版本
- ✅ `PEGA指令通_V2.5.1.spec` - 舊版本

### 需要移動
- 📁 8 個文件檔案 → `docs/`
- 📁 2 個建置檔案 → `build_scripts/`
- 📁 2 個日誌檔案 → `logs/`（可選）

---

**您想要我執行這些清理嗎？** 😊
