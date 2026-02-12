# 常用設定快速參考

**用途**: 快速修改 `setup.json` 中的常用設定

---

## 📋 分隔條位置 (左右面板)

**位置**: `setup.json` → `DUT_Control` → `Pane_Sash_Position`

**常用值**:
- `"579"` - 預設值 (左側面板較窄)
- `"800"` - 中等寬度
- `"1000"` - 左側面板較寬
- `"1156"` - 你喜歡的寬度

**修改方法**:
```json
"DUT_Control": {
  "Pane_Sash_Position": "1156",  ← 改這裡
  ...
}
```

---

## 📋 字體大小

**位置**: `setup.json` → `DUT_Control`

**常用值**:
- UI 字體: `"10"` (小), `"12"` (中), `"13"` (大)
- 內容字體: `"10"` (小), `"12"` (中), `"13"` (大)

**修改方法**:
```json
"DUT_Control": {
  "UI_Font_Size": "13",        ← UI 字體大小
  "Content_Font_Size": "13",   ← 內容字體大小
  ...
}
```

---

## 📋 COM 口

**位置**: `setup.json` → `DUT_Control` → `Serial_COM_Port`

**常用值**:
- `"COM3"`, `"COM4"`, `"COM5"` 等

**修改方法**:
```json
"DUT_Control": {
  "Serial_COM_Port": "COM4",  ← 改這裡
  ...
}
```

---

## 📋 超時時間

**位置**: `setup.json` → `DUT_Control` → `Command_Timeout_Seconds`

**常用值**:
- `"15"` (快速), `"30"` (預設), `"60"` (較長)

**修改方法**:
```json
"DUT_Control": {
  "Command_Timeout_Seconds": "30",  ← 改這裡
  ...
}
```

---

## 📋 預設 IP 位址

**位置**: `setup.json` → `DUT_Control` → `Default_IP_Address`

**修改方法**:
```json
"DUT_Control": {
  "Default_IP_Address": "172.0.0.1",  ← 改這裡
  ...
}
```

---

## 📋 指令檔案路徑

**位置**: `setup.json` → `DUT_Control` → `Command_File_Path`

**修改方法**:
```json
"DUT_Control": {
  "Command_File_Path": "D:/((Python TOOL/指令工具-20250428T020034Z-001/360-command-tool/Command_TABLE/GEMINI.txt",  ← 改這裡
  ...
}
```

---

## 🚀 快速修改步驟

1. **關閉程式** (如果正在執行)
2. **用記事本或 VS Code 開啟 `setup.json`**
3. **找到 `DUT_Control` 區塊**
4. **修改你要的設定**
5. **儲存檔案**
6. **重新啟動程式** ✅

---

## ⚠️ 注意事項

1. **JSON 格式要正確**:
   - 字串要用雙引號 `""`
   - 數字不用引號 (但我們的設定都是字串,所以要用引號)
   - 最後一個項目後面不要有逗號
   - 布林值用 `true` 或 `false` (小寫,不用引號)

2. **修改前先備份**:
   - 複製一份 `setup.json` 到其他地方
   - 或者從 `backup` 資料夾恢復

3. **程式必須關閉**:
   - 修改 `setup.json` 時,程式必須關閉
   - 否則程式關閉時會覆蓋你的修改

---

## 📝 你的常用設定模板

**複製這段到 `setup.json` 的 `DUT_Control` 區塊**:

```json
"DUT_Control": {
  "Pane_Sash_Position": "1156",
  "UI_Font_Size": "13",
  "Content_Font_Size": "13",
  "Serial_COM_Port": "COM4",
  "Command_Timeout_Seconds": "30",
  "Default_IP_Address": "172.0.0.1",
  "Command_File_Path": "D:/((Python TOOL/指令工具-20250428T020034Z-001/360-command-tool/Command_TABLE/GEMINI.txt",
  "Command_End_String": "root",
  "Last_Selected_Command_Section": "Gemeni 1",
  "Window_Width": "1536",
  "Window_Height": "793",
  "Auto_Execute": false,
  "Available_End_Strings": ["root"],
  "Window_Title": "PEGA指令通",
  "Notification_Font_Size": "10",
  "Single_Command_Timeout": "15"
}
```

---

**建立日期**: 2026-02-12  
**建立者**: Antigravity AI  
**版本**: v1.0.0
