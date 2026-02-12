# 配置管理重構方案 - 統一讀寫接口

**日期**: 2026-02-11  
**問題**: 多處寫入 setup.json 導致配置混亂和衝突  
**目標**: 建立統一的配置管理接口,所有配置讀寫都通過單一入口

---

## 🚨 當前問題

### 問題 1: 多處寫入配置
目前至少有以下地方在寫入 `setup.json`:

1. **`ui_handlers.py`** - 字體大小調整時
2. **`ui_components_settings.py`** - 「設定我」頁面的「儲存設定」按鈕
3. **`ui_settings_tab.py`** - 「設定我」頁面的手動儲存
4. **`ui_main.py`** - 程式關閉時 (`on_close` 方法)
5. **`config_core.py`** - 各種配置更新
6. **`core/config_manager.py`** - 底層配置管理

### 問題 2: 不一致的儲存邏輯
- 有些地方使用 `save_setup(manual_save=True)`
- 有些地方直接修改 `current_setup` 然後儲存
- 有些地方只儲存部分欄位,導致其他欄位被清空

### 問題 3: 缺乏驗證和預設值
- 空字串 `""` 被寫入配置,導致程式啟動失敗
- 缺乏欄位驗證和預設值保護

---

## ✅ 解決方案: 統一配置管理器

### 設計原則

1. **單一入口**: 所有配置讀寫都通過 `ConfigManager`
2. **欄位驗證**: 寫入前驗證欄位值,提供預設值
3. **部分更新**: 支援只更新特定欄位,不影響其他配置
4. **原子操作**: 配置更新要麼全部成功,要麼全部失敗
5. **事件通知**: 配置更新後通知相關組件

### 架構設計

```
┌─────────────────────────────────────────────────┐
│              UI Components                      │
│  (ui_handlers, ui_settings_tab, etc.)          │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│         ConfigService (新增)                    │
│  - update_font_size(ui_size, content_size)     │
│  - update_window_title(title)                  │
│  - update_dut_settings(settings_dict)          │
│  - update_fixture_settings(settings_dict)      │
│  - get_setting(key_path)                       │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│         ConfigManager (現有,需強化)             │
│  - load_config()                               │
│  - save_config()                               │
│  - validate_config()  ← 新增                   │
│  - merge_config()     ← 新增                   │
└─────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│              setup.json                         │
└─────────────────────────────────────────────────┘
```

---

## 📝 實施計劃

### 階段 1: 建立 ConfigService (高優先級)

建立 `core/config_service.py`,提供高層次的配置操作接口:

```python
class ConfigService:
    """統一配置服務 - 所有配置操作的單一入口"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self._callbacks = []  # 配置更新回調
    
    def update_font_size(self, ui_size=None, content_size=None, fixture_size=None):
        """更新字體大小 - 統一入口"""
        config = self.config_manager.load_config()
        
        if ui_size:
            ui_size = str(ui_size) if ui_size else '12'
            config['UIFontSize'] = ui_size
            config['DUT_Control']['UI_Font_Size'] = ui_size
        
        if content_size:
            content_size = str(content_size) if content_size else '12'
            config['ContentFontSize'] = content_size
            config['DUT_Control']['Content_Font_Size'] = content_size
        
        if fixture_size:
            fixture_size = str(fixture_size) if fixture_size else '11'
            config['Fixture_Control']['Fixture_Font_Size'] = fixture_size
        
        return self.config_manager.save_config(config, manual_save=True)
    
    def update_window_settings(self, title=None, width=None, height=None):
        """更新視窗設定"""
        config = self.config_manager.load_config()
        
        if title:
            config['Window_Title'] = title
            config['DUT_Control']['Window_Title'] = title
        
        if width and height:
            config['Window_Width'] = str(width)
            config['Window_Height'] = str(height)
            config['DUT_Control']['Window_Width'] = str(width)
            config['DUT_Control']['Window_Height'] = str(height)
        
        return self.config_manager.save_config(config, manual_save=True)
    
    def update_dut_settings(self, **kwargs):
        """更新 DUT 控制設定"""
        config = self.config_manager.load_config()
        
        for key, value in kwargs.items():
            if value is not None and value != '':
                config['DUT_Control'][key] = value
        
        return self.config_manager.save_config(config, manual_save=True)
    
    def get_setting(self, key_path, default=None):
        """獲取配置值 (支援路徑如 'DUT_Control.UI_Font_Size')"""
        config = self.config_manager.load_config()
        keys = key_path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        
        return value if value is not None and value != '' else default
```

### 階段 2: 強化 ConfigManager 驗證 (中優先級)

在 `core/config_manager.py` 中添加驗證邏輯:

```python
def _validate_and_fix_config(self, config):
    """驗證並修復配置 - 確保所有必要欄位都有有效值"""
    
    # 驗證字體大小
    if not config.get('UIFontSize') or config['UIFontSize'] == '':
        config['UIFontSize'] = '12'
    
    if not config.get('ContentFontSize') or config['ContentFontSize'] == '':
        config['ContentFontSize'] = '12'
    
    # 驗證 DUT_Control
    if 'DUT_Control' in config:
        dut = config['DUT_Control']
        if not dut.get('UI_Font_Size') or dut['UI_Font_Size'] == '':
            dut['UI_Font_Size'] = config.get('UIFontSize', '12')
        
        if not dut.get('Content_Font_Size') or dut['Content_Font_Size'] == '':
            dut['Content_Font_Size'] = config.get('ContentFontSize', '12')
        
        if not dut.get('Command_End_String') or dut['Command_End_String'] == '':
            dut['Command_End_String'] = 'root'
        
        if not dut.get('Command_Timeout_Seconds') or dut['Command_Timeout_Seconds'] == '':
            dut['Command_Timeout_Seconds'] = '30'
    
    # 驗證其他必要欄位...
    
    return config
```

### 階段 3: 重構現有程式碼 (低優先級)

逐步將現有的配置寫入邏輯遷移到 `ConfigService`:

**修改前** (`ui_handlers.py`):
```python
def change_ui_font_size(self, size):
    # ...
    self.parent.setup['UIFontSize'] = str(size)
    self.parent.setup['DUT_Control']['UI_Font_Size'] = str(size)
    save_setup(self.parent.setup, manual_save=True)
```

**修改後**:
```python
def change_ui_font_size(self, size):
    # ...
    from core.config_service import get_config_service
    config_service = get_config_service()
    config_service.update_font_size(ui_size=size)
```

---

## 🎯 立即行動: 臨時解決方案

在完整重構之前,**立即禁用有問題的儲存邏輯**:

### 方案 1: 禁用「設定我」頁面的儲存按鈕

在 `ui_components_settings.py` 中:

```python
def save_settings(self):
    """儲存設定到 setup.json - 暫時禁用"""
    messagebox.showwarning(
        "功能暫時禁用",
        "此功能正在重構中,請使用以下方式調整設定:\n\n"
        "• 字體大小: 在 DUT 控制頁面使用滑桿調整\n"
        "• 其他設定: 程式關閉時會自動儲存\n\n"
        "造成不便,敬請見諒!"
    )
    return
```

### 方案 2: 只允許字體大小在 DUT 控制頁面調整

保留 `ui_handlers.py` 的字體大小儲存邏輯,禁用其他所有地方的配置寫入。

---

## 📊 優先級建議

1. **立即** (今天):
   - ✅ 恢復 `setup.json` 到正確狀態
   - ✅ 禁用「設定我」頁面的儲存按鈕 (臨時方案)
   - ✅ 確保程式可以正常啟動和使用

2. **短期** (本週):
   - 🔨 建立 `ConfigService` 統一接口
   - 🔨 在 `ConfigManager` 中添加驗證邏輯
   - 🔨 遷移字體大小調整邏輯到 `ConfigService`

3. **中期** (下週):
   - 📝 逐步遷移其他配置操作到 `ConfigService`
   - 📝 建立配置更新事件系統
   - 📝 完善錯誤處理和日誌記錄

4. **長期** (未來):
   - 🎯 建立配置版本管理
   - 🎯 支援配置遷移和升級
   - 🎯 建立配置備份和恢復機制

---

## 🤔 你的選擇

請選擇接下來的行動:

**選項 A**: 立即實施臨時方案 (禁用「設定我」儲存按鈕)
- 優點: 快速,避免進一步破壞配置
- 缺點: 使用者無法在「設定我」頁面儲存設定

**選項 B**: 立即開始建立 ConfigService
- 優點: 從根本解決問題
- 缺點: 需要更多時間,可能影響其他功能

**選項 C**: 混合方案 (先 A 再 B)
- 優點: 兼顧穩定性和長期解決方案
- 缺點: 需要分階段實施

---

**建議**: 選擇 **選項 C (混合方案)**

1. 現在立即禁用「設定我」儲存按鈕
2. 然後逐步建立 ConfigService
3. 最後遷移所有配置操作到統一接口

你希望我先做哪一個?
