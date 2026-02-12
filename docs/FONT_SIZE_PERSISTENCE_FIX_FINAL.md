# 字體大小持久化問題 - 最終修復報告

**日期**: 2026-02-11  
**問題**: 調整文字大小後,重啟程式又恢復為預設文字大小  
**修復狀態**: ✅ 已完成 (第二次修復)

---

## 🚨 問題追蹤歷程

### 第一次修復 (不完整)

**修改檔案**: `ui_parts/ui_handlers.py`

修改了 `change_ui_font_size()` 和 `change_content_font_size()` 方法,添加了 `manual_save=True` 參數。

**結果**: ❌ 仍然失敗

**錯誤訊息**:
```
[DEBUG] 準備儲存UI字體大小: 12
DEBUG:VALO360:自動保存已禁用，跳過配置保存
[ERROR] UI字體大小儲存失敗!
```

### 第二次調查

發現問題的**真正根源**:

`config_core.py` 的 `save_setup()` 函數在呼叫 `config_manager.save_config()` 時,**沒有傳遞 `manual_save` 參數**!

**呼叫鏈**:
```
ui_handlers.py: change_ui_font_size()
  ↓ 呼叫 save_setup(self.parent.setup, manual_save=True)
  ↓
config_core.py: save_setup()
  ↓ 呼叫 config_manager.save_config(setup_data)  ❌ 沒有傳遞 manual_save!
  ↓
config_manager.py: save_config()
  ↓ 檢查 if not manual_save and not self._auto_save_enabled:
  ↓ 因為 manual_save=False (預設值),所以返回 False ❌
```

---

## 🔧 最終修復方案

### 修改檔案 1: `config_core.py` (第 132-139 行) ⭐ 關鍵修復

**修改前**:
```python
def save_setup(setup_data: Dict[str, Any], manual_save=False) -> bool:
    """保存設定檔 - 使用新的配置管理器"""
    # 如果不是手動保存,則跳過(暫時禁用自動保存)
    if not manual_save:
        print("[DEBUG] 自動保存已禁用,請使用手動保存")
        return False
    return config_manager.save_config(setup_data)  # ❌ 沒有傳遞 manual_save!
```

**修改後**:
```python
def save_setup(setup_data: Dict[str, Any], manual_save=False) -> bool:
    """保存設定檔 - 使用新的配置管理器"""
    # 如果不是手動保存,則跳過(暫時禁用自動保存)
    if not manual_save:
        print("[DEBUG] 自動保存已禁用,請使用手動保存")
        return False
    # ⭐ 關鍵修復: 將 manual_save 參數傳遞給 config_manager.save_config
    return config_manager.save_config(setup_data, manual_save=True)
```

### 修改檔案 2: `ui_parts/ui_handlers.py` (第一次修復)

#### 修改 1: `change_ui_font_size` 方法 (第 1178-1191 行)

**修改前**:
```python
save_setup(self.parent.setup)  # ❌ 沒有 manual_save=True
```

**修改後**:
```python
# ⭐ 關鍵修復: 使用 manual_save=True 強制儲存
save_result = save_setup(self.parent.setup, manual_save=True)
if save_result:
    print(f"[SUCCESS] UI字體大小已儲存: {size}")
else:
    print(f"[ERROR] UI字體大小儲存失敗!")
```

#### 修改 2: `change_content_font_size` 方法 (第 1244-1257 行)

**修改前**:
```python
save_setup(self.parent.setup)  # ❌ 沒有 manual_save=True
```

**修改後**:
```python
# ⭐ 關鍵修復: 使用 manual_save=True 強制儲存
save_result = save_setup(self.parent.setup, manual_save=True)
if save_result:
    print(f"[SUCCESS] 內容字體大小已儲存: {size}")
else:
    print(f"[ERROR] 內容字體大小儲存失敗!")
```

---

## ✅ 修復效果

### 修復後的呼叫鏈:
```
ui_handlers.py: change_ui_font_size()
  ↓ 呼叫 save_setup(self.parent.setup, manual_save=True) ✅
  ↓
config_core.py: save_setup(manual_save=True)
  ↓ 呼叫 config_manager.save_config(setup_data, manual_save=True) ✅
  ↓
config_manager.py: save_config(manual_save=True)
  ↓ 檢查 if not manual_save and not self._auto_save_enabled:
  ↓ 因為 manual_save=True,跳過檢查,繼續執行 ✅
  ↓ 成功儲存到 setup.json ✅
```

### 預期日誌輸出:
```
[DEBUG] 準備儲存UI字體大小: 16
[SUCCESS] UI字體大小已儲存: 16
```

**不再出現**: `DEBUG:VALO360:自動保存已禁用，跳過配置保存`

---

## 🧪 測試步驟

1. **重新啟動程式**
2. **進入「DUT 控制」標籤頁**
3. **調整 UI 字體大小滑桿** (例如: 12 → 16)
4. **查看終端機輸出**,應該看到:
   ```
   [DEBUG] 準備儲存UI字體大小: 16
   [SUCCESS] UI字體大小已儲存: 16
   ```
   **不應該看到**: `DEBUG:VALO360:自動保存已禁用，跳過配置保存`

5. **調整內容字體大小滑桿** (例如: 12 → 14)
6. **查看終端機輸出**,應該看到:
   ```
   [DEBUG] 準備儲存內容字體大小: 14
   [SUCCESS] 內容字體大小已儲存: 14
   ```

7. **驗證 setup.json**:
   - 開啟 `setup.json` 檔案
   - 確認字體大小已更新:
     ```json
     {
       "UIFontSize": "16",
       "ContentFontSize": "14",
       "DUT_Control": {
         "UI_Font_Size": "16",
         "Content_Font_Size": "14"
       }
     }
     ```

8. **重啟測試**:
   - 關閉程式
   - 重新啟動程式
   - **確認字體大小保持為 16 和 14** ✅

---

## 📝 修改檔案總結

1. **`config_core.py`** (第 132-139 行) ⭐ 最關鍵
   - 修復 `save_setup()` 沒有傳遞 `manual_save` 參數的問題

2. **`ui_parts/ui_handlers.py`** (第 1178-1191 行)
   - 修復 `change_ui_font_size()` 沒有使用 `manual_save=True` 的問題

3. **`ui_parts/ui_handlers.py`** (第 1244-1257 行)
   - 修復 `change_content_font_size()` 沒有使用 `manual_save=True` 的問題

---

## 🎯 根本原因總結

**問題**: 參數傳遞鏈斷裂

1. `ui_handlers.py` 呼叫 `save_setup(manual_save=True)` ✅
2. `config_core.py` 的 `save_setup()` 接收到 `manual_save=True` ✅
3. 但 `save_setup()` 呼叫 `config_manager.save_config()` 時,**沒有傳遞這個參數** ❌
4. `config_manager.save_config()` 使用預設值 `manual_save=False` ❌
5. 因為自動保存被禁用,所以返回 `False`,設定未儲存 ❌

**解決方案**: 確保 `manual_save` 參數在整個呼叫鏈中正確傳遞

---

**建立日期**: 2026-02-11  
**建立者**: Antigravity AI  
**版本**: v2.5.4  
**修復次數**: 2 次
