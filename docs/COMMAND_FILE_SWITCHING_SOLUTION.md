# 換 TXT 檔案功能 - 解決方案

**日期**: 2026-02-11  
**問題**: 使用者換了 TXT 指令檔案後,需要點擊「儲存設定」才能生效,但該按鈕已被禁用

---

## 🎯 解決方案選項

### 選項 A: 建立獨立的「套用指令檔案」按鈕 (推薦)

在「設定我」頁面的「指令檔案路徑」旁邊,建立一個獨立的「套用」按鈕:

```python
def apply_command_file(self):
    """套用指令檔案變更"""
    try:
        # 1. 獲取新的檔案路徑
        new_path = self.command_file_path_var.get()
        
        # 2. 驗證檔案是否存在
        if not os.path.exists(new_path):
            messagebox.showerror("錯誤", f"檔案不存在: {new_path}")
            return
        
        # 3. 使用 ConfigService 儲存路徑
        from core.config_service import get_config_service
        config_service = get_config_service()
        config_service.update_dut_settings(Command_File_Path=new_path)
        
        # 4. 重新載入指令檔案
        from config_core import load_commands
        commands = load_commands(new_path)
        
        # 5. 通知 DUT 控制頁面更新指令列表
        # (需要找到 DUT UI 實例並呼叫更新方法)
        
        messagebox.showinfo("成功", f"指令檔案已套用:\n{new_path}")
        
    except Exception as e:
        messagebox.showerror("錯誤", f"套用指令檔案時發生錯誤: {e}")
```

**UI 布局**:
```
[指令檔案路徑] [___________________] [瀏覽...] [套用]
```

---

### 選項 B: 自動儲存並重新載入 (最簡單)

當使用者選擇新的 TXT 檔案後,**立即儲存並重新載入**,不需要額外按鈕:

```python
def browse_command_file(self):
    """瀏覽並選擇指令檔案"""
    from tkinter import filedialog
    
    filename = filedialog.askopenfilename(
        title="選取指令檔案",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    
    if filename:
        # 更新 UI 顯示
        self.command_file_path_var.set(filename)
        
        # ⭐ 立即儲存並套用
        try:
            # 1. 使用 ConfigService 儲存
            from core.config_service import get_config_service
            config_service = get_config_service()
            config_service.update_dut_settings(Command_File_Path=filename)
            
            # 2. 重新載入指令
            from config_core import load_commands
            commands = load_commands(filename)
            
            # 3. 通知 DUT 控制頁面更新
            # ...
            
            messagebox.showinfo("成功", f"指令檔案已套用:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"套用指令檔案時發生錯誤: {e}")
```

---

### 選項 C: 在 DUT 控制頁面提供「重新載入指令」按鈕

在 DUT 控制頁面建立一個「🔄 重新載入指令」按鈕:

```python
def reload_commands(self):
    """重新載入指令檔案"""
    try:
        # 1. 從配置讀取檔案路徑
        from core.config_service import get_config_service
        config_service = get_config_service()
        file_path = config_service.get_setting('DUT_Control.Command_File_Path')
        
        # 2. 重新載入指令
        from config_core import load_commands
        commands = load_commands(file_path)
        
        # 3. 更新 UI
        self.update_command_list(commands)
        
        messagebox.showinfo("成功", "指令檔案已重新載入")
        
    except Exception as e:
        messagebox.showerror("錯誤", f"重新載入指令時發生錯誤: {e}")
```

---

## 💡 我的建議

**選項 B (自動儲存並重新載入)** 是最好的選擇:

### 優點
✅ 使用者體驗最好 - 選擇檔案後立即生效  
✅ 不需要額外的按鈕  
✅ 符合「即時生效」的設計理念  
✅ 實現簡單

### 缺點
❌ 無法「預覽」檔案路徑再決定是否套用  
❌ 如果檔案有問題,會立即影響程式

---

## 🔧 實施步驟

### 步驟 1: 找到「瀏覽」按鈕的程式碼

搜尋 `browse` 或 `filedialog` 相關的程式碼

### 步驟 2: 修改 `browse_file` 方法

在選擇檔案後,立即呼叫 `ConfigService.update_dut_settings()` 儲存路徑

### 步驟 3: 重新載入指令

呼叫 `load_commands()` 重新載入指令檔案

### 步驟 4: 更新 DUT 控制頁面

通知 DUT 控制頁面更新指令列表

---

## ❓ 你希望使用哪個選項?

**選項 A**: 建立獨立的「套用」按鈕  
**選項 B**: 自動儲存並重新載入 (推薦)  
**選項 C**: 在 DUT 控制頁面提供「重新載入」按鈕  

請告訴我你的選擇,我會立即實施! 🚀
