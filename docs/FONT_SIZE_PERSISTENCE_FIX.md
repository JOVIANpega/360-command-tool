# 字體大小重啟後重置問題 - 調查與修復報告

**日期**: 2026-02-11  
**問題**: 調整文字大小後,重啟程式又恢復為預設文字大小  
**修復狀態**: ✅ 已完成

---

## 📋 問題分析

### 1. 程式架構概覽

根據 `README.md` 和 `README_FOR_AI.md`,本專案已完成重構 (v2.5.4):

```
360-command-tool/
├── main.py              # 進入點
├── setup.json           # 全域設定 ⭐ 問題核心
├── config_core.py       # 配置管理核心
├── core/
│   ├── config_manager.py    # 統一配置管理器
│   └── ...
├── ui_parts/
│   ├── ui_handlers.py       # 事件處理器 ⭐ 修復位置
│   ├── ui_components.py     # UI 元件 (包含字體滑桿)
│   └── ...
└── transport/           # 傳輸核心 (已重構)
```

### 2. 根本原因

#### 問題: 字體大小調整後無法儲存

字體大小是在 **DUT 控制頁面** 透過滑桿調整的,當使用者拖動滑桿時:

1. 觸發 `ui_handlers.py` 的 `change_ui_font_size()` 和 `change_content_font_size()` 方法
2. 這兩個方法呼叫 `save_setup(self.parent.setup)` **沒有傳遞 `manual_save=True`**
3. 因為自動保存被禁用,設定根本沒有被儲存到檔案
4. 重啟後,程式從 `setup.json` 讀取的還是舊的預設值 12

#### 證據

查看 `ui_handlers.py` 的原始程式碼 (第 1187 行):

```python
def change_ui_font_size(self, size):
    # ... 更新 UI ...
    
    # 保存設置到DUT_Control和全域設定
    self.parent.setup['UIFontSize'] = str(size)
    self.parent.setup['DUT_Control']['UI_Font_Size'] = str(size)
    
    save_setup(self.parent.setup)  # ❌ 沒有 manual_save=True!
```

查看 `config_core.py` (第 132-138 行):

```python
def save_setup(setup_data: Dict[str, Any], manual_save=False) -> bool:
    """保存設定檔 - 使用新的配置管理器"""
    # 如果不是手動保存,則跳過(暫時禁用自動保存)
    if not manual_save:
        print("[DEBUG] 自動保存已禁用,請使用手動保存")
        return False  # ❌ 直接返回 False,設定未保存!
    return config_manager.save_config(setup_data)
```

**結論**: 因為沒有傳遞 `manual_save=True`,所有的字體大小調整都**沒有被儲存**!

---

## 🔧 修復方案

### 修改檔案: `ui_parts/ui_handlers.py`

#### 修改 1: `change_ui_font_size` 方法 (第 1178-1191 行)

**修改前**:
```python
# 保存設置到DUT_Control和全域設定
self.parent.setup['UIFontSize'] = str(size)
if 'DUT_Control' not in self.parent.setup:
    self.parent.setup['DUT_Control'] = {}
self.parent.setup['DUT_Control']['UI_Font_Size'] = str(size)

save_setup(self.parent.setup)  # ❌ 沒有 manual_save=True
```

**修改後**:
```python
# 保存設置到DUT_Control和全域設定
print(f"[DEBUG] 準備儲存UI字體大小: {size}")

self.parent.setup['UIFontSize'] = str(size)
if 'DUT_Control' not in self.parent.setup:
    self.parent.setup['DUT_Control'] = {}
self.parent.setup['DUT_Control']['UI_Font_Size'] = str(size)

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
# 保存設置到DUT_Control和全域設定
self.parent.setup['ContentFontSize'] = str(size)
if 'DUT_Control' not in self.parent.setup:
    self.parent.setup['DUT_Control'] = {}
self.parent.setup['DUT_Control']['Content_Font_Size'] = str(size)

save_setup(self.parent.setup)  # ❌ 沒有 manual_save=True
```

**修改後**:
```python
# 保存設置到DUT_Control和全域設定
print(f"[DEBUG] 準備儲存內容字體大小: {size}")

self.parent.setup['ContentFontSize'] = str(size)
if 'DUT_Control' not in self.parent.setup:
    self.parent.setup['DUT_Control'] = {}
self.parent.setup['DUT_Control']['Content_Font_Size'] = str(size)

# ⭐ 關鍵修復: 使用 manual_save=True 強制儲存
save_result = save_setup(self.parent.setup, manual_save=True)
if save_result:
    print(f"[SUCCESS] 內容字體大小已儲存: {size}")
else:
    print(f"[ERROR] 內容字體大小儲存失敗!")
```

### 關鍵改進

1. ✅ 使用 `manual_save=True` **強制儲存**
2. ✅ 添加**儲存前的調試輸出**,顯示準備儲存的字體大小
3. ✅ 添加**儲存後的驗證**,確認儲存是否成功
4. ✅ 同時修復 **UI 字體** 和 **內容字體** 的儲存邏輯

---

## ✅ 修復效果

### 修復前:
1. 在 DUT 控制頁面調整字體大小滑桿
2. UI 立即更新,字體大小改變
3. **設定未實際保存** (因為 `manual_save=False`)
4. 重啟程式 → 字體大小恢復預設值 12 ❌

### 修復後:
1. 在 DUT 控制頁面調整字體大小滑桿
2. UI 立即更新,字體大小改變
3. **設定強制保存** (使用 `manual_save=True`)
4. 終端機顯示儲存成功訊息
5. 重啟程式 → 字體大小保持設定值 ✅

---

## 🧪 測試步驟

1. **調整字體大小**:
   - 開啟程式
   - 進入「DUT 控制」標籤頁
   - 調整 UI 字體大小滑桿 (例如: 12 → 16)
   - 調整內容字體大小滑桿 (例如: 12 → 14)

2. **確認儲存成功**:
   - 查看終端機輸出,應該看到:
     ```
     [DEBUG] 準備儲存UI字體大小: 16
     [SUCCESS] UI字體大小已儲存: 16
     [DEBUG] 準備儲存內容字體大小: 14
     [SUCCESS] 內容字體大小已儲存: 14
     ```

3. **驗證 setup.json**:
   - 開啟 `setup.json` 檔案
   - 確認以下位置都已更新:
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

4. **重啟測試**:
   - 關閉程式
   - 重新啟動程式
   - 確認字體大小保持為 16 和 14 ✅

---

## 📝 相關檔案

- **修改檔案**: `ui_parts/ui_handlers.py`
- **相關檔案**:
  - `config_core.py` - 配置管理核心
  - `core/config_manager.py` - 統一配置管理器
  - `setup.json` - 設定檔案
  - `ui_parts/ui_components.py` - UI 元件 (字體滑桿)

---

## 🎯 總結

**問題根源**: 字體大小調整時呼叫 `save_setup()` 沒有傳遞 `manual_save=True`,導致自動保存被禁用,設定未實際寫入檔案

**解決方案**: 
1. 使用 `manual_save=True` 強制保存
2. 添加儲存前後的調試輸出
3. 添加儲存結果驗證

**修復狀態**: ✅ 已完成

---

**建立日期**: 2026-02-11  
**建立者**: Antigravity AI  
**版本**: v2.5.4
