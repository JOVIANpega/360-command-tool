# 🔄 重構回退指南

## ⚠️ 重要提示給未來的 AI

如果您看到這個文件，表示此專案已經進行過重構。
如果重構版本出現問題，請按照以下步驟回退到舊版本。

---

## 📅 重構資訊

- **重構日期**: 2026-02-11
- **重構內容**: Worker 模組重構（Console, ADB, SSH）
- **重構原因**: 消除重複程式碼，避免交叉影響
- **重構方式**: 並行開發（舊版本保留）

---

## 🔄 如何回退（< 1 分鐘）

### 步驟 1: 修改 `ui_parts/command_processor.py`

找到第 11-14 行：
```python
# 使用重構版本的 worker (V2)
from transport.serial_worker_v2 import SerialWorkerV2
from transport.adb_worker_v2 import ADBWorkerV2
```

改回：
```python
from serial_worker import SerialWorker
from adb_worker import ADBWorker
```

找到第 189 行：
```python
self.adb_worker = ADBWorkerV2(
```

改回：
```python
self.adb_worker = ADBWorker(
```

找到第 215 行：
```python
self.serial_worker = SerialWorkerV2(
```

改回：
```python
self.serial_worker = SerialWorker(
```

---

### 步驟 2: 修改 `ui_parts/ui_handlers.py`

找到第 1620-1622 行：
```python
from transport.adb_worker_v2 import ADBWorkerV2
self.parent.thread = ADBWorkerV2(
```

改回：
```python
from adb_worker import ADBWorker
self.parent.thread = ADBWorker(
```

找到第 1633-1634 行：
```python
from transport.ssh_worker_v2 import SSHWorkerV2
```

改回：
```python
from ssh_worker import SSHWorker
```

找到第 1648 行：
```python
self.parent.thread = SSHWorkerV2(
```

改回：
```python
self.parent.thread = SSHWorker(
```

找到第 1663-1665 行：
```python
from transport.serial_worker_v2 import SerialWorkerV2
self.parent.thread = SerialWorkerV2(
```

改回：
```python
from serial_worker import SerialWorker
self.parent.thread = SerialWorker(
```

找到第 1815-1818 行（第二處）：
```python
from transport.adb_worker_v2 import ADBWorkerV2
self.parent.thread = ADBWorkerV2(
```

改回：
```python
from adb_worker import ADBWorker
self.parent.thread = ADBWorker(
```

找到第 1827-1829 行：
```python
from transport.ssh_worker_v2 import SSHWorkerV2
```

改回：
```python
from ssh_worker import SSHWorker
```

找到第 1845 行：
```python
self.parent.thread = SSHWorkerV2(
```

改回：
```python
self.parent.thread = SSHWorker(
```

找到第 1855-1857 行：
```python
from transport.serial_worker_v2 import SerialWorkerV2
self.parent.thread = SerialWorkerV2(
```

改回：
```python
from serial_worker import SerialWorker
self.parent.thread = SerialWorker(
```

---

### 步驟 3: 重啟程式

關閉程式 → 重新開啟 → 恢復舊版本

---

## 📁 檔案位置

### 舊版本（保留，未刪除）
```
根目錄/
├── serial_worker.py             ← 舊版本 Console 工作器
├── adb_worker.py                ← 舊版本 ADB 工作器
└── ssh_worker.py                ← 舊版本 SSH 工作器
```

### 新版本（V2）
```
transport/
├── base_worker.py               ← 基礎類別
├── serial_worker_v2.py          ← 新版本 Console 工作器
├── adb_worker_v2.py             ← 新版本 ADB 工作器
└── ssh_worker_v2.py             ← 新版本 SSH 工作器
```

### 已修改的檔案
```
ui_parts/
├── command_processor.py         ← 已切換到 V2（需要回退）
└── ui_handlers.py               ← 已切換到 V2（需要回退）
```

---

## 🐛 已知問題與修復

### 問題 1: 指令執行超時（已修復）

**症狀**：
```
[錯誤] 指令執行超時 (1.0s)
```

**原因**：
- 單個指令超時設定太短

**修復**：
- 已在 `transport/base_worker.py` 中修復
- 移除了重複輸出 stdout 的問題

**如果仍有問題**：
- 檢查 `setup.json` 中的 `Single_Command_Timeout` 設定
- 建議設定為 10.0 或更高

---

## ✅ 回退檢查清單

回退後請確認：

- [ ] 修改 `ui_parts/command_processor.py` (3 處)
- [ ] 修改 `ui_parts/ui_handlers.py` (10 處)
- [ ] 重啟程式
- [ ] 測試 Console 模式
- [ ] 測試 ADB 模式（如果可用）
- [ ] 測試 SSH 模式（如果可用）

---

## 📞 聯絡資訊

如果回退後仍有問題：

1. 檢查 `REFACTORING_COMPLETE_REPORT.md` 了解重構詳情
2. 檢查 `REFACTORING_COMPARISON.txt` 查看修改對比
3. 檢查 `REFACTORING_PLAN.md` 了解重構計劃

---

## 🎓 給未來 AI 的建議

### 如果要修改 DELAY 邏輯

**新版本（V2）**：
- 只需修改 `transport/base_worker.py` 的 `_handle_delay_command()` 方法
- 三個 worker 自動同步

**舊版本**：
- 需要修改 3 個檔案：
  - `serial_worker.py`
  - `adb_worker.py`
  - `ssh_worker.py`

### 如果要新增 WAIT 指令

**新版本（V2）**：
- 在 `transport/base_worker.py` 新增 `_handle_wait_command()` 方法
- 在 `_handle_special_command()` 中呼叫
- 三個 worker 自動擁有新功能

**舊版本**：
- 需要在 3 個檔案中分別新增方法
- 需要在 3 個檔案的 `run()` 方法中呼叫

---

**建立日期**: 2026-02-11
**建立者**: Antigravity AI
**狀態**: 回退指南已建立
