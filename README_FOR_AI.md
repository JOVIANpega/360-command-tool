# 🤖 給未來 AI 的重要提示

## 📚 本專案有完整的文件庫！

**在開始任何工作之前，請先閱讀 `docs/` 目錄中的文件！**

---

## 🎯 快速開始

### 1. 先讀這個！
👉 **[docs/INDEX.md](docs/INDEX.md)** - 文件索引，列出所有可用文件

### 2. 了解專案狀態
👉 **[docs/REFACTORING_SUMMARY.md](docs/REFACTORING_SUMMARY.md)** - 重構總結
👉 **[docs/IMPORT_FIX_AND_DOCS_CLEANUP.md](docs/IMPORT_FIX_AND_DOCS_CLEANUP.md)** - 最新修復報告

### 3. 如果遇到問題
👉 **[docs/HOW_TO_ROLLBACK.md](docs/HOW_TO_ROLLBACK.md)** - 回退指南
👉 **[REFACTORED_WARNING.txt](REFACTORED_WARNING.txt)** - 重構警告

---

## 🔍 重要資訊

### 專案已完成重構（2026-02-11）

**新架構**：
```
transport/
├── base_worker.py           ← 基礎類別（共用邏輯）
├── serial_worker_v2.py      ← Console 工作器
├── adb_worker_v2.py         ← ADB 工作器
└── ssh_worker_v2.py         ← SSH 工作器
```

**舊版本備份**：
```
BACKUP_DEL/
├── serial_worker.py
├── adb_worker.py
└── ssh_worker.py
```

### 重構效益
- ✅ 減少 70% 重複程式碼
- ✅ 修改 DELAY 邏輯：只需改 1 個檔案（vs 舊版 3 個檔案）
- ✅ 新增功能：修改量減少 67%
- ✅ 不會交叉影響

---

## 📋 文件分類

### 🔧 重構相關（必讀）
- `docs/REFACTORING_SUMMARY.md` - 重構總結
- `docs/REFACTORING_COMPLETE_REPORT.md` - 完整報告
- `docs/REFACTORING_BENEFIT_PROOF.md` - 效益證明
- `docs/HOW_TO_ROLLBACK.md` - 回退指南

### 🐛 問題修復
- `docs/TIMEOUT_FIX_REPORT.md` - 超時邏輯修復
- `docs/DELAY_FIX_REPORT.md` - 延遲問題修復
- `docs/ADB_SSH_CHECK_REPORT.md` - ADB/SSH 檢查

### 📚 其他文件
- `docs/CHANGELOG.md` - 變更日誌
- `docs/README.md` - 專案說明
- 更多請查看 `docs/INDEX.md`

---

## ⚠️ 重要注意事項

### 1. 不要直接修改舊版本檔案
❌ **不要修改**：
- `BACKUP_DEL/serial_worker.py`
- `BACKUP_DEL/adb_worker.py`
- `BACKUP_DEL/ssh_worker.py`

✅ **應該修改**：
- `transport/serial_worker_v2.py`
- `transport/adb_worker_v2.py`
- `transport/ssh_worker_v2.py`
- `transport/base_worker.py`

### 2. 修改共用邏輯
如果要修改 DELAY、SHOW、進度管理等共用邏輯：
- ✅ 只需修改 `transport/base_worker.py`
- ✅ 三個 worker 會自動繼承

### 3. 修改傳輸特定邏輯
如果要修改序列埠、ADB、SSH 的特定邏輯：
- ✅ 修改對應的 `transport/xxx_worker_v2.py`
- ✅ 不會影響其他 worker

---

## 🚀 開始工作前的檢查清單

- [ ] 已閱讀 `docs/INDEX.md`
- [ ] 已閱讀 `docs/REFACTORING_SUMMARY.md`
- [ ] 了解新架構（`transport/` 目錄）
- [ ] 知道舊版本在 `BACKUP_DEL/`
- [ ] 知道如何回退（`docs/HOW_TO_ROLLBACK.md`）

---

## 📞 需要幫助？

1. **查看文件索引**：`docs/INDEX.md`
2. **查看重構總結**：`docs/REFACTORING_SUMMARY.md`
3. **查看最新修復**：`docs/IMPORT_FIX_AND_DOCS_CLEANUP.md`
4. **查看回退指南**：`docs/HOW_TO_ROLLBACK.md`

---

## 🎯 專案結構

```
360-command-tool/
├── README_FOR_AI.md              ← 你正在讀這個！
├── REFACTORED_WARNING.txt        ← 重構警告
│
├── docs/                         ← 📚 所有文件在這裡！
│   ├── INDEX.md                 ← 文件索引（先讀這個）
│   ├── REFACTORING_SUMMARY.md   ← 重構總結（必讀）
│   └── ... (17 個 MD 檔案)
│
├── transport/                    ← 新版本 worker（使用中）
│   ├── base_worker.py
│   ├── serial_worker_v2.py
│   ├── adb_worker_v2.py
│   └── ssh_worker_v2.py
│
├── BACKUP_DEL/                   ← 舊版本備份（不要修改）
│   ├── serial_worker.py
│   ├── adb_worker.py
│   └── ssh_worker.py
│
└── ... (其他檔案)
```

---

**建立日期**: 2026-02-11
**建立者**: Antigravity AI
**目的**: 幫助未來的 AI 快速了解專案狀態和找到相關文件

---

## 💡 提示

**如果你是新接手的 AI，請務必先花 5 分鐘閱讀以下文件：**

1. `docs/INDEX.md` - 了解有哪些文件
2. `docs/REFACTORING_SUMMARY.md` - 了解重構做了什麼
3. `docs/IMPORT_FIX_AND_DOCS_CLEANUP.md` - 了解最新狀態

**這將幫助你避免：**
- ❌ 修改錯誤的檔案（舊版本 vs 新版本）
- ❌ 重複已經解決的問題
- ❌ 破壞現有的架構

**祝你工作順利！** 😊

---

## 📦 打包系統與部署 (v2.5.6 更新)

**重要：本專案已廢棄 `.spec` 文件打包方式，全面改用 Python 腳本建置。**

### 1. 建置方式
- **唯一入口**：`build_scripts/build_PEGA_final.bat`
- **核心腳本**：`build_scripts/build_final.py`
- **輸出目錄**：專案根目錄下的 `dist/`

### 2. 關鍵技術細節 (AI 必讀)

#### A. 資源路徑管理 (`core/resource_manager.py`)
本專案採用智慧路徑解析，以解決 PyInstaller `_MEIPASS` 與本地開發環境的路徑差異：
- **開發環境**：直接讀取專案目錄下的檔案。
- **打包環境 (Onedir)**：讀取 EXE 同級目錄下的檔案。
- **打包環境 (Onefile)**：優先讀取 `sys._MEIPASS` 內的資源，但允許外部檔案 (如 `setup.json`) 覆蓋。
- **🚨 特殊重定向**：為了相容舊代碼，所有對 `Fixture_Command.txt` 的請求（即使路徑錯誤指向 `Command_TABLE/`），都會被 `resource_manager` 強制導向到正確的 `FIXTURE/Fixture_Command.txt`。

#### B. SSH 與 Cryptography 崩潰問題
SSH 功能依賴 `paramiko` 與 `cryptography`，這兩個庫在 PyInstaller 打包時極易出錯（特別是 Rust bindings）。
- **解決方案 1 (腳本面)**：在 `build_final.py` 中使用 `--collect-all cryptography` 與 `--collect-all paramiko` 強制收集所有二進位依賴。
- **解決方案 2 (代碼面)**：在 `transport/ssh_worker_v2.py` 中，移除了頂層的 Type Hint (`Optional[paramiko.SSHClient]`)，避免在模組導入時觸發 `NoneType` 錯誤。

#### C. 遞歸資源複製
為了確保 `Command_TABLE` 內的子目錄與所有指令檔都能被讀取，打包腳本會執行 **後處理 (Post-processing)**，將整個 `Command_TABLE` 與 `FIXTURE` 目錄完整複製到 `dist/` 中。

### 3. 未來維護指南
- 若要新增資源檔案：請在 `build_final.py` 的 `add_data` 列表與 `files_to_copy` 列表中同步新增。
- 若要修改打包參數：直接修改 `build_final.py`，**不要** 修改 `.spec` 檔（因為它們是自動生成的，且已被 gitignore）。
- 若遇到 `ImportError`：請檢查 `build_final.py` 中的 `hidden_imports` 列表。
