# 視窗大小儲存問題 - 真正的根本原因

**日期**: 2026-02-12  
**問題**: `on_closing` 被覆蓋,視窗大小儲存邏輯未執行  
**狀態**: ✅ 已修復

---

## 🔍 真正的問題

### 多重綁定衝突

發現有**三個地方**綁定了 `WM_DELETE_WINDOW`:

1. **`main.py` 第 334 行**: `root.protocol("WM_DELETE_WINDOW", on_closing)`
   - ✅ 包含視窗大小儲存邏輯
   
2. **`ui_tab_manager.py` 第 98 行**: `self.root.protocol("WM_DELETE_WINDOW", self.on_closing)`
   - ❌ 沒有視窗大小儲存邏輯
   - ❌ 覆蓋了 `main.py` 的綁定
   
3. **`ui_main.py` 第 307 行**: `self.root.protocol("WM_DELETE_WINDOW", self.on_close)`
   - ❌ 沒有視窗大小儲存邏輯  
   - ❌ 覆蓋了 `main.py` 的綁定

### 執行順序

```
1. main.py 綁定 on_closing → 包含視窗大小儲存
2. ui_tab_manager.py 綁定 on_closing → 覆蓋了 main.py 的綁定!
3. ui_main.py 綁定 on_close → 再次覆蓋!
```

**結果**: `main.py` 的 `on_closing` 根本沒有執行,所以視窗大小沒有被儲存!

---

## ✅ 解決方案

### 註解掉重複的綁定

只保留 `main.py` 的綁定,註解掉其他兩個:

**`ui_tab_manager.py` 第 97-98 行**:
```python
# 設定視窗關閉事件
# ⚠️ 已移至 main.py 的 on_closing,確保視窗大小能正確儲存
# self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
```

**`ui_main.py` 第 306-307 行**:
```python
# 綁定關閉事件
# ⚠️ 已移至 main.py 的 on_closing,確保視窗大小能正確儲存
# self.root.protocol("WM_DELETE_WINDOW", self.on_close)
```

---

## 📋 修改的檔案

### `ui_parts/ui_tab_manager.py`
- 第 98 行: 註解掉 `WM_DELETE_WINDOW` 綁定

### `ui_parts/ui_main.py`
- 第 307 行: 註解掉 `WM_DELETE_WINDOW` 綁定

### `main.py`
- 第 334 行: 保留 `WM_DELETE_WINDOW` 綁定 (唯一的綁定)

---

## 🧪 測試步驟

1. **重新啟動程式**
2. **拖曳視窗到不同大小** (例如: 1200x900)
3. **關閉程式**
4. **查看終端機輸出**,應該看到:
   ```
   [DEBUG] 取得視窗大小: 1200x900
   [DEBUG] 已更新頂層視窗大小
   [DEBUG] 已更新 DUT_Control 視窗大小
   [DEBUG] save_setup 已呼叫
   [DEBUG] ✅ 視窗大小已儲存: 1200x900
   ```
5. **檢查 `setup.json`**:
   - 頂層 `Window_Width` 應該是 "1200"
   - 頂層 `Window_Height` 應該是 "900"
   - `DUT_Control.Window_Width` 應該是 "1200"
   - `DUT_Control.Window_Height` 應該是 "900"
6. **重新啟動程式**
7. **確認視窗大小是 1200x900** ✅

---

## 💡 關鍵洞察

**問題的根源**: 多個地方綁定了同一個事件,後面的綁定覆蓋了前面的綁定

**解決方案**: 只在一個地方綁定 `WM_DELETE_WINDOW`,確保邏輯不被覆蓋

**教訓**: 
- 在 Tkinter 中,`protocol()` 的綁定會被後續的綁定覆蓋
- 應該只在一個地方綁定關閉事件
- 如果需要多個關閉邏輯,應該在同一個函數中依序呼叫

---

## 🎯 為什麼之前沒發現?

1. **日誌中沒有除錯訊息**: 因為 `main.py` 的 `on_closing` 根本沒執行
2. **程式能正常關閉**: 因為 `ui_main.py` 的 `on_close` 有執行
3. **視窗大小沒儲存**: 因為 `ui_main.py` 的 `on_close` 沒有儲存視窗大小的邏輯

---

**建立日期**: 2026-02-12  
**建立者**: Antigravity AI  
**版本**: v4.0.0  
**狀態**: ✅ 已修復 (真正的根本原因)
