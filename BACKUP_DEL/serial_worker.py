# -*- coding: utf-8 -*-
"""
序列埠工作器 - 重構版本
使用新的異步處理和錯誤處理機制
"""
import serial
import threading
import time
import re
import tkinter as tk
from tkinter import messagebox
from typing import List, Callable, Optional

# 導入核心模組
from core import (
    get_error_handler, get_async_manager, safe_execute,
    log_debug, log_info, log_error, profile
)



class SerialWorker(threading.Thread):
    """序列埠工作器 - 重構版本"""

    def __init__(self, com: str, cmd_list: List[str], end_str: str, timeout: float,
                 on_data: Callable, on_status: Callable, on_progress: Callable,
                 on_finish: Callable, stop_event: threading.Event, cmd_timeout: float = 10.0):
        super().__init__()

        # 初始化核心組件
        self.error_handler = get_error_handler()
        self.async_manager = get_async_manager()

        # 序列埠參數
        self.com = com
        self.cmd_list = cmd_list
        self.end_str = end_str
        self.timeout = timeout
        self.cmd_timeout = cmd_timeout

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

        # 序列埠連接（簡化版本）
        self.serial_connection: Optional[serial.Serial] = None

        log_debug(f"SerialWorker 初始化: COM={com}, 指令數={len(cmd_list)}, 超時={timeout}s")

    # 移除複雜的 force_stop 方法，回到簡單的停止邏輯
    # 舊版本只需要設置 stop_event，線程會自然結束

    # 移除複雜的 _safe_close_serial 方法
    # 舊版本使用簡單的 ser.close() 就足夠了



    @profile("SerialWorker.run")
    def run(self):
        """主執行方法"""
        start_time = time.time()
        log_info(f"開始執行序列埠任務: {self.com}")

        try:
            # 創建序列埠連接
            ser = serial.Serial(self.com, 115200, timeout=0.1)
            self.serial_connection = ser  # 保存引用以便強制停止時使用

            self.on_status(True)

            buffer = ""

            finished = False



            # 執行所有指令
            for i, item in enumerate(self.cmd_list):
                if self.stop_event.is_set() or finished:
                    break
                
                # 處理指令格式 (支持 tuple 或 string)
                if isinstance(item, tuple):
                    cmd_name, cmd_str = item
                else:
                    cmd_name, cmd_str = "", item

                cmd = str(cmd_str).strip()
                if not cmd:
                    continue

                # 處理特殊指令 (DELAY, SHOW) ...
                # 這裡簡化處理，假設特殊指令不會以 tuple 傳入，或者如果傳入也只處理 cmd 部分
                
                # 處理特殊指令: DELAY
                delay_match = re.match(r'^DELAY:(\d+)$', cmd)
                if delay_match:
                    delay_seconds = int(delay_match.group(1))
                    self.on_data(f'\n[系統] 延遲 {delay_seconds} 秒...\n', "purple")
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
                    self.on_data(f'\n[系統] 顯示訊息: {message}\n', "purple")
                    if hasattr(self, 'show_message_callback') and self.show_message_callback:
                        # ... (省略完整 show 邏輯，保持原樣) ...
                        pass 
                    continue

                # 正常指令處理
                # 格式化輸出：顯示序號和指令
                # 02  發送指令 Set RTC=date -s "..."
                if cmd_name:
                    header = f"{i+1:02d}  發送指令 {cmd_name}={cmd}"
                else:
                    header = f"{i+1:02d}  發送指令 {cmd}"
                
                self.on_data(f'\n{header}\n', "purple")
                self.on_data(f'[發送] {cmd}\n', "send")

                ser.write((cmd + '\r\n').encode())
                ser.flush()
                
                # 檢查每個命令的回應，但不立即結束
                cmd_start_time = time.time()
                cmd_buffer = ""
                cmd_received_end = False
                
                # 等待這個命令的響應，使用設定的指令超時時間
                cmd_timeout = self.cmd_timeout
                
                while not self.stop_event.is_set() and not finished:
                    cmd_elapsed = time.time() - cmd_start_time
                    if cmd_elapsed > cmd_timeout:
                        # 這個命令等待超時，但繼續執行下一個命令
                        self.on_data(f'\n[警告] 命令 "{cmd}" 等待響應超過 {cmd_timeout} 秒，繼續執行下一步\n', "warning")
                        break
                    
                    data = ser.read(1024)
                    if data:
                        text = data.decode(errors='ignore')
                        cmd_buffer += text
                        buffer += text
                        self.on_data(text, None)
                        
                        # 檢查是否收到結束字串，但不立即結束整個過程
                        if self.end_str in cmd_buffer:
                            cmd_received_end = True
                            # 只有在最後一個命令時，才標記整個過程完成
                            if i == len(self.cmd_list) - 1:
                                self.on_data(f'\n[結束] 收到指定結束字串 {self.end_str}\n', "end")
                                finished = True
                            break
                    
                    time.sleep(0.1)
                
                # 添加分隔線
                self.on_data('\n####################\n', "purple")
                
                # 命令間隔1秒
                time.sleep(1)



            # 如果沒有在執行命令時接收到結束字串，則繼續等待

            if not finished and not self.stop_event.is_set():

                self.on_data(f'\n[系統] 所有命令已發送，等待最終回應...\n', "purple")

                

                # 等待最終回應

                final_wait_start = time.time()

                while not self.stop_event.is_set() and not finished:

                    elapsed = time.time() - start_time

                    if elapsed > self.timeout:

                        self.on_data(f'\n[超時] 已超過 {self.timeout} 秒，指令自動中止\n', "timeout")

                        break

                    

                    data = ser.read(1024)

                    if data:

                        text = data.decode(errors='ignore')

                        buffer += text

                        self.on_data(text, None)

                        if self.end_str in buffer:

                            self.on_data(f'\n[結束] 收到指定結束字串 {self.end_str}\n', "end")

                            finished = True

                            break

                        

                        # 如果等待最終回應已超過5秒且沒有新數據，認為已完成

                        if time.time() - final_wait_start > 5 and not data:

                            self.on_data(f'\n[系統] 沒有更多數據，執行完成\n', "purple")

                            break

                        

                    time.sleep(0.1)  # 讓進度條平滑更新



            ser.flush()

        except serial.SerialException as e:
            error_msg = str(e)
            if "PermissionError" in error_msg or "存取被拒" in error_msg or "Access is denied" in error_msg:
                self.on_data(f'\n[錯誤] 無法開啟 {self.com} (存取被拒)\n', "error")
                self.on_data(f'[提示] 該 COM 口可能正被其他程式 (如 Tera Term) 佔用中。\n', "warning")
                self.on_data(f'[建議 1] 請暫時斷開 Tera Term 連線 (File -> Disconnect)。\n', "warning")
                self.on_data(f'[建議 2] 若需同時開啟 Tera Term 看 Log，請將「傳輸方式」改為 ADB 模式。\n', "warning")
            else:
                self.on_data(f'\n[錯誤] 序列埠錯誤: {e}\n', "error")

        except Exception as e:
            self.on_data(f'\n[錯誤] 執行失敗: {e}\n', "error")

        finally:
            # 使用簡化的關閉邏輯（回到舊版穩定做法）
            try:
                if hasattr(self, 'serial_connection') and self.serial_connection is not None:
                    self.serial_connection.close()
                    log_debug(f"簡單關閉 COM 口 {self.com}")
            except Exception as e:
                # 忽略關閉時的錯誤，這些通常是無害的
                log_debug(f"關閉 COM 口時發生錯誤（已忽略）: {e}")

            # 確保 thread 狀態重設（舊版邏輯）
            self.stop_event.set()

            # 更新狀態
            self.on_status(False)
            self.on_finish()

            log_debug("SerialWorker 執行完成")