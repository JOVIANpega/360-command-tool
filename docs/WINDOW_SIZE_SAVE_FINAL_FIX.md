# 視窗大小儲存問題 - 最終修復

**日期**: 2026-02-12  
**問題**: 視窗已被銷毀,無法取得視窗大小  
**狀態**: ✅ 已修復

---

## 🔍 問題根源

### 錯誤訊息

```
ERROR:VALO360:儲存運行時狀態失敗: can't invoke "winfo" command: application has been destroyed
  File "main.py", line 277, in on_closing
    width = root.winfo_width()
```

### 執行順序問題

**修復前的執行順序**:
1. 呼叫 `app.on_close()` → **銷毀視窗** (`root.destroy()`)
2. 取得視窗大小 (`root.winfo_width()`) → ❌ **視窗已被銷毀,無法取得!**

**問題**: `app.on_close()` 中呼叫了 `self.root.destroy()`,導致視窗被銷毀,之後無法取得視窗大小!

---

## ✅ 解決方案

### 調整執行順序

**修復後的執行順序**:
1. **先取得視窗大小** (`root.winfo_width()`) → ✅ 視窗還存在
2. **儲存視窗大小到 JSON** → ✅ 成功儲存
3. 呼叫 `app.on_close()` → 銷毀視窗 (沒關係,已經取得視窗大小了)

---

## 📋 修改內容

### `main.py` 的 `on_closing()` 函數

**修改前**:
```python
def on_closing():
    # 1. 先呼叫 app.on_close() → 銷毀視窗
    app.on_close()
    
    # 2. 取得視窗大小 → ❌ 視窗已被銷毀!
    width = root.winfo_width()
```

**修改後**:
```python
def on_closing():
    # 1. 先取得並儲存視窗大小 (在視窗被銷毀之前!)
    width = root.winfo_width()
    height = root.winfo_height()
    current_settings["Window_Width"] = str(width)
    current_settings["Window_Height"] = str(height)
    current_settings["DUT_Control"]["Window_Width"] = str(width)
    current_settings["DUT_Control"]["Window_Height"] = str(height)
    save_setup(current_settings, manual_save=True)
    
    # 2. 然後呼叫 app.on_close() → 銷毀視窗
    app.on_close()
    return  # app.on_close() 已經銷毀視窗,直接返回
```

---

### 避免重複銷毀視窗

**問題**: `app.on_close()` 和 `finally` 中都呼叫了 `root.destroy()`,導致錯誤

**解決方案**:
1. `app.on_close()` 成功後直接 `return`,不執行 `finally`
2. `finally` 中使用 `try-except` 捕獲錯誤

```python
try:
    app.on_close()
    return  # 直接返回,不執行 finally
except Exception as e:
    log_info(f"app.on_close 失敗: {e}")
finally:
    try:
        root.destroy()  # 如果 app.on_close() 失敗,這裡再銷毀
    except:
        pass  # 視窗可能已經被銷毀了
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
   [INFO] 呼叫 app.on_close()...
   [INFO] app.on_close() 已完成
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

**問題的根源**: 執行順序錯誤,在視窗被銷毀後才嘗試取得視窗大小

**解決方案**: 在視窗被銷毀**之前**先取得並儲存視窗大小

**教訓**: 
- 在 Tkinter 中,`destroy()` 會立即銷毀視窗
- 銷毀後無法再呼叫 `winfo_width()` 等方法
- 必須在銷毀前取得所有需要的資訊

---

**建立日期**: 2026-02-12  
**建立者**: Antigravity AI  
**版本**: v3.0.0  
**狀態**: ✅ 已修復
