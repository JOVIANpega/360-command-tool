# -*- coding: utf-8 -*-
"""
序列埠工作器 - 重構版本 (使用 BaseWorker)
"""
import serial
from typing import Tuple
from transport.base_worker import BaseWorker


class SerialWorkerRefactored(BaseWorker):
    """
    序列埠工作器 - 重構版本
    
    只實現序列埠特定的邏輯：
    - 序列埠連線管理
    - 序列埠指令執行
    - 序列埠回應讀取
    
    所有共用邏輯 (DELAY, SHOW, 進度管理等) 都由 BaseWorker 提供
    """
    
    def __init__(self, com: str, *args, **kwargs):
        """
        初始化序列埠工作器
        
        Args:
            com: COM 埠號 (如 "COM3")
            *args, **kwargs: 傳遞給 BaseWorker 的參數
        """
        super().__init__(*args, **kwargs)
        
        # 序列埠特定參數
        self.com = com
        self.serial_connection = None
    
    # ==================== 實現抽象方法 ====================
    
    def connect(self) -> bool:
        """
        建立序列埠連線
        
        Returns:
            bool: 連線成功返回 True，失敗返回 False
        """
        try:
            self.serial_connection = serial.Serial(
                self.com, 
                115200, 
                timeout=0.1
            )
            self.on_data(f"\n[Console] 已連線到 {self.com}\n", "info")
            return True
            
        except serial.SerialException as e:
            error_msg = str(e)
            if "PermissionError" in error_msg or "存取被拒" in error_msg:
                self.on_data(f'\n[錯誤] 無法開啟 {self.com} (存取被拒)\n', "error")
                self.on_data(f'[提示] 該 COM 口可能正被其他程式佔用\n', "warning")
                self.on_data(f'[建議] 請關閉 Tera Term 或改用 ADB/SSH 模式\n', "warning")
            else:
                self.on_data(f'\n[錯誤] 序列埠錯誤: {e}\n', "error")
            return False
            
        except Exception as e:
            self.on_data(f'\n[錯誤] 連線失敗: {e}\n', "error")
            return False
    
    def execute_command(self, cmd: str) -> Tuple[int, str, str]:
        """
        執行序列埠指令
        
        Args:
            cmd: 要執行的指令
            
        Returns:
            Tuple[int, str, str]: (返回碼, 標準輸出, 標準錯誤)
        """
        try:
            if not self.serial_connection:
                return -1, "", "序列埠未連線"
            
            # 發送指令
            self.serial_connection.write((cmd + '\r\n').encode())
            self.serial_connection.flush()
            
            # 讀取回應
            buffer = ""
            cmd_start_time = time.time()
            
            while not self.stop_event.is_set():
                elapsed = time.time() - cmd_start_time
                if elapsed > self.cmd_timeout:
                    return -1, buffer, f"指令執行超時 ({self.cmd_timeout}s)"
                
                data = self.serial_connection.read(1024)
                if data:
                    text = data.decode(errors='ignore')
                    buffer += text
                    
                    # 檢查是否收到結束字串
                    if self.end_str and self.end_str in buffer:
                        return 0, buffer, ""
                
                time.sleep(0.1)
            
            return 0, buffer, ""
            
        except Exception as e:
            return -1, "", str(e)
    
    def disconnect(self):
        """關閉序列埠連線"""
        try:
            if self.serial_connection:
                self.serial_connection.close()
                self.serial_connection = None
                self.on_data(f"\n[Console] 已關閉 {self.com}\n", "info")
        except Exception as e:
            # 忽略關閉時的錯誤
            pass
    
    def get_transport_name(self) -> str:
        """獲取傳輸方式名稱"""
        return "Console"


# ==================== 對比說明 ====================

"""
重構前 (serial_worker.py):
- 274 行程式碼
- 包含大量重複邏輯 (DELAY, SHOW, 進度管理)
- 修改 DELAY 邏輯需要同步到 ADB 和 SSH

重構後 (serial_worker_refactored.py):
- 約 100 行程式碼 (減少 63%)
- 只包含序列埠特定邏輯
- 修改 DELAY 邏輯只需修改 BaseWorker，自動同步

優點：
✅ 程式碼量大幅減少
✅ 職責更清晰
✅ 易於測試
✅ 不會交叉影響
✅ 易於擴展

使用範例：
```python
# 使用方式與原版完全相同
worker = SerialWorkerRefactored(
    com="COM3",
    cmd_list=["ls", "pwd"],
    end_str="root",
    timeout=30,
    on_data=on_data_callback,
    on_status=on_status_callback,
    on_progress=on_progress_callback,
    on_finish=on_finish_callback,
    stop_event=stop_event,
    cmd_timeout=10.0
)
worker.start()
```
"""
