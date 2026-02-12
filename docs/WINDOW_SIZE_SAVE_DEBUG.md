# 視窗大小儲存問題 - 除錯版本

**日期**: 2026-02-12  
**問題**: 視窗大小沒有被儲存到 setup.json  
**狀態**: 🔧 已添加除錯訊息

---

## 🔍 問題分析

### 測試結果

1. **拖曳視窗** ✅
2. **關閉程式** ✅
3. **檢查 setup.json** ❌ - 視窗大小仍然是 "1536" 和 "793"

**結論**: `on_closing()` 函數沒有正確執行或有錯誤發生

---

## 🐛 可能的原因

### 原因 1: `'app' in locals()` 檢查失敗 ✅ 已修復

**問題**: `app` 在 `on_closing()` 函數外部定義,不在 `locals()` 中

**修復**: 移除 `'app' in locals()` 檢查,直接使用 `app`

```python
# 修復前
if 'app' in locals() and hasattr(app, 'on_close'):
    app.on_close()

# 修復後
if hasattr(app, 'on_close'):
    app.on_close()
```

---

### 原因 2: 需要更多除錯訊息 ✅ 已添加

**添加的除錯訊息**:

```python
print(f"[DEBUG] 取得視窗大小: {width}x{height}")
print(f"[DEBUG] 已更新頂層視窗大小")
print(f"[DEBUG] 已更新 DUT_Control 視窗大小")
print(f"[DEBUG] save_setup 已呼叫")
print(f"[DEBUG] ✅ 視窗大小已儲存: {width}x{height}")
```

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
5. **檢查 `setup.json`**,確認視窗大小已更新

---

## 📋 修改的檔案

### `main.py`

**第 262 行**: 移除 `'app' in locals()` 檢查
```python
# 修復前
if 'app' in locals() and hasattr(app, 'on_close'):

# 修復後
if hasattr(app, 'on_close'):
```

**第 293 行**: 移除 `'app' in locals()` 檢查
```python
# 修復前
if 'app' in locals() and hasattr(app, 'current_font_size'):

# 修復後
if hasattr(app, 'current_font_size'):
```

**第 276-310 行**: 添加除錯訊息
- 取得視窗大小
- 更新頂層視窗大小
- 更新 DUT_Control 視窗大小
- save_setup 已呼叫
- 視窗大小已儲存

---

## 🎯 下一步

1. **重新啟動程式並測試**
2. **查看終端機輸出**,確認除錯訊息
3. **如果看到除錯訊息**:
   - ✅ `on_closing()` 函數正常執行
   - 檢查 `save_setup()` 是否真的儲存了
4. **如果沒看到除錯訊息**:
   - ❌ `on_closing()` 函數沒有被呼叫
   - 檢查 `WM_DELETE_WINDOW` 事件綁定

---

**建立日期**: 2026-02-12  
**建立者**: Antigravity AI  
**版本**: v2.0.0  
**狀態**: 🔧 等待測試
