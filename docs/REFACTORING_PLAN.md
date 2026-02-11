# 🔧 程式碼重構計劃 - 避免交叉影響

## 📋 問題分析

### 當前問題
修改 Console (serial_worker.py) 時，可能影響到 ADB (adb_worker.py) 或 SSH (ssh_worker.py)，原因：

1. **重複的程式碼** (Code Duplication)
   - 三個 worker 有 70% 相似的邏輯
   - 特殊指令處理 (DELAY, SHOW) 重複實現 3 次
   - 進度更新邏輯重複 3 次
   - 錯誤處理邏輯重複 3 次

2. **缺乏抽象層** (No Abstraction)
   - 沒有共用的基礎類別
   - 沒有統一的介面定義
   - 每個 worker 都是獨立實現

3. **職責混亂** (Mixed Responsibilities)
   - Worker 同時處理：連線管理、指令執行、特殊指令、進度回報
   - 難以單獨測試某一功能

## 🎯 解決方案

### 方案 A: 提取共用基礎類別 (推薦) ⭐

#### 架構設計
```
BaseWorker (抽象基礎類別)
  ├─ 共用功能
  │   ├─ 特殊指令處理 (DELAY, SHOW)
  │   ├─ 進度管理
  │   ├─ 錯誤處理
  │   └─ 回調管理
  │
  ├─ 抽象方法 (子類必須實現)
  │   ├─ connect()
  │   ├─ execute_command()
  │   └─ disconnect()
  │
  └─ 子類實現
      ├─ SerialWorker (只實現序列埠特定邏輯)
      ├─ ADBWorker (只實現 ADB 特定邏輯)
      └─ SSHWorker (只實現 SSH 特定邏輯)
```

#### 優點
✅ 修改共用邏輯時，三個 worker 同步更新
✅ 修改特定 worker 時，不影響其他 worker
✅ 程式碼量減少約 40%
✅ 易於測試和維護
✅ 新增傳輸方式更容易

#### 實作步驟

**步驟 1: 建立 BaseWorker**
```python
# transport/base_worker.py
class BaseWorker(threading.Thread):
    """傳輸層基礎類別"""
    
    def __init__(self, cmd_list, end_str, timeout, ...):
        # 共用初始化
        
    def run(self):
        """主執行流程 (模板方法)"""
        try:
            if not self.connect():
                return
            
            for i, cmd in enumerate(self.cmd_list):
                if self.stop_event.is_set():
                    break
                
                # 處理特殊指令
                if self._handle_special_command(cmd):
                    continue
                
                # 執行正常指令
                self._execute_normal_command(cmd, i)
            
        finally:
            self.disconnect()
    
    # 抽象方法 (子類必須實現)
    @abstractmethod
    def connect(self) -> bool:
        """建立連線"""
        pass
    
    @abstractmethod
    def execute_command(self, cmd: str) -> tuple:
        """執行單個指令"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """關閉連線"""
        pass
    
    # 共用方法
    def _handle_special_command(self, cmd: str) -> bool:
        """處理特殊指令 (DELAY, SHOW)"""
        # 統一實現，三個 worker 共用
        
    def _execute_normal_command(self, cmd: str, index: int):
        """執行正常指令的通用流程"""
        # 統一實現，呼叫子類的 execute_command()
```

**步驟 2: 簡化 SerialWorker**
```python
# transport/serial_worker.py
class SerialWorker(BaseWorker):
    """序列埠工作器 - 只實現序列埠特定邏輯"""
    
    def connect(self) -> bool:
        """建立序列埠連線"""
        try:
            self.ser = serial.Serial(self.com, 115200, timeout=0.1)
            return True
        except Exception as e:
            self.on_data(f"連線失敗: {e}", "error")
            return False
    
    def execute_command(self, cmd: str) -> tuple:
        """執行序列埠指令"""
        self.ser.write((cmd + '\r\n').encode())
        # ... 讀取回應 ...
        return (returncode, stdout, stderr)
    
    def disconnect(self):
        """關閉序列埠"""
        if self.ser:
            self.ser.close()
```

**步驟 3: 簡化 ADBWorker**
```python
# transport/adb_worker.py
class ADBWorker(BaseWorker):
    """ADB 工作器 - 只實現 ADB 特定邏輯"""
    
    def connect(self) -> bool:
        """檢查 ADB 連線"""
        return self.check_adb_connection()
    
    def execute_command(self, cmd: str) -> tuple:
        """執行 ADB 指令"""
        result = subprocess.run(['adb', 'shell', cmd], ...)
        return (result.returncode, result.stdout, result.stderr)
    
    def disconnect(self):
        """ADB 不需要斷線"""
        pass
```

**步驟 4: 簡化 SSHWorker**
```python
# transport/ssh_worker.py
class SSHWorker(BaseWorker):
    """SSH 工作器 - 只實現 SSH 特定邏輯"""
    
    def connect(self) -> bool:
        """建立 SSH 連線"""
        # ... SSH 連線邏輯 ...
        return self.connected
    
    def execute_command(self, cmd: str) -> tuple:
        """執行 SSH 指令"""
        stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
        return (return_code, stdout_data, stderr_data)
    
    def disconnect(self):
        """關閉 SSH 連線 (或保持持久連線)"""
        if not self.use_persistent:
            self.ssh_client.close()
```

---

### 方案 B: 策略模式 + 組合

#### 架構設計
```
CommandExecutor (統一執行器)
  │
  ├─ TransportStrategy (傳輸策略介面)
  │   ├─ SerialTransport
  │   ├─ ADBTransport
  │   └─ SSHTransport
  │
  ├─ SpecialCommandHandler (特殊指令處理器)
  │   ├─ DelayHandler
  │   └─ ShowHandler
  │
  └─ ProgressManager (進度管理器)
```

#### 優點
✅ 更高的靈活性
✅ 易於擴展新功能
✅ 職責更清晰

#### 缺點
❌ 架構較複雜
❌ 需要大量重構
❌ 學習曲線較陡

---

## 📊 對比分析

| 項目 | 當前架構 | 方案 A (推薦) | 方案 B |
|------|---------|--------------|--------|
| 程式碼重複 | 高 (70%) | 低 (10%) | 極低 (5%) |
| 維護難度 | 高 | 中 | 低 |
| 重構成本 | - | 中 | 高 |
| 擴展性 | 低 | 高 | 極高 |
| 學習曲線 | 低 | 中 | 高 |
| 測試難度 | 高 | 中 | 低 |

---

## 🚀 實施計劃 (方案 A)

### Phase 1: 準備階段 (1 天)
- [ ] 建立 `transport/` 目錄
- [ ] 建立 `base_worker.py`
- [ ] 撰寫單元測試框架

### Phase 2: 提取共用邏輯 (2 天)
- [ ] 提取特殊指令處理邏輯
- [ ] 提取進度管理邏輯
- [ ] 提取錯誤處理邏輯
- [ ] 建立抽象方法定義

### Phase 3: 重構 SerialWorker (1 天)
- [ ] 繼承 BaseWorker
- [ ] 實現抽象方法
- [ ] 移除重複程式碼
- [ ] 測試 Console 模式

### Phase 4: 重構 ADBWorker (1 天)
- [ ] 繼承 BaseWorker
- [ ] 實現抽象方法
- [ ] 移除重複程式碼
- [ ] 測試 ADB 模式

### Phase 5: 重構 SSHWorker (1 天)
- [ ] 繼承 BaseWorker
- [ ] 實現抽象方法
- [ ] 移除重複程式碼
- [ ] 測試 SSH 模式

### Phase 6: 整合測試 (1 天)
- [ ] 三種模式完整測試
- [ ] 回歸測試
- [ ] 效能測試
- [ ] 文件更新

---

## 📝 程式碼範例

### 當前問題示例
```python
# 問題：修改 serial_worker.py 的 DELAY 邏輯
# serial_worker.py (第 105-117 行)
delay_match = re.match(r'^DELAY:(\d+)$', cmd)
if delay_match:
    delay_seconds = int(delay_match.group(1))
    # ... 處理邏輯 ...

# adb_worker.py (第 135-147 行) - 完全相同的程式碼！
delay_match = re.match(r'^DELAY:(\d+)$', cmd)
if delay_match:
    delay_seconds = int(delay_match.group(1))
    # ... 處理邏輯 ...

# ssh_worker.py (第 378-390 行) - 又是相同的程式碼！
# 如果修改一處，必須手動同步其他兩處，容易遺漏
```

### 重構後示例
```python
# base_worker.py - 統一實現
class BaseWorker:
    def _handle_delay_command(self, cmd: str) -> bool:
        """處理 DELAY 指令 (統一實現)"""
        delay_match = re.match(r'^DELAY:(\d+)$', cmd)
        if delay_match:
            delay_seconds = int(delay_match.group(1))
            # ... 處理邏輯 ...
            return True
        return False

# serial_worker.py - 繼承即可使用
class SerialWorker(BaseWorker):
    # 自動繼承 _handle_delay_command()
    # 不需要重複實現！

# adb_worker.py - 繼承即可使用
class ADBWorker(BaseWorker):
    # 自動繼承 _handle_delay_command()
    # 不需要重複實現！

# ssh_worker.py - 繼承即可使用
class SSHWorker(BaseWorker):
    # 自動繼承 _handle_delay_command()
    # 不需要重複實現！

# ✅ 修改一次，三個 worker 同步更新！
```

---

## 🎯 預期效果

### 修改前
```
修改 Console 的 DELAY 邏輯
  ↓
需要手動同步到 ADB
  ↓
需要手動同步到 SSH
  ↓
容易遺漏，產生 Bug
```

### 修改後
```
修改 BaseWorker 的 DELAY 邏輯
  ↓
三個 worker 自動同步
  ↓
不會遺漏，不會產生交叉影響
```

---

## 🔍 測試策略

### 單元測試
```python
# tests/test_base_worker.py
def test_delay_command():
    """測試 DELAY 指令處理"""
    worker = MockWorker(...)
    result = worker._handle_delay_command("DELAY:5")
    assert result == True

# tests/test_serial_worker.py
def test_serial_specific():
    """測試序列埠特定功能"""
    worker = SerialWorker(...)
    # 只測試序列埠特定邏輯
```

### 整合測試
```python
# tests/test_integration.py
def test_all_workers_consistency():
    """確保三個 worker 行為一致"""
    # 使用相同的指令列表測試三個 worker
    # 驗證輸出格式一致
```

---

## 📚 參考資料

### 設計模式
- **模板方法模式** (Template Method Pattern)
  - BaseWorker.run() 定義執行流程
  - 子類實現具體步驟

- **策略模式** (Strategy Pattern)
  - 不同的傳輸策略可以互換

### 最佳實踐
- **DRY 原則** (Don't Repeat Yourself)
  - 消除重複程式碼

- **單一職責原則** (Single Responsibility Principle)
  - 每個類別只負責一件事

- **開放封閉原則** (Open-Closed Principle)
  - 對擴展開放，對修改封閉

---

## ✅ 檢查清單

### 重構前
- [ ] 備份當前程式碼
- [ ] 建立測試案例
- [ ] 記錄當前行為

### 重構中
- [ ] 逐步重構，不要一次改太多
- [ ] 每個步驟都要測試
- [ ] 保持版本控制

### 重構後
- [ ] 完整測試三種模式
- [ ] 更新文件
- [ ] 程式碼審查

---

## 🎓 建議

### 立即可做
1. **建立測試案例** - 確保重構不會破壞現有功能
2. **提取常數** - 將魔術數字提取為常數
3. **統一命名** - 確保三個 worker 使用一致的變數名稱

### 短期目標 (1-2 週)
1. **實施方案 A** - 建立 BaseWorker
2. **重構一個 worker** - 先重構 SerialWorker 作為範例
3. **驗證效果** - 確認重構後的程式碼更易維護

### 長期目標 (1-2 個月)
1. **完成所有重構** - 三個 worker 都繼承 BaseWorker
2. **建立完整測試** - 單元測試 + 整合測試
3. **文件化** - 更新架構文件和使用說明

---

**建立日期**: 2026-02-11
**建立者**: Antigravity AI
**狀態**: 待實施
