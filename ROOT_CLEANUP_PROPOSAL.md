# 📁 根目錄整理建議

## 📋 現況分析

根目錄目前有很多散落的檔案，建議整理成以下結構：

---

## 🎯 建議的目錄結構

```
360-command-tool/
├── MAIN.PY                       ← 主程式（保留在根目錄）
├── README_FOR_AI.md              ← AI 指南（保留在根目錄）
├── REFACTORED_WARNING.txt        ← 重構警告（保留在根目錄）
├── requirements.txt              ← 依賴清單（保留在根目錄）
├── .gitignore                    ← Git 設定（保留在根目錄）
│
├── config/                       ← 配置檔案目錄（新建）
│   ├── setup.json
│   ├── tooltips.ini
│   ├── tooltip_config.txt
│   └── config.py.bak
│
├── data/                         ← 資料檔案目錄（新建）
│   ├── command.txt
│   ├── color_word.txt
│   ├── sign_DOC.txt
│   ├── user_guide.txt
│   └── readROVO.txt
│
├── logs/                         ← 日誌檔案目錄（新建）
│   ├── run_log.txt
│   ├── error_log.txt
│   └── temp_line.txt
│
├── build_scripts/                ← 建置腳本目錄（新建）
│   ├── build_PEGA_final.bat
│   ├── PEGA指令通_V2.5.41.spec
│   ├── PEGA指令通_V2.5.1.spec
│   ├── PEGA指令通_V2.5.0.spec
│   └── PEGA指令通_V2.1.5.spec
│
├── docs/                         ← 文件目錄（已存在）
│   ├── INDEX.md
│   ├── FINAL_SUMMARY.md
│   ├── GUI_ARCHITECTURE.txt
│   ├── GUI_ARCHITECTURE_SIMPLE.txt
│   ├── PEGA指令通使用說明.html
│   ├── VALO360 指令 - 複製.txt
│   ├── version_info_zh.txt
│   ├── ssh_handler_patch.txt
│   ├── build_manual_commands.txt
│   ├── REFACTORING_COMPARISON.txt
│   └── ... (其他 MD 檔案)
│
├── transport/                    ← Worker 模組（已存在）
├── ui_parts/                     ← UI 模組（已存在）
├── core/                         ← 核心模組（已存在）
├── Command_TABLE/                ← 指令表（已存在）
├── assets/                       ← 資源檔案（已存在）
├── BACKUP_DEL/                   ← 舊版本備份（已存在）
├── backup/                       ← 設定備份（已存在）
├── build/                        ← 建置輸出（已存在）
└── dist/                         ← 發布檔案（已存在）
```

---

## 📂 整理方案

### 方案 A：完整整理（推薦）

**優點**：
- ✅ 根目錄非常乾淨
- ✅ 檔案分類清楚
- ✅ 易於維護

**缺點**：
- ⚠️ 需要修改一些程式碼中的路徑
- ⚠️ 需要更新 setup.json 中的路徑

**建議移動**：
1. **config/** - 所有配置檔案
   - `setup.json`
   - `tooltips.ini`
   - `tooltip_config.txt`
   - `config.py.bak`

2. **data/** - 所有資料檔案
   - `command.txt`
   - `color_word.txt`
   - `sign_DOC.txt`
   - `user_guide.txt`
   - `readROVO.txt`

3. **logs/** - 所有日誌檔案
   - `run_log.txt`
   - `error_log.txt`
   - `temp_line.txt`

4. **build_scripts/** - 所有建置相關檔案
   - `build_PEGA_final.bat`
   - `*.spec` 檔案

5. **docs/** - 所有文件（已部分完成）
   - `GUI_ARCHITECTURE.txt`
   - `GUI_ARCHITECTURE_SIMPLE.txt`
   - `PEGA指令通使用說明.html`
   - `version_info_zh.txt`
   - `ssh_handler_patch.txt`
   - `build_manual_commands.txt`
   - `REFACTORING_COMPARISON.txt`
   - `VALO360 指令 - 複製.txt`

---

### 方案 B：保守整理（較安全）

**優點**：
- ✅ 不需要修改程式碼
- ✅ 風險較低
- ✅ 快速完成

**缺點**：
- ⚠️ 根目錄仍有一些檔案

**建議移動**：
1. **docs/** - 只移動文件類檔案
   - `GUI_ARCHITECTURE.txt`
   - `GUI_ARCHITECTURE_SIMPLE.txt`
   - `PEGA指令通使用說明.html`
   - `version_info_zh.txt`
   - `ssh_handler_patch.txt`
   - `build_manual_commands.txt`
   - `REFACTORING_COMPARISON.txt`
   - `VALO360 指令 - 複製.txt`

2. **build_scripts/** - 只移動建置相關檔案
   - `build_PEGA_final.bat`
   - `*.spec` 檔案

3. **保留在根目錄**：
   - `setup.json` - 程式需要
   - `tooltips.ini` - 程式需要
   - `command.txt` - 程式需要
   - `run_log.txt` - 程式需要
   - 其他程式運行時需要的檔案

---

### 方案 C：最小整理（最安全）

**優點**：
- ✅ 完全不影響程式運行
- ✅ 零風險

**缺點**：
- ⚠️ 根目錄仍較雜亂

**建議移動**：
1. **docs/** - 只移動純文件檔案
   - `GUI_ARCHITECTURE.txt`
   - `GUI_ARCHITECTURE_SIMPLE.txt`
   - `ssh_handler_patch.txt`
   - `build_manual_commands.txt`
   - `REFACTORING_COMPARISON.txt`

2. **其他全部保留在根目錄**

---

## 💡 我的建議

**推薦方案 B（保守整理）**

原因：
1. ✅ 可以讓根目錄變乾淨
2. ✅ 不需要修改程式碼
3. ✅ 風險低，易於回退
4. ✅ 快速完成

---

## 🚀 執行步驟（方案 B）

### 步驟 1: 移動文件到 docs/
```powershell
Move-Item "GUI_ARCHITECTURE.txt" "docs\"
Move-Item "GUI_ARCHITECTURE_SIMPLE.txt" "docs\"
Move-Item "PEGA指令通使用說明.html" "docs\"
Move-Item "version_info_zh.txt" "docs\"
Move-Item "ssh_handler_patch.txt" "docs\"
Move-Item "build_manual_commands.txt" "docs\"
Move-Item "REFACTORING_COMPARISON.txt" "docs\"
Move-Item "VALO360 指令 - 複製.txt" "docs\"
```

### 步驟 2: 建立 build_scripts/ 並移動建置檔案
```powershell
New-Item -ItemType Directory -Path "build_scripts"
Move-Item "build_PEGA_final.bat" "build_scripts\"
Move-Item "PEGA指令通_V*.spec" "build_scripts\"
```

### 步驟 3: 更新 .gitignore
```
# Logs
logs/
*.log
run_log.txt
error_log.txt
temp_line.txt
```

### 步驟 4: 提交到 Git
```powershell
git add .
git commit -m "📁 整理根目錄檔案"
git push
```

---

## ❓ 您想選擇哪個方案？

- **方案 A**：完整整理（需要修改程式碼）
- **方案 B**：保守整理（推薦，不需修改程式碼）✨
- **方案 C**：最小整理（最安全）

請告訴我您的選擇，我會幫您執行！😊
