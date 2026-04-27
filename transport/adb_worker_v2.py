# -*- coding: utf-8 -*-
"""
ADB 工作器 - 重構版本 (繼承 BaseWorker)
只實現 ADB 特定邏輯，共用邏輯由 BaseWorker 提供
"""
import subprocess
import sys
import os
from typing import Tuple

# 添加 transport 目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from transport.base_worker import BaseWorker

# 導入核心模組
from core import log_debug, log_info, log_error


class ADBWorkerV2(BaseWorker):
    """
    ADB 工作器 - 重構版本
    
    只實現 ADB 特定的邏輯：
    - ADB 連線檢查
    - ADB 指令執行
    
    所有共用邏輯 (DELAY, SHOW, 進度管理等) 都由 BaseWorker 提供
    """
    
    def __init__(self, cmd_list, end_str: str, timeout: float,
                 on_data, on_status, on_progress, on_finish, stop_event, cmd_timeout: float = 30.0, cmd_interval: float = 1.0):
        """
        初始化 ADB 工作器
        
        Args:
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
        
        log_debug("ADBWorkerV2 初始化")
    
    # ==================== 實現抽象方法 ====================
    
    def connect(self) -> bool:
        """
        檢查 ADB 連線
        
        Returns:
            bool: 連線成功返回 True，失敗返回 False
        """
        try:
            # 在 Windows 上隱藏 DOS 視窗
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            result = subprocess.run(['adb', 'devices'],
                                  capture_output=True, text=True, timeout=5,
                                  startupinfo=startupinfo)
            
            if result.returncode == 0:
                devices = result.stdout.strip().split('\n')[1:]  # 跳過標題行
                connected_devices = [line for line in devices if line.strip() and 'device' in line]
                
                if len(connected_devices) > 0:
                    log_info("ADB 連線成功")
                    return True
                else:
                    self.on_data("\n[錯誤] 沒有檢測到 ADB 設備連接\n", "error")
                    self.on_data("請確認：\n", "error")
                    self.on_data("1. 設備已連接並開啟 USB 調試\n", "error")
                    self.on_data("2. ADB 驅動已正確安裝\n", "error")
                    self.on_data("3. 執行 'adb devices' 可以看到設備\n", "error")
                    return False
            
            return False
            
        except Exception as e:
            log_error(f"檢查 ADB 連接時發生錯誤: {e}")
            self.on_data(f"\n[錯誤] ADB 連線檢查失敗: {e}\n", "error")
            return False
    
    def execute_command(self, cmd: str) -> Tuple[int, str, str]:
        """
        執行 ADB 指令
        
        Args:
            cmd: 要執行的指令
            
        Returns:
            Tuple[int, str, str]: (返回碼, 標準輸出, 標準錯誤)
        """
        try:
            # 構建 adb shell 指令
            adb_cmd = ['adb', 'shell', cmd]

            # 在 Windows 上隱藏 DOS 視窗
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            # 執行指令
            result = subprocess.run(adb_cmd, capture_output=True, text=True, timeout=self.cmd_timeout,
                                  startupinfo=startupinfo)

            # 即時輸出結果
            if result.stdout:
                self.on_data(result.stdout, None)

            return result.returncode, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            # 超時：顯示警告，但繼續執行（返回成功）
            self.on_data(f'\n[警告] 命令 "{cmd}" 等待響應超過 {self.cmd_timeout} 秒，繼續執行下一步\n', "warning")
            return 0, "", ""  # 返回成功，讓流程繼續
        except Exception as e:
            log_error(f"執行 ADB 指令失敗: {e}")
            return -1, "", str(e)
    
    def disconnect(self):
        """ADB 不需要斷線"""
        log_debug("ADB 工作器結束")
    
    def get_transport_name(self) -> str:
        """獲取傳輸方式名稱"""
        return "ADB"
