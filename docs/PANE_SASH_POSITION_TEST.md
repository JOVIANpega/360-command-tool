# 分隔條位置儲存測試

**日期**: 2026-02-12  
**問題**: 分隔條位置 (Pane_Sash_Position) 是否能正確儲存和恢復  
**狀態**: 🧪 待測試

---

## 📋 測試步驟

### 1. 確認當前狀態

**當前 `setup.json` 中的值**:
```json
"DUT_Control": {
  "Pane_Sash_Position": "908"
}
```

---

### 2. 測試分隔條位置恢復

1. **重新啟動程式**
2. **檢查分隔條位置**:
   - 左側面板和右側面板之間的分隔條位置
   - 應該在 908 像素的位置
3. **如果位置正確** ✅:
   - 分隔條位置恢復功能正常
4. **如果位置不正確** ❌:
   - 檢查啟動日誌,看看是否有 `[DEBUG] 已恢復分割位置: XXX`
   - 檢查恢復的值是否是 908

---

### 3. 測試分隔條位置儲存

1. **拖曳分隔條**到新的位置 (例如: 1000)
2. **等待 1 秒** (延遲儲存)
3. **檢查日誌**,應該看到:
   ```
   [DEBUG] 分割位置已變更: 1000
   [DEBUG] 分割位置已保存到設定檔: 1000
   ```
4. **關閉程式**
5. **檢查 `setup.json`**:
   ```json
   "DUT_Control": {
     "Pane_Sash_Position": "1000"
   }
   ```
6. **重新啟動程式**
7. **確認分隔條位置是 1000** ✅

---

## 🔍 可能的問題

### 問題 1: 啟動時分隔條位置被重置

**症狀**: 即使 `setup.json` 中是 908,啟動後分隔條位置還是預設值 (633)

**原因**: `restore_pane_position()` 沒有正確執行,或讀取了錯誤的值

**解決方案**: 檢查啟動日誌,確認是否有 `[DEBUG] 已恢復分割位置: 908`

---

### 問題 2: 關閉時分隔條位置被覆蓋

**症狀**: 拖曳分隔條到 1000,關閉後 `setup.json` 中還是 908

**原因**: `SerialUI.on_close` 中的 `get_settings_from_ui()` 沒有包含分隔條位置

**解決方案**: 檢查 `get_settings_from_ui()` 是否返回分隔條位置

---

## 💡 關鍵程式碼位置

### 啟動時恢復分隔條位置

**檔案**: `ui_components_base.py`  
**函數**: `restore_pane_position()`  
**行數**: 510-533

```python
def restore_pane_position(self):
    """恢復 PanedWindow 分割位置"""
    try:
        # 獲取保存的分割位置
        sash_position = self.parent.setup.get('DUT_Control', {}).get('Pane_Sash_Position', 633)
        
        # 設定分割位置
        if hasattr(self, 'main_frame') and self.main_frame:
            self.main_frame.sashpos(0, sash_position)
            print(f"[DEBUG] 已恢復分割位置: {sash_position}")
```

---

### 拖曳時儲存分隔條位置

**檔案**: `ui_components_base.py`  
**函數**: `_delayed_save_pane_position()`  
**行數**: 489-500

```python
def _delayed_save_pane_position(self, sash_position):
    """延遲保存分割位置"""
    try:
        from config_core import load_setup, save_setup
        full_setup = load_setup()
        if 'DUT_Control' not in full_setup:
            full_setup['DUT_Control'] = {}
        full_setup['DUT_Control']['Pane_Sash_Position'] = str(sash_position)
        save_setup(full_setup, manual_save=True)
        print(f"[DEBUG] 分割位置已保存到設定檔: {sash_position}")
```

---

### 關閉時儲存分隔條位置

**檔案**: `ui_main.py`  
**函數**: `SerialUI.on_close()`  
**行數**: 1722-1740

```python
# 保存 PanedWindow 分割位置
try:
    if hasattr(self.components, 'main_frame'):
        sash_position = self.components.main_frame.sashpos(0)
        if sash_position > 0:
            current_settings['Pane_Sash_Position'] = str(sash_position)
            print(f"[DEBUG] SerialUI.on_close: 保存分割位置: {sash_position}")
```

---

## 🧪 測試結果

**請在測試後填寫**:

- [ ] 啟動時分隔條位置正確恢復為 908
- [ ] 拖曳分隔條到 1000 後,日誌顯示已儲存
- [ ] 關閉程式後,`setup.json` 中是 "1000"
- [ ] 重新啟動程式,分隔條位置是 1000

---

**建立日期**: 2026-02-12  
**建立者**: Antigravity AI  
**版本**: v1.0.0  
**狀態**: 🧪 待測試
