# 配置管理 - 最終解決方案

**日期**: 2026-02-12  
**方案**: 單一 JSON + 智能儲存  
**狀態**: ✅ 已實施

---

## 🎯 核心原則

**從 JSON 讀取 → 只更新需要的欄位 → 寫回 JSON**

- ✅ 安全: 不會產生空字串
- ✅ 可靠: 只更新特定欄位
- ✅ 簡單: 不需要兩個 JSON

---

## ✅ 已實施的功能

### 1. 程式關閉時只儲存運行時狀態 ✅

**位置**: `main.py` 第 256-305 行

**功能**:
- 從 `setup.json` 讀取完整設定
- 只更新視窗大小和字體大小
- 寫回 `setup.json`
- **不覆蓋其他設定**

**程式碼**:
```python
def on_closing():
    # 1. 從 JSON 讀取完整設定
    current_settings = load_setup()
    
    # 2. 只更新運行時的狀態
    current_settings["Window_Width"] = str(width)
    current_settings["Window_Height"] = str(height)
    current_settings["DUT_Control"]["UI_Font_Size"] = str(font_size)
    
    # 3. 寫回 JSON
    save_setup(current_settings, manual_save=True)
```

---

### 2. 獨立更新按鈕 ✅

**位置**: `ui_parts/ui_settings_tab.py`

**已完成的按鈕**:
1. **版本號** (第 303-317 行) - `[2.5.4] [更新版本號]`
2. **設備標籤** (第 351-367 行) - `[XXXXX] [更新]`
3. **啟動名稱** (第 374-390 行) - `[ GEMINI TOOL] [更新]`

**更新方法** (第 1251-1449 行):
- `update_version_only()`
- `update_device_label_only()`
- `update_startup_label_only()`
- `update_tab_name_only(tab_index)`
- `update_hint_text_only()`

**所有方法都使用 `manual_save=True`** ✅

---

## 📋 待實施的功能

### 步驟 2: SSH 獨立按鈕 (10 分鐘)

在 SSH 設定區域添加「更新」按鈕:

```
SSH 主機: [192.168.11.143] [更新]
SSH 埠號: [22] [更新]
SSH 帳號: [root/oelinux123] [更新]
```

---

### 步驟 3: 「儲存所有設定」按鈕 (15 分鐘)

在「設定我」頁面底部添加:

```
[💾 儲存所有設定]
```

**功能**:
- 從 JSON 讀取完整設定
- 只更新非空值
- 寫回 JSON

---

## 🧪 測試結果

### ✅ 版本號更新測試

1. 修改版本號: `2.5.4` → `2.5.49`
2. 點擊「更新版本號」
3. 重啟程式
4. **版本號保持為 `2.5.49`** ✅

### ✅ 設備標籤更新測試

1. 修改設備標籤: `XXXXX` → `XXXXX99`
2. 點擊「更新」
3. 重啟程式
4. **設備標籤保持為 `XXXXX99`** ✅

### ✅ 啟動名稱更新測試

1. 修改啟動名稱: ` GEMINI TOOL` → `GEMINI TOOL99`
2. 點擊「更新」
3. 重啟程式
4. **啟動名稱保持為 `GEMINI TOOL99`** ✅

---

## 📊 修改的檔案

### `main.py`
- 第 256-305 行: 改進 `on_closing()` 函數

### `ui_parts/ui_settings_tab.py`
- 第 303-390 行: 添加獨立更新按鈕 (版本號、設備標籤、啟動名稱)
- 第 1251-1449 行: 添加 5 個獨立更新方法
- 所有方法都使用 `save_setup(current_settings, manual_save=True)`

---

## 🎯 核心優勢

### vs 兩個 JSON

| 比較項目 | 兩個 JSON | 單一 JSON + 智能儲存 |
|---------|----------|---------------------|
| **複雜度** | 高 | 低 |
| **同步問題** | 有 | 無 |
| **使用者困惑** | 高 | 低 |
| **安全性** | 高 | 高 |
| **推薦度** | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 💡 關鍵洞察

**問題的根源不是「多個地方讀寫 JSON」,而是「寫入時沒有從 JSON 讀取完整資料」**

**解決方案**: 所有寫入都使用「從 JSON 讀取 → 只更新需要的欄位 → 寫回」的模式

---

**建立日期**: 2026-02-12  
**建立者**: Antigravity AI  
**版本**: v2.0.0  
**狀態**: ✅ 步驟 1 完成,步驟 2-3 待實施
