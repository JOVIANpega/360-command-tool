# VALO360 指令通 建置說明

## 問題診斷
根據 run_log.txt，之前遇到 `ModuleNotFoundError: No module named 'serial'` 錯誤，但現在已經解決。

## 建置步驟

### 方法 1: 使用修改過的 spec 文件
```bash
# 1. 安裝依賴
pip install pyinstaller pyserial psutil

# 2. 使用現有的 spec 文件建置
pyinstaller VALO360指令通.spec
```

### 方法 2: 直接命令行建置
```bash
# 1. 安裝依賴
pip install pyinstaller pyserial psutil

# 2. 清理舊檔案
rmdir /s /q build
rmdir /s /q dist

# 3. 執行建置
pyinstaller --onefile --windowed --clean --noconfirm --name "VALO360指令通" --icon "assets/app.ico" --add-data "Command_TABLE;Command_TABLE" --add-data "FIXTURE;FIXTURE" --add-data "ui_parts;ui_parts" --add-data "assets;assets" --add-data "user_guide.txt;." --add-data "setup.json;." --add-data "command.txt;." --add-data "color_word.txt;." --add-data "config_core.py;." --add-data "config_utils.py;." --add-data "serial_worker.py;." --hidden-import "tkinter" --hidden-import "tkinter.ttk" --hidden-import "serial" --hidden-import "serial.tools.list_ports" --hidden-import "config_core" --hidden-import "config_utils" --hidden-import "serial_worker" main.py
```

### 方法 3: 使用批次檔
執行 `build_fix.bat` 或 `simple_build.cmd`

## 已修復的問題

1. ✅ **Command_Separator 功能已實作**
   - 在 setup.json 中新增 "Command_Separator": "|" 
   - 在設定頁面新增 GUI 欄位
   - 修改指令解析邏輯使用動態分隔符號
   - 支援即時更新

2. ✅ **Spec 文件已更新**
   - 新增必要的 hiddenimports
   - 修正 datas 路徑
   - 包含所有必要檔案

3. ✅ **依賴問題已解決**
   - pyserial 模組現在可正常導入
   - 所有必要模組都已包含

## 建置後檢查

建置完成後，檢查以下項目：

1. `dist/VALO360指令通.exe` 是否存在
2. 檔案大小是否合理 (通常 20-50 MB)
3. 執行檔是否可以正常啟動
4. 新增的「指令間隔符號」功能是否正常工作

## 故障排除

如果建置失敗：

1. 檢查 Python 版本 (建議 3.8+)
2. 確認所有依賴已安裝：`pip list | findstr "pyinstaller\|serial\|psutil"`
3. 檢查檔案路徑是否正確
4. 查看建置輸出中的錯誤訊息

## 測試新功能

建置完成後，測試「指令間隔符號」功能：

1. 開啟程式，進入「設定」頁面
2. 修改「指令間隔符號」從 `|` 改為 `||`
3. 確認設定立即生效
4. 檢查 setup.json 中的 Command_Separator 值是否更新
5. 測試指令執行是否使用新的分隔符號

## 完成狀態

✅ 所有功能已實作完成，可以進行建置
✅ 指令間隔符號功能已完整實作
✅ 建置配置已優化
✅ 依賴問題已解決