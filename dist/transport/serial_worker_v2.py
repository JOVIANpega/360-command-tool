# -*- coding: utf-8 -*-
"""
序列埠工作器 - 重構版本 (繼承 BaseWorker)
只實現序列埠特定邏輯，共用邏輯由 BaseWorker 提供
"""
import serial
import time
from typing import Tuple
import sys
import os

# 添加 transport 目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from transport.base_worker import BaseWorker

# 導入核心模組
from core import log_debug, log_info, log_error


class SerialWorkerV2(BaseWorker):
    """
    序列埠工作器 - 重構版本
    
    只實現序列埠特定的邏輯：
    - 序列埠連線管理
    - 序列埠指令執行
    - 序列埠回應讀取
    
    所有共用邏輯 (DELAY, SHOW, 進度管理等) 都由 BaseWorker 提供
    """
    
    def __init__(self, com: str, cmd_list, end_str: str, timeout: float,
                 on_data, on_status, on_progress, on_finish, stop_event, cmd_timeout: float = 10.0):
        """
        初始化序列埠工作器
        
        Args:
            com: COM 埠號 (如 "COM3")
            其他參數傳遞給 BaseWorker
        """
        super().__init__(
            cmd_list=cmd_list,
            end_str=end_str,
            timeout=timeout,
            on_data=on_data,
            on_status=on_status,
            on_progress=on_progress,
            on_finish=on_finish,
            stop_event=stop_event,
            cmd_timeout=cmd_timeout
        )
        
        # 序列埠特定參數
        self.com = com
        self.serial_connection = None
        self.global_buffer = ""  # 全域緩衝區，用於檢查結束字串
        
        log_debug(f"SerialWorkerV2 初始化: COM={com}")
    
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
            log_info(f"序列埠連線成功: {self.com}")
            return True
            
        except serial.SerialException as e:
            error_msg = str(e)
            if "PermissionError" in error_msg or "存取被拒" in error_msg or "Access is denied" in error_msg:
                self.on_data(f'\n[錯誤] 無法開啟 {self.com} (存取被拒)\n', "error")
                self.on_data(f'[提示] 該 COM 口可能正被其他程式 (如 Tera Term) 佔用中。\n', "warning")
                self.on_data(f'[建議 1] 請暫時斷開 Tera Term 連線 (File -> Disconnect)。\n', "warning")
                self.on_data(f'[建議 2] 若需同時開啟 Tera Term 看 Log，請將「傳輸方式」改為 ADB 模式。\n', "warning")
            else:
                self.on_data(f'\n[錯誤] 序列埠錯誤: {e}\n', "error")
            log_error(f"序列埠連線失敗: {e}")
            return False
            
        except Exception as e:
            self.on_data(f'\n[錯誤] 連線失敗: {e}\n', "error")
            log_error(f"序列埠連線失敗: {e}")
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
                    # 單個指令超時：顯示警告，但繼續執行（返回成功）
                    self.on_data(f'\n[警告] 命令 "{cmd}" 等待響應超過 {self.cmd_timeout} 秒，繼續執行下一步\n', "warning")
                    return 0, buffer, ""  # 返回成功，讓流程繼續
                
                data = self.serial_connection.read(1024)
                if data:
                    text = data.decode(errors='ignore')
                    buffer += text
                    self.global_buffer += text
                    
                    # 即時輸出到介面
                    self.on_data(text, None)
                    
                    # 檢查是否收到結束字串
                    if self.end_str and self.end_str in buffer:
                        return 0, buffer, ""
                
                time.sleep(0.1)
            
            return 0, buffer, ""
            
        except Exception as e:
            log_error(f"執行序列埠指令失敗: {e}")
            return -1, "", str(e)
    
    def wait_for_final_response(self, start_time: float) -> bool:
        """
        等待最終回應（在所有指令執行完後）
        
        Args:
            start_time: 開始時間
            
        Returns:
            bool: 如果收到結束字串返回 True
        """
        try:
            if not self.serial_connection:
                return False
            
            final_wait_start = time.time()  # 記錄開始等待最終回應的時間
            last_data_time = time.time()    # 記錄最後一次收到資料的時間
            
            while not self.stop_event.is_set():
                elapsed = time.time() - start_time
                if elapsed > self.timeout:
                    # 總超時
                    return False
                
                # 智能結束：如果等待最終回應已超過 5 秒且沒有新數據，認為已完成
                if time.time() - last_data_time > 5:
                    self.on_data(f'\n[系統] 沒有更多數據，執行完成\n', "purple")
                    return False
                
                data = self.serial_connection.read(1024)
                if data:
                    text = data.decode(errors='ignore')
                    self.global_buffer += text
                    last_data_time = time.time()  # 更新最後收到資料的時間
                    
                    # 即時輸出到介面
                    self.on_data(text, None)
                    
                    # 檢查是否收到結束字串
                    if self.end_str and self.end_str in self.global_buffer:
                        self.on_data(f'\n[結束] 收到指定結束字串 {self.end_str}\n', "end")
                        return True
                
                time.sleep(0.1)
            
            return False
            
        except Exception as e:
            log_error(f"等待最終回應時發生錯誤: {e}")
            return False
    
    def disconnect(self):
        """關閉序列埠連線"""
        try:
            if self.serial_connection:
                self.serial_connection.close()
                self.serial_connection = None
                log_debug(f"序列埠已關閉: {self.com}")
        except Exception as e:
            log_debug(f"關閉序列埠時發生錯誤（已忽略）: {e}")
    
    def get_transport_name(self) -> str:
        """獲取傳輸方式名稱"""
        return "Console"
