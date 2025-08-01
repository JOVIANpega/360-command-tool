# -*- coding: utf-8 -*-
"""
ADB 工作器模組
負責使用 ADB 執行指令
"""

import subprocess
import threading
import time
import re
from typing import List, Callable, Optional

# 導入核心模組
from core import (
    get_error_handler, get_async_manager, safe_execute,
    log_debug, log_info, log_error, profile
)


class ADBWorker(threading.Thread):
    """ADB 工作器 - 使用 adb shell 執行指令"""

    def __init__(self, cmd_list: List[str], end_str: str, timeout: float,
                 on_data: Callable, on_status: Callable, on_progress: Callable,
                 on_finish: Callable, stop_event: threading.Event):
        super().__init__()

        # 初始化核心組件
        self.error_handler = get_error_handler()
        self.async_manager = get_async_manager()

        # ADB 參數
        self.cmd_list = cmd_list
        self.end_str = end_str
        self.timeout = timeout

        # 回調函數
        self.on_data = on_data
        self.on_status = on_status
        self.on_progress = on_progress
        self.on_finish = on_finish
        self.stop_event = stop_event

        # 設置為守護線程
        self.daemon = True

        # 用於顯示訊息的回調函數
        self.show_message_callback: Optional[Callable] = None

        log_debug(f"ADBWorker 初始化: 指令數={len(cmd_list)}, 超時={timeout}s")

    def check_adb_connection(self):
        """檢查 ADB 連接狀態"""
        try:
            result = subprocess.run(['adb', 'devices'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                devices = result.stdout.strip().split('\n')[1:]  # 跳過標題行
                connected_devices = [line for line in devices if line.strip() and 'device' in line]
                return len(connected_devices) > 0
            return False
        except Exception as e:
            log_error(f"檢查 ADB 連接時發生錯誤: {e}")
            return False

    def execute_adb_command(self, command: str) -> tuple:
        """執行單個 ADB 指令"""
        try:
            # 構建 adb shell 指令
            adb_cmd = ['adb', 'shell', command]
            
            # 執行指令
            result = subprocess.run(adb_cmd, capture_output=True, text=True, timeout=30)
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return -1, "", "指令執行超時"
        except Exception as e:
            return -1, "", str(e)

    @profile("ADBWorker.run")
    def run(self):
        """主執行方法"""
        start_time = time.time()
        log_info("開始執行 ADB 任務")

        try:
            # 檢查 ADB 連接
            if not self.check_adb_connection():
                self.on_data("\n[錯誤] 沒有檢測到 ADB 設備連接\n", "error")
                self.on_data("請確認：\n", "error")
                self.on_data("1. 設備已連接並開啟 USB 調試\n", "error")
                self.on_data("2. ADB 驅動已正確安裝\n", "error")
                self.on_data("3. 執行 'adb devices' 可以看到設備\n", "error")
                return

            self.on_status(True)
            finished = False

            # 執行所有指令
            for i, cmd in enumerate(self.cmd_list):
                if self.stop_event.is_set() or finished:
                    break

                cmd = cmd.strip()
                if not cmd:
                    continue

                # 處理特殊指令: DELAY
                delay_match = re.match(r'^DELAY:(\d+)$', cmd)
                if delay_match:
                    delay_seconds = int(delay_match.group(1))
                    self.on_data(f'\n[系統] 延遲 {delay_seconds} 秒...\n', "purple")
                    
                    # 分段延遲，每秒更新一次進度
                    for j in range(delay_seconds):
                        if self.stop_event.is_set() or finished:
                            break
                        time.sleep(1)
                        progress = ((j + 1) / delay_seconds) * 100
                        self.on_progress(progress)
                        self.on_data(f'剩餘 {delay_seconds - j - 1} 秒...\r', "purple")
                    
                    self.on_data(f'\n[系統] 延遲結束\n', "purple")
                    continue

                # 處理特殊指令: SHOW
                show_match = re.match(r'^SHOW:(.+)$', cmd)
                if show_match:
                    message = show_match.group(1)
                    self.on_data(f'\n[顯示] {message}\n', "purple")
                    
                    if self.show_message_callback:
                        try:
                            self.show_message_callback("提示", message)
                        except Exception as e:
                            self.on_data(f'[錯誤] 顯示消息框時發生錯誤: {e}\n', "error")
                    else:
                        self.on_data(f'[警告] 無法顯示消息框，因為未設置回調函數\n', "error")
                    
                    continue

                # 正常指令處理
                self.on_data(f'\n[ADB 發送] {cmd}\n', "send")
                
                # 執行 ADB 指令
                returncode, stdout, stderr = self.execute_adb_command(cmd)
                
                # 處理執行結果
                if returncode == 0:
                    if stdout:
                        self.on_data(stdout, None)
                    
                    # 檢查是否收到結束字串
                    if self.end_str and self.end_str in stdout:
                        if i == len(self.cmd_list) - 1:
                            self.on_data(f'\n[結束] 收到指定結束字串 {self.end_str}\n', "end")
                            finished = True
                else:
                    # 指令執行失敗
                    if stderr:
                        self.on_data(f'\n[錯誤] {stderr}\n', "error")
                    else:
                        self.on_data(f'\n[錯誤] 指令執行失敗 (返回碼: {returncode})\n', "error")

                # 更新進度
                progress = ((i + 1) / len(self.cmd_list)) * 100
                self.on_progress(progress)

                # 指令間隔1秒
                if i < len(self.cmd_list) - 1:  # 不是最後一個指令
                    time.sleep(1)

            # 如果沒有在執行指令時接收到結束字串，則標記完成
            if not finished and not self.stop_event.is_set():
                self.on_data(f'\n[系統] 所有 ADB 指令已執行完成\n', "purple")

        except Exception as e:
            self.on_data(f'\n[錯誤] ADB 執行時發生錯誤: {e}\n', "error")
            log_error(f"ADB 執行錯誤: {e}")

        finally:
            # 更新狀態
            self.on_status(False)
            self.on_finish()
            log_debug("ADBWorker 執行完成")

    def set_show_message_callback(self, callback: Callable):
        """設置顯示消息框的回調函數"""
        self.show_message_callback = callback
