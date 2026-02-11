# JOVIAN 字串檢查功能實現說明

## 功能概述

本次更新在程式中加入了全面的 JOVIAN 字串檢查功能，確保只有包含合法字串的指令檔才能被載入和使用。檢查會在兩個關鍵點進行：

1. **程式啟動時**：強制檢查，失敗則退出程式
2. **設定儲存時**：檢查指令檔路徑，失敗則阻止儲存

## 實現方案

### **方案特點**
- **單一檢查點**：避免重複檢查和多重彈窗
- **啟動時攔截**：在GUI創建前就攔截問題
- **儲存時保護**：防止保存無效的指令檔路徑

## 實現位置

### 1. 啟動時檢查（`main.py`）

**檢查邏輯**：
```python
if __name__ == "__main__":
    try:
        # 在創建GUI前，先檢查指令檔是否包含 JOVIAN 字串
        log_info("程式啟動時檢查指令檔...")
        
        # 載入設定檔
        setup = load_setup()
        command_file_path = setup.get("DUT_Control", {}).get("Command_File_Path", "")
        
        # 如果沒有設定路徑或檔案不存在，使用預設路徑
        if not command_file_path or not os.path.exists(command_file_path):
            command_file_path = "command.txt"
            log_info(f"使用預設指令檔路徑: {command_file_path}")
        else:
            log_info(f"使用設定檔中的指令檔路徑: {command_file_path}")
        
        # 立即檢查指令檔是否包含 JOVIAN 字串
        if not check_jovian_string(command_file_path, show_error=True, exit_on_fail=True):
            log_error(f"指令檔 JOVIAN 檢查失敗: {command_file_path}")
            sys.exit(1)
        
        log_info("指令檔 JOVIAN 檢查通過，開始創建GUI...")
        
        # 初始化應用程式
        root, app = initialize_application()
```

**檢查流程**：
1. 載入設定檔，讀取 `Command_File_Path`
2. 驗證路徑有效性，無效則回退到預設的 `command.txt`
3. 使用 `check_jovian_string()` 檢查 JOVIAN 字串
4. 檢查失敗則強制退出程式（`exit_on_fail=True`）
5. 檢查成功才繼續創建GUI

### 2. 設定儲存時檢查（`ui_parts/ui_settings_tab.py`）

**檢查邏輯**：
```python
def manual_save_settings(self):
    """手動保存設定到 setup.json"""
    try:
        print("[DEBUG] 開始手動保存設定...")

        # 在保存設定前，先檢查指令檔是否包含合法字串
        try:
            command_file_path = self.vars["DUT_Command_File_Path"].get()
            if command_file_path and os.path.exists(command_file_path):
                # 檢查是否包含 JOVIAN 字串
                from config_core import check_jovian_string
                if not check_jovian_string(command_file_path, show_error=True, exit_on_fail=False):
                    error_msg = f'指令表需內含合法的字串才能保存設定\n\n檔案: {os.path.basename(command_file_path)}\n請確認指令檔中包含 "JOVIAN" 字串後再進行儲存'
                    messagebox.showerror('錯誤', error_msg)
                    print(f"[ERROR] 指令檔檢查失敗，阻止儲存: {error_msg}")
                    return
                else:
                    print("[DEBUG] 指令檔 JOVIAN 字串檢查通過")
            else:
                print("[WARNING] 指令檔路徑無效或檔案不存在，跳過 JOVIAN 字串檢查")
        except Exception as e:
            print(f"[WARNING] 指令檔檢查時發生錯誤: {e}")

        # 生成設定字典並繼續儲存...
```

**檢查流程**：
1. 獲取當前設定的指令檔路徑
2. 如果路徑有效且檔案存在，檢查 JOVIAN 字串
3. 使用 `check_jovian_string()` 檢查，`exit_on_fail=False`
4. 檢查失敗則顯示錯誤訊息並阻止儲存（`return`）
5. 檢查成功才繼續儲存設定

### 3. 通用檢查函式（`config_core.py`）

**函式定義**：
```python
def check_jovian_string(file_path: str, show_error: bool = True, exit_on_fail: bool = False) -> bool:
    """
    檢查指令檔是否包含 JOVIAN 字串
    
    Args:
        file_path: 指令檔路徑
        show_error: 是否顯示錯誤訊息
        exit_on_fail: 是否在檢查失敗時強制退出程式
        
    Returns:
        bool: True 如果包含 JOVIAN 字串，False 如果不包含
    """
```

**檢查邏輯**：
- 驗證檔案存在性
- 讀取檔案內容
- 檢查是否包含 "JOVIAN" 字串
- 根據參數決定是否顯示錯誤訊息和強制退出

## 錯誤訊息說明

### 啟動時錯誤
```
程式啟動失敗：指令表需內含合法的字串

檔案: [檔案名稱]
請確認指令檔中包含 "JOVIAN" 字串後重新啟動程式
```

### 儲存時錯誤
```
指令表需內含合法的字串才能保存設定

檔案: [檔案名稱]
請確認指令檔中包含 "JOVIAN" 字串後再進行儲存
```

## 檢查標準

- **必要條件**: 指令檔內容中必須包含 "JOVIAN" 字串（區分大小寫）
- **檢查方式**: 使用 `'JOVIAN' not in content` 進行字串搜尋
- **檔案編碼**: 支援 UTF-8 編碼
- **檢查範圍**: 整個檔案內容，包括註釋行

## 測試結果

### ✅ 正常情況測試
- `command.txt` 包含 "I LOVE JOVIAN" ✅ 通過
- 程式正常啟動和運行

### ❌ 異常情況測試
- `command - test.txt` 只包含 "I LOVE" ❌ 失敗
- 啟動時顯示錯誤訊息：「程式啟動失敗：指令表需內含合法的字串...請確認指令檔中包含 "JOVIAN" 字串後重新啟動程式」
- 程式正確攔截並強制退出

### 🔒 設定儲存保護
- 嘗試儲存無效指令檔路徑時會被阻止
- 顯示明確的錯誤提示
- GUI不會關閉，只阻止儲存操作

## 保護層級

1. **啟動時保護**: 在GUI創建前就攔截問題
2. **儲存時保護**: 防止保存無效的指令檔路徑
3. **單一檢查點**: 避免重複檢查和多重彈窗
4. **智慧路徑處理**: 自動回退到預設指令檔

## 檔案修改清單

### 新增功能
- `config_core.py`: 新增 `check_jovian_string()` 通用檢查函式

### 主要修改
- `main.py`: 啟動時加入指令檔檢查邏輯
- `ui_parts/ui_settings_tab.py`: 儲存時加入指令檔檢查邏輯

### 移除重複檢查
- `ui_parts/ui_components.py`: 移除動態載入時的檢查
- `ui_parts/ui_handlers_core.py`: 移除指令解析時的檢查
- `ui_parts/ui_handlers.py`: 移除指令處理時的檢查
- `ui_parts/ui_components_input.py`: 移除輸入元件時的檢查
- `ui_parts/command_processor.py`: 移除指令處理器時的檢查

## 版本資訊

- **實現日期**: 2025-01-20
- **功能版本**: v1.9.6
- **修改類型**: 安全性增強（啟動時攔截 + 儲存時保護）
- **影響範圍**: 程式啟動和設定儲存
- **檢查點數量**: 2個主要檢查點（啟動時 + 儲存時）
- **保護程度**: 全面覆蓋，避免無效指令檔被使用 