# PEGA 指令通 (PEGA Command Tool) v2.5.4

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

專為工程師設計的高效能指令執行工具，支援序列埠 (Serial/Console)、ADB 以及 SSH 傳輸模式。透過分類管理與自動化執行，大幅提升設備控制與測試效率。

## 🌟 核心功能

- **多模式傳輸**：支援 Console (RS232)、ADB、SSH 模式。
- **指令分類管理**：自定義指令清單，支援多層級分類（如：DUT 控制、治具控制）。
- **特殊指令支援**：
  - `DELAY:數字`：精確的倒數計時計時器（支援浮點數）。
  - `SHOW:文字`：自定義彈窗提醒，協助手動操作流程。
- **進度追蹤**：視覺化進度條，清晰掌握指令執行進度。
- **資源管理器**：智能路徑定位，確保在不同環境（開發 vs 打包）下均能正確讀取配置。
- **自定義介面**：動態調整字體大小 (8-20pt)，支援 ToolTip 提示與通知系統。

## 🏗️ 系統架構 (已重構 v2.5)

專案已完成核心架構重構，採用 **模板方法模式 (Template Method Pattern)**，大幅提升維護性：

- `transport/base_worker.py`: 核心行為基底類別（共用 DELAY, SHOW, 進度管理）。
- `transport/serial_worker_v2.py`: 序列埠專屬邏輯。
- `transport/adb_worker_v2.py`: ADB 專屬邏輯。
- `transport/ssh_worker_v2.py`: SSH 專屬邏輯。

## 🚀 快速開始

### 環境需求
- Windows OS
- Python 3.8+
- 依賴項：`tk`, `pyserial`, `psutil` (及其他於 `requirements.txt` 列出之項目)

### 安裝與執行
1. 克隆專案：
   ```bash
   git clone [repository-url]
   cd 360-command-tool
   ```
2. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   ```
3. 執行程式：
   ```bash
   python main.py
   ```

## 📦 打包發佈 (EXE)

本專案提供自動化編譯指令碼：
1. 開啟終端機。
2. 執行 `build_scripts\build_PEGA_final.bat`。
3. 產出之可執行檔將位於 `dist/` 目錄中。

## 📂 專案結構

```
360-command-tool/
├── main.py              # 進入點
├── setup.json           # 全域設定
├── Command_TABLE/       # 指令清單目錄
├── transport/           # 傳輸核心 (Serial, ADB, SSH)
├── ui_parts/            # UI 組件與處理邏輯
├── docs/                # 專案文件與使用手冊
└── build_scripts/       # 自動化打包指令碼
```

## 📝 授權說明
本專案為內部開發工具，未經授權禁止外傳。

---
**Last Updated**: 2026-02-12
**Version**: 2.5.6 (Stable Release)
