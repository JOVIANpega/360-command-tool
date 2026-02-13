# DUT控制標籤頁分割線位置無法記住問題 - 修復報告

## 問題描述
用戶反饋：DUT控制標籤頁的分割線位置無法正確保存，重啟後又恢復到預設值。

## 根本原因分析

### 對比：設定標籤頁 vs DUT控制標籤頁

**設定標籤頁（工作正常）**：
```python
# ui_parts/ui_settings_tab.py 第72-80行
self._last_known_sash_pos = None  # ✅ 有即時記錄變數

def on_sash_pos_changed_local(e):
    try:
        pos = self.main_container.sashpos(0)
        if pos > 100:
            self._last_known_sash_pos = pos  # ✅ 即時記錄
            print(f"[DEBUG] 記錄設定頁面分欄位置: {pos}")
    except: pass
```

**DUT控制標籤頁（修復前）**：
```python
# ui_parts/ui_components_base.py
# ❌ 沒有即時記錄變數
# ❌ 只在延遲保存時才記錄位置
# ❌ 如果程式在延遲保存（1秒後）之前關閉，位置就丟失了
```

### 問題流程
1. 用戶拖動DUT控制頁面的分割線
2. 觸發 `on_pane_position_changed` 事件
3. 設置1秒後延遲保存（`after(1000, ...)`）
4. **用戶在1秒內關閉程式** ⚠️
5. 延遲保存未執行，新位置丟失
6. 程式關閉時從 `main_frame.sashpos(0)` 讀取位置
7. 此時可能讀到舊值或預設值
8. 保存了錯誤的位置到 setup.json

## 修復方案

### 1. 添加即時記錄變數（ui_components_base.py）

```python
# 第111-117行
# [修復] 即時記錄分割線位置，確保程式關閉時能保存最後的位置
self._last_known_sash_pos = None
```

### 2. 在分割線變更時立即記錄（ui_components_base.py）

```python
# 第361-381行
def on_pane_position_changed(self, event):
    """當 PanedWindow 分割位置變更時的處理"""
    try:
        if hasattr(self, 'main_frame') and self.main_frame:
            # 獲取新的分割位置
            sash_position = self.main_frame.sashpos(0)
            
            # [修復] 立即記錄位置，確保程式關閉時能保存
            if sash_position > 100:
                self._last_known_sash_pos = sash_position
                print(f"[DEBUG] 即時記錄DUT分割位置: {sash_position}")
            
            # 延遲保存，避免頻繁寫入（保持原有邏輯）
            if hasattr(self, '_pane_timer'):
                self.parent.root.after_cancel(self._pane_timer)
            self._pane_timer = self.parent.root.after(1000, lambda: self._delayed_save_pane_position(sash_position))
```

### 3. 程式關閉時優先使用即時記錄值（ui_main.py）

```python
# 第1719-1749行
# 保存 PanedWindow 分割位置
try:
    if hasattr(self.components, 'main_frame'):
        # [修復] 優先使用即時記錄的位置，確保保存用戶最後調整的值
        sash_position = None
        
        # 優先使用即時記錄的位置
        if hasattr(self.components, '_last_known_sash_pos') and self.components._last_known_sash_pos:
            sash_position = self.components._last_known_sash_pos
            print(f"[DEBUG] SerialUI.on_close: 使用即時記錄的分割位置: {sash_position}")
        else:
            # 如果沒有記錄，才使用即時讀取的值
            sash_position = self.components.main_frame.sashpos(0)
            print(f"[DEBUG] SerialUI.on_close: 使用即時讀取的分割位置: {sash_position}")

        if sash_position and sash_position > 100:  # 確保分割位置有效
            current_settings['Pane_Sash_Position'] = str(sash_position)
            print(f"[DEBUG] SerialUI.on_close: 保存分割位置: {sash_position}")
```

## 修復效果

### 修復前
- ❌ 拖動分割線後立即關閉程式 → 位置丟失
- ❌ 重啟後恢復到預設值或舊值
- ❌ 需要等待1秒後才能關閉程式以確保保存

### 修復後
- ✅ 拖動分割線後立即記錄到記憶體
- ✅ 無論何時關閉程式，都能保存最後的位置
- ✅ 重啟後正確恢復用戶調整的位置
- ✅ 與設定標籤頁的行為一致

## 測試步驟

1. **啟動程式**
   - 觀察 DUT 控制頁面的分割線位置

2. **調整分割線**
   - 拖動 DUT 控制頁面的分割線到新位置
   - 觀察控制台輸出：`[DEBUG] 即時記錄DUT分割位置: XXX`

3. **立即關閉程式**（不等待1秒）
   - 觀察控制台輸出：`[DEBUG] SerialUI.on_close: 使用即時記錄的分割位置: XXX`
   - 觀察控制台輸出：`[DEBUG] SerialUI.on_close: 保存分割位置: XXX`

4. **重新啟動程式**
   - 檢查 DUT 控制頁面的分割線位置是否恢復到步驟2調整的位置
   - 觀察控制台輸出：`[DEBUG] 已恢復分割位置: XXX`

5. **驗證 setup.json**
   - 打開 `setup.json` 文件
   - 檢查 `DUT_Control.Pane_Sash_Position` 的值是否正確

## 預期日誌輸出

```
# 拖動分割線時
[DEBUG] 即時記錄DUT分割位置: 850
[DEBUG] 分割位置已變更: 850

# 關閉程式時
[DEBUG] SerialUI.on_close: 程式關閉，正在保存設定...
[DEBUG] SerialUI.on_close: 使用即時記錄的分割位置: 850
[DEBUG] SerialUI.on_close: 保存分割位置: 850
[DEBUG] 配置保存成功

# 重新啟動時
[DEBUG] 已恢復分割位置: 850
```

## 技術細節

### 為什麼需要即時記錄？

1. **延遲保存的時間窗口問題**
   - 延遲保存設置為1秒（`after(1000, ...)`）
   - 用戶可能在1秒內關閉程式
   - 導致延遲保存未執行

2. **Tkinter 的事件循環特性**
   - `after()` 是異步執行的
   - 程式關閉時會取消所有待執行的 `after()` 回調
   - 即時記錄確保數據不丟失

3. **一致性原則**
   - 設定標籤頁已經使用這種模式並工作正常
   - 統一所有分割線的保存機制

## 相關文件

- `ui_parts/ui_components_base.py` - DUT控制頁面UI組件
- `ui_parts/ui_main.py` - 主程式和關閉邏輯
- `ui_parts/ui_settings_tab.py` - 設定標籤頁（參考實現）
- `setup.json` - 配置文件

## 修復日期
2026-02-13

## 修復人員
Antigravity AI Assistant
