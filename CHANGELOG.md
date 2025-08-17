# JOVIAN指令工具 更新日誌

## 版本 1.10 (2025-08-16)

### 🆕 新功能
- **完整 ToolTip 系統**：為所有按鈕、下拉選單、輸入框等 UI 元件添加提示功能
- **設定頁面新增 ToolTip 開關**：可在設定頁面啟用/禁用按鈕提示功能
- **全新 tooltips.ini 配置**：支援自訂每個元件的提示文字

### 🔧 改進
- **重構 ToolTip 類別**：改善跨平台顯示相容性，特別針對 Windows 系統優化
- **事件綁定優化**：支援 `<Enter>`/`<Leave>`/`<Motion>`/`<ButtonPress>` 事件
- **延遲顯示控制**：預設 500ms 延遲，離開元件立即關閉
- **支援所有元件類型**：Button、Label、Entry、Combobox、Checkbutton、Frame 等

### 🐛 修復
- 修復 DOS 標籤頁 tooltip_manager 初始化問題
- 修復設定頁面 UI_ToolTip_Enabled 變數順序問題
- 改善 tooltip 系統的記憶體管理和事件處理
- 修正跨標籤頁切換時的 tooltip 功能

### 📝 技術細節
- 新增 `ui_parts/tooltip.py` 模組
- 完善所有標籤頁的 tooltip 綁定
- 支援從 `tooltips.ini` 動態載入提示文字
- 改進錯誤處理和調試輸出

---

## 版本 1.9 (之前版本)
ㄨ- 基礎功能和 UI 改進
