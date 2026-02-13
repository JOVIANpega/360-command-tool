# 🚀 EXE 打包優化指南

## 📋 優化背景
目前指令通專案在打包成 EXE 後，啟動速度與檔案體積有優化空間。
主要的效能瓶頸在於 PyInstaller 的 `--onefile` 模式以及過度打包未使用的模組。

## 💡 三大優化策略

### 1. 模式切換：`--onedir` vs `--onefile`
*   **Onefile (目前的預設)**：將所有檔案壓縮成一個 EXE。啟動時需先解壓到臨時目錄，這在 Windows 上耗時約 3~10 秒。
*   **Onedir (建議方案)**：將檔案放在一個資料夾中。啟動幾乎是**即時 (秒開)**，且執行效率最高。

### 2. 模組排除 (Exclude Modules)
目前的開發環境包含大型科學計算庫（如 `scipy`, `pandas`），這些在庫在指令通中並未被使用。
透過 `--exclude-module` 參數，我們可以將 EXE 體積大幅減少。
**預計可排除模組**：`scipy`, `pandas`, `selenium`, `matplotlib`, `numpy`, `PIL`

### 3. 去除壓縮 (Disable UPX)
UPX 壓縮雖然可以減少體積，但會增加啟動時的 CPU 負擔。在現代電腦上，通常建議不使用以獲得最快啟動感。

---

## 🛠️ 如何執行優化打包

我們已更新 `build_scripts/build_PEGA_final.bat`，現在支援以下選項：

### 模式 A：極速開發模式 (Onedir)
這是啟動最快的模式，適合生產線頻繁啟動的環境。
1. 執行 `build_scripts/build_PEGA_final.bat`
2. 當詢問模式時選擇 `1` (Onedir)

### 模式 B：輕量單檔案模式 (Onefile Optimized)
仍保持單個 EXE，但移除了多餘的庫。
1. 執行 `build_scripts/build_PEGA_final.bat`
2. 當詢問模式時選擇 `2` (Onefile)

---

## 📊 預期效果
| 指標 | 優化前 | 優化後 (Onedir) |
| :--- | :--- | :--- |
| **啟動時間** | ~8 秒 | **< 1 秒** |
| **檔案體積** | ~100MB+ | **~40MB** |
| **穩定性** | 較易被防毒誤報 | 較穩定 |

**建立日期**: 2026-02-12
**更新者**: Antigravity AI
