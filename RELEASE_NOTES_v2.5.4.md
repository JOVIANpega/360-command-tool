# v2.5.4 - 修復儲存設定後分類按鈕消失的問題

## 🐛 Bug 修復

### 主要問題
點擊「儲存設定並即刻生效」按鈕後，指令分類按鈕會消失，導致無法選擇指令分類。

### 根本原因
1. **佈局管理器衝突**：`regenerate_section_buttons` 方法直接在 `section_frame` 上使用 `grid` 佈局，但 `section_frame` 已經有用 `pack` 管理的子元件（`selector_subframe` 和 `section_description`），導致 Tkinter 錯誤：
   ```
   TclError: cannot use geometry manager grid inside ... which already has slaves managed by pack
   ```

2. **重複 pack 調用**：在 `refresh_commands_fully` 中重複調用 `selector_subframe.pack()`，破壞了已經用 `grid` 佈局的按鈕。

3. **指令解析不統一**：`init_cmd_components` 中存在手動解析指令檔案的舊代碼，與 `CommandProcessor` 的解析邏輯不一致。

## ✅ 修復內容

### 1. 統一指令解析邏輯
**檔案**: `ui_parts/ui_components.py`
- 移除 `init_cmd_components` 中的手動檔案解析代碼
- 統一使用 `CommandProcessor.parse_commands_by_section()` 進行解析
- 支援多種標題格式：`[Section]`、`==Section==`、`===Section===`

### 2. 修復佈局管理器衝突
**檔案**: `ui_parts/ui_components.py`
- 重構 `regenerate_section_buttons` 方法，改為調用 `create_section_selector`
- 避免直接在 `section_frame` 上混用 `pack` 和 `grid`
- 所有按鈕都在 `selector_subframe` 內使用 `grid`，而 `selector_subframe` 本身用 `pack` 放在 `section_frame` 中

### 3. 移除重複的佈局調用
**檔案**: `ui_parts/ui_components.py`
- 在 `refresh_commands_fully` 中移除重複的 `selector_subframe.pack()` 調用
- 添加調試輸出以追蹤刷新流程

### 4. 增強 CommandProcessor
**檔案**: `ui_parts/command_processor.py`
- 改進區段標題解析邏輯，支援前後空白
- 支援至少 2 個等號的標題格式（`==Section==` 或更多）
- 自動去除標題前後的空白和等號

### 5. 添加刷新調用
**檔案**: `ui_parts/ui_main.py`
- 在 `update_all_settings` 中添加 `refresh_commands_fully` 調用
- 確保儲存設定後分類按鈕正確刷新

### 6. UI 改進：指令內容顯示位置調整
**檔案**: `ui_parts/ui_components.py`, `ui_parts/ui_components_input.py`
- 新增 `cmd_content_label` 標籤，放置在指令下拉選單下方
- 將指令內容顯示從分類按鈕區域移到指令選擇區域
- `section_description` 保留用於顯示分類說明

## 📝 修改的檔案

1. `ui_parts/ui_components.py`
   - `init_cmd_components()`: 統一使用 CommandProcessor
   - `create_section_selector()`: 添加調試輸出
   - `regenerate_section_buttons()`: 重構以避免佈局衝突
   - `refresh_commands_fully()`: 移除重複 pack 調用
   - `init_cmd_row()`: 添加指令內容顯示標籤
   - `on_cmd_selected()`: 更新指令內容顯示邏輯

2. `ui_parts/ui_components_input.py`
   - `update_cmd_list()`: 移除冗餘的檔案解析
   - 更新指令內容顯示邏輯

3. `ui_parts/command_processor.py`
   - `parse_commands_by_section()`: 增強標題解析

4. `ui_parts/ui_main.py`
   - `update_all_settings()`: 添加刷新指令分類按鈕的調用

5. `setup.json`
   - 更新版本號為 2.5.4

## 🧪 測試結果

- ✅ 點擊「儲存設定並即刻生效」後，分類按鈕正常顯示
- ✅ 支援 `[Section]` 和 `===Section===` 兩種標題格式
- ✅ 指令內容正確顯示在指令下拉選單下方
- ✅ 分類說明正確顯示在分類按鈕下方
- ✅ 無 TclError 錯誤
- ✅ UI 刷新流程正常

## 🔍 技術細節

### 佈局結構
```
left_panel (grid)
├── row=0: COM 端口選擇
├── row=1: 超時設定
├── row=2: section_frame (pack 內部)
│   ├── selector_subframe (pack, top)
│   │   └── 分類按鈕 (grid 內部)
│   └── section_description (pack, bottom)
├── row=3: cmd_frame (grid 內部)
│   ├── row=0: 指令下拉選單 + 執行按鈕
│   └── row=1: cmd_content_label (指令內容)
└── row=4: Ping 組件
```

### 關鍵修復
- **避免混用**: 同一容器內不混用 `pack` 和 `grid`
- **統一解析**: 所有指令解析都通過 `CommandProcessor`
- **正確刷新**: 儲存設定後正確調用刷新方法

## 📌 相關 Issue
修復用戶報告的「按下儲存按鈕後分類按鈕消失」問題。
