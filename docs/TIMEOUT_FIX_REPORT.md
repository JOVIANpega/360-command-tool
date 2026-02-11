# 🔧 超時邏輯修復報告

## 📋 問題描述

用戶反饋：重構後的行為與舊版本不同

### 舊版本行為（正確）
```
1. 單個指令超時（1秒）→ 顯示警告，繼續執行下一個指令
2. 所有指令執行完 → 繼續等待最終回應
3. 總超時（30秒）→ 顯示總超時警告，結束執行
```

### 新版本行為（錯誤）
```
1. 單個指令超時（1秒）→ 顯示錯誤，直接停止 ❌
2. 沒有等待最終回應的邏輯 ❌
```

---

## ✅ 已修復

### 修復 1: serial_worker_v2.py
**修改內容**：
- 單個指令超時時，改為顯示**警告**而非錯誤
- 返回成功（returncode=0），讓流程繼續執行

**修改前**：
```python
if elapsed > self.cmd_timeout:
    return -1, buffer, f"指令執行超時 ({self.cmd_timeout}s)"  # 返回錯誤
```

**修改後**：
```python
if elapsed > self.cmd_timeout:
    # 單個指令超時：顯示警告，但繼續執行（返回成功）
    self.on_data(f'\n[警告] 命令 "{cmd}" 等待響應超過 {self.cmd_timeout} 秒，繼續執行下一步\n', "warning")
    return 0, buffer, ""  # 返回成功，讓流程繼續
```

### 修復 2: serial_worker_v2.py - 新增方法
**新增**：`wait_for_final_response()` 方法
- 在所有指令執行完後，繼續讀取序列埠資料
- 等待結束字串或總超時

```python
def wait_for_final_response(self, start_time: float) -> bool:
    """等待最終回應（在所有指令執行完後）"""
    while not self.stop_event.is_set():
        elapsed = time.time() - start_time
        if elapsed > self.timeout:
            return False  # 總超時
        
        data = self.serial_connection.read(1024)
        if data:
            text = data.decode(errors='ignore')
            self.global_buffer += text
            self.on_data(text, None)
            
            # 檢查是否收到結束字串
            if self.end_str and self.end_str in self.global_buffer:
                self.on_data(f'\n[結束] 收到指定結束字串 {self.end_str}\n', "end")
                return True  # 收到結束字串
        
        time.sleep(0.1)
    
    return False
```

### 修復 3: base_worker.py
**修改內容**：
- 在所有指令執行完後，調用子類的 `wait_for_final_response()` 方法
- 如果子類沒有此方法，使用簡單等待

```python
# 步驟 3: 如果沒有收到結束字串，繼續等待最終回應
if not finished and not self.stop_event.is_set():
    self.on_data(f'\n[{transport_name}] 所有指令已發送，等待最終回應...\n', "purple")
    
    # 如果子類有 wait_for_final_response 方法，則調用它
    if hasattr(self, 'wait_for_final_response'):
        finished = self.wait_for_final_response(start_time)
        if finished:
            # 已收到結束字串
            pass
        else:
            # 總超時
            elapsed = time.time() - start_time
            if elapsed > self.timeout:
                self.on_data(f'\n[{transport_name}] 總超時 ({self.timeout}秒)，結束執行\n', "warning")
```

---

## 🎯 修復後的行為

### 現在的行為（與舊版本一致）
```
1. 單個指令超時（1秒）→ 顯示警告，繼續執行下一個指令 ✓
2. 所有指令執行完 → 繼續等待最終回應 ✓
3. 總超時（30秒）→ 顯示總超時警告，結束執行 ✓
```

### 預期輸出
```
=== 執行指令: 44 Write MAC ===
COM 口: COM4, 超時: 30 秒, 結束字串: root

01  發送指令 ./mfg_sources/mb_eeprom_rw.sh w mac_address 00:a0:c9:11:22:33
[Console 發送] ./mfg_sources/mb_eeprom_rw.sh w mac_address 00:a0:c9:11:22:33
./mfg_sources/mb_eeprom_rw.sh w mac_address 00:a0:c9:11:22:33

[警告] 命令 "./mfg_sources/mb_eeprom_rw.sh w mac_address 00:a0:c9:11:22:33" 等待響應超過 1.0 秒，繼續執行下一步

####################

[Console] 所有指令已發送，等待最終回應...
Writing MAC address: 00:a0:c9:11:22:33
Done
root@device:~#

[結束] 收到指定結束字串 root

[Console] 所有指令已執行完成
```

---

## 📊 對比總結

| 項目 | 舊版本 | 新版本（修復前） | 新版本（修復後） |
|------|--------|-----------------|-----------------|
| 單個指令超時 | 警告，繼續 | 錯誤，停止 ❌ | 警告，繼續 ✓ |
| 等待最終回應 | 有 | 無 ❌ | 有 ✓ |
| 總超時處理 | 有 | 無 ❌ | 有 ✓ |
| 行為一致性 | - | 不一致 ❌ | 一致 ✓ |

---

## 🔍 技術細節

### 全域緩衝區
新增 `self.global_buffer` 用於跨指令檢查結束字串：
- 每個指令執行時，累積到全域緩衝區
- 等待最終回應時，繼續累積到全域緩衝區
- 檢查結束字串時，使用全域緩衝區

### 超時層級
1. **單個指令超時** (`cmd_timeout`，預設 1.0秒)
   - 超時後顯示警告
   - 繼續執行下一個指令

2. **總超時** (`timeout`，預設 30秒)
   - 從開始執行到結束的總時間
   - 超時後顯示警告並結束

---

## ✅ 驗證清單

請驗證以下場景：

### 場景 1: 正常執行
- [ ] 指令在 1 秒內完成
- [ ] 收到結束字串
- [ ] 顯示「所有指令已執行完成」

### 場景 2: 單個指令超時
- [ ] 指令超過 1 秒未完成
- [ ] 顯示警告訊息
- [ ] 繼續執行下一個指令

### 場景 3: 等待最終回應
- [ ] 所有指令執行完
- [ ] 顯示「等待最終回應...」
- [ ] 繼續讀取序列埠資料
- [ ] 收到結束字串後結束

### 場景 4: 總超時
- [ ] 30 秒內未收到結束字串
- [ ] 顯示總超時警告
- [ ] 結束執行

---

**修復日期**: 2026-02-11
**修復者**: Antigravity AI
**狀態**: ✅ 已修復，待驗證
