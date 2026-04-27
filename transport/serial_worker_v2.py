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
    
    def __init__(self, com: str, cmd_list, end_str: str, timeout: float, baudrate: int = 115200,
                 on_data=None, on_status=None, on_progress=None, on_finish=None, stop_event=None, cmd_timeout: float = 10.0, cmd_interval: float = 1.0):
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
            cmd_timeout=cmd_timeout,
            cmd_interval=cmd_interval
        )
        
        # 序列埠特定參數
        self.com = com
        self.baudrate = baudrate
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
                self.baudrate, 
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
        執行序列埠指令 (支援先等後送邏輯)
        """
        try:
            if not self.serial_connection:
                return -1, "", "序列埠未連線"
            
            # 預置變數
            wait_before_str = None
            final_cmd = cmd
            current_end_str = self.end_str
            
            # 檢查是否有自定義預期字串 (格式: <<WaitStr>>Command)
            if cmd.startswith("<<") and ">>" in cmd:
                end_tag_pos = cmd.find(">>")
                wait_before_str = cmd[2:end_tag_pos].lower() # 提取並轉小寫，以便不區分大小寫比對
                final_cmd = cmd[end_tag_pos+2:]      # 提取要發送的指令
                log_info(f"[提示] 本步驟改為：先等待 \"{wait_before_str}\" (不分大小寫)")
            
            buffer = ""
            cmd_start_time = time.time()
            
            # --- 階段 1: 等待模式 (加入靜默偵測) ---
            if wait_before_str:
                self.on_data(f"[系統] 正在等待提示符: \"{wait_before_str}\" ...\n", "purple")
                while not self.stop_event.is_set():
                    if (time.time() - cmd_start_time) > self.cmd_timeout:
                        self.on_data(f'\n[警告] 等不到 "{wait_before_str}" (超時)，強行發送\n', "warning")
                        break
                    
                    data = self.serial_connection.read(1024)
                    if data:
                        text = data.decode(errors='ignore')
                        buffer += text
                        self.global_buffer += text
                        self.on_data(text, None)
                        
                        # 核心修改：智慧匹配
                        # 如果是 password，我們放寬匹配條件，只要包含 password 即可
                        # (解決 [sudo] password for pega: 中間夾雜文字的問題)
                        match_target = wait_before_str.replace(":", "") if "password" in wait_before_str else wait_before_str
                        
                        if match_target in buffer.lower():
                            # 看到提示符了！接著進行「靜默偵測」：
                            # 持續讀取直到連續 0.3 秒沒新字噴出來，確保畫面已停止
                            self.on_data(f"\n[系統] 偵測到 \"{match_target}\"，等待畫面靜止 (0.3s)...\n", "purple")
                            last_read_time = time.time()
                            while (time.time() - last_read_time) < 0.3:
                                # 檢查是否有新資料傳入
                                if self.serial_connection.in_waiting > 0:
                                    more_data = self.serial_connection.read(self.serial_connection.in_waiting)
                                    if more_data:
                                        self.on_data(more_data.decode(errors='ignore'), None)
                                        last_read_time = time.time()
                                time.sleep(0.05)
                            break
                    time.sleep(0.05)
            
            # --- 階段 2: 發送指令 ---
            if wait_before_str:
                # 對於敏感指令（登入、密碼），採用仿人類慢速打字，每個字元停 0.05 秒
                for char in final_cmd:
                    self.serial_connection.write(char.encode())
                    time.sleep(0.05)
                self.serial_connection.write('\r'.encode()) # 修正為單一 \r (CR)
            else:
                self.serial_connection.write((final_cmd + '\r').encode()) # 修正為單一 \r
            self.serial_connection.flush()
            
            # --- 階段 3: 等待回顯或後續提示符 ---
            if wait_before_str:
                time.sleep(1.0) # 密碼送出後多等一秒讓設備反應
                return 0, buffer, ""

            # 原有邏輯：發送後等待結束字串
            while not self.stop_event.is_set():
                elapsed = time.time() - cmd_start_time
                if elapsed > self.cmd_timeout:
                    self.on_data(f'\n[警告] 命令 "{final_cmd}" 等待響應超過 {self.cmd_timeout} 秒，繼續執行下一步\n', "warning")
                    return 0, buffer, ""
                
                data = self.serial_connection.read(1024)
                if data:
                    text = data.decode(errors='ignore')
                    buffer += text
                    self.global_buffer += text
                    self.on_data(text, None)
                    
                    if current_end_str and current_end_str in buffer:
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
