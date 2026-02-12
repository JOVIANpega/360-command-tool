# 視窗大小儲存問題 - 修復報告

**日期**: 2026-02-12  
**問題**: 調整視窗大小後重啟程式,視窗又變成預設值  
**狀態**: ✅ 已修復

---

## 🔍 問題分析

### 根本原因

`setup.json` 中有**兩個地方**儲存視窗大小:

```json
{
  "Window_Width": "1536",   ← 頂層
  "Window_Height": "793",
  
  "DUT_Control": {
    "Window_Width": "958",  ← DUT_Control 裡
    "Window_Height": "1048"
  }
}
```

**程式啟動時**: 讀取 `DUT_Control.Window_Width` 和 `DUT_Control.Window_Height`  
**程式關閉時**: 只更新頂層的 `Window_Width` 和 `Window_Height`

**結果**: 下次啟動時還是讀取舊的值!

---

## ✅ 修復方案

### 修改 `main.py` 的 `on_closing()` 函數

**位置**: 第 275-288 行

**修改內容**: 同時更新頂層和 DUT_Control 中的視窗大小

```python
# 只更新運行時的狀態 (視窗大小)
width = root.winfo_width()
height = root.winfo_height()

# 同時更新頂層和 DUT_Control 中的視窗大小
current_settings["Window_Width"] = str(width)
current_settings["Window_Height"] = str(height)

if "DUT_Control" not in current_settings:
    current_settings["DUT_Control"] = {}
current_settings["DUT_Control"]["Window_Width"] = str(width)
current_settings["DUT_Control"]["Window_Height"] = str(height)

log_info(f"準備儲存視窗大小: {width}x{height} (頂層 + DUT_Control)")
```

---

### 統一 `setup.json` 中的視窗大小

確保頂層和 DUT_Control 中的值一致:

```json
{
  "Window_Width": "1536",
  "Window_Height": "793",
  
  "DUT_Control": {
    "Window_Width": "1536",  ← 統一為相同值
    "Window_Height": "793"
  }
}
```

---

## 🧪 測試步驟

1. **重新啟動程式** ✅
2. **調整視窗大小** (例如: 拖曳視窗邊緣到 1200x900)
3. **關閉程式**
4. **檢查 `setup.json`**:
   - 頂層的 `Window_Width` 應該是 "1200"
   - 頂層的 `Window_Height` 應該是 "900"
   - `DUT_Control.Window_Width` 應該是 "1200"
   - `DUT_Control.Window_Height` 應該是 "900"
5. **重新啟動程式**
6. **確認視窗大小是 1200x900** ✅

---

## 📋 修改的檔案

### `main.py`
- 第 275-288 行: 同時更新頂層和 DUT_Control 中的視窗大小

### `setup.json`
- 第 4-5 行: 頂層視窗大小
- 第 27-28 行: DUT_Control 視窗大小
- 統一為 1536x793

---

## 💡 關鍵洞察

**問題的根源**: 程式啟動時讀取的位置和關閉時儲存的位置不一致

**解決方案**: 確保啟動和關閉時使用相同的位置

**最佳實踐**: 
- 只在一個地方儲存視窗大小 (避免重複)
- 或確保所有地方都同步更新

---

**建立日期**: 2026-02-12  
**建立者**: Antigravity AI  
**版本**: v1.0.0  
**狀態**: ✅ 已修復
