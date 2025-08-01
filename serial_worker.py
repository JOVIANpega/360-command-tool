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
                 on_finish: Callable, stop_event: threading.Event):
        super().__init__()

        # 初始化核心組件
        self.error_handler = get_error_handler()
        self.async_manager = get_async_manager()

        # 序列埠參數
        self.com = com
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

        # 序列埠連接
        self.serial_connection: Optional[serial.Serial] = None

        # COM 口關閉鎖，防止重複關閉
        self._close_lock = threading.Lock()
        self._is_closed = False

        log_debug(f"SerialWorker 初始化: COM={com}, 指令數={len(cmd_list)}, 超時={timeout}s")

    def force_stop(self):
        """強制停止執行並關閉 COM 口"""
        try:
            # 設置停止事件
            self.stop_event.set()
            log_debug("SerialWorker 已設置停止事件")

            # 等待一小段時間讓主線程有機會正常關閉
            time.sleep(0.2)

            # 使用鎖來安全關閉 COM 口
            self._safe_close_serial()

            log_debug("SerialWorker 已強制停止")
            return True
        except Exception as e:
            log_error(f"強制停止時發生錯誤: {e}")
            return False

    def _safe_close_serial(self):
        """安全關閉序列埠連接，防止重複關閉"""
        with self._close_lock:
            if self._is_closed:
                log_debug(f"COM 口 {self.com} 已經關閉，跳過")
                return

            if self.serial_connection is not None:
                try:
                    # 檢查 serial_connection 是否仍然有效
                    if hasattr(self.serial_connection, 'is_open'):
                        if self.serial_connection.is_open:
                            # 先嘗試清空緩衝區
                            try:
                                if hasattr(self.serial_connection, 'reset_input_buffer'):
                                    self.serial_connection.reset_input_buffer()
                                if hasattr(self.serial_connection, 'reset_output_buffer'):
                                    self.serial_connection.reset_output_buffer()
                            except:
                                pass  # 忽略緩衝區清空錯誤

                            # 關閉連接
                            self.serial_connection.close()
                            log_debug(f"安全關閉 COM 口 {self.com}")
                        else:
                            log_debug(f"COM 口 {self.com} 已經關閉")
                    else:
                        log_debug(f"COM 口 {self.com} 連接對象無效")
                except (OSError, AttributeError, ValueError) as e:
                    # 特別處理各種關閉錯誤
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in ['控制代碼無效', 'invalid handle', 'handle is invalid', 'bad file descriptor']):
                        log_debug(f"COM 口 {self.com} 控制代碼已無效，跳過關閉")
                    else:
                        log_debug(f"關閉 COM 口時發生錯誤（已忽略）: {e}")
                except Exception as e:
                    # 忽略其他關閉時的錯誤，這些通常是無害的
                    log_debug(f"關閉 COM 口時發生錯誤（已忽略）: {e}")
                finally:
                    # 無論如何都要清理引用和設置狀態
                    try:
                        self.serial_connection = None
                    except:
                        pass
                    self._is_closed = True



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

                    

                    # 移除彈窗顯示，只在控制台顯示進度

                    

                    # 分段延遲，每秒更新一次進度

                    for i in range(delay_seconds):

                        if self.stop_event.is_set() or finished:

                            break

                        time.sleep(1)

                        progress = ((i + 1) / delay_seconds) * 100

                        self.on_progress(progress)

                        self.on_data(f'剩餘 {delay_seconds - i - 1} 秒...\r', "purple")

                    

                    self.on_data(f'\n[系統] 延遲結束\n', "purple")

                    

                    # 移除延遲結束通知彈窗

                    

                    continue

                

                # 處理特殊指令: SHOW

                show_match = re.match(r'^SHOW:(.+)$', cmd)

                if show_match:

                    message = show_match.group(1)

                    self.on_data(f'\n[系統] 顯示訊息: {message}\n', "purple")

                    

                    # 使用事件來協調主線程和工作線程

                    message_confirmed = threading.Event()

                    

                    # 如果設置了回調函數，則使用它來顯示消息框

                    if hasattr(self, 'show_message_callback') and self.show_message_callback:

                        # 在主線程中顯示消息框，並在用戶確認後設置事件

                        def confirm_callback():

                            # 標記訊息已確認

                            message_confirmed.set()

                            # 記錄確認訊息

                            self.on_data(f'\n[系統] 訊息已確認\n', "purple")

                            

                        # 顯示訊息並設置回調

                        self.show_message_callback(f"系統訊息: {message}", confirm_callback)

                        

                        # 等待最多3秒

                        wait_start = time.time()

                        while not message_confirmed.is_set() and not self.stop_event.is_set() and not finished:

                            time.sleep(0.1)

                            # 如果等待超過3秒，自動確認

                            if time.time() - wait_start > 3:

                                message_confirmed.set()

                                self.on_data(f'\n[系統] 訊息自動確認 (超時)\n', "purple")

                                break

                    else:

                        # 如果沒有設置回調函數，則只在控制台輸出消息

                        self.on_data(f'[警告] 無法顯示消息框，因為未設置回調函數\n', "error")

                    

                    continue

                

                # 正常指令處理

                self.on_data(f'\n[發送] {cmd}\n', "send")

                ser.write((cmd + '\r\n').encode())

                ser.flush()

                

                # 檢查每個命令的回應，但不立即結束

                cmd_start_time = time.time()

                cmd_buffer = ""

                cmd_received_end = False

                

                # 等待這個命令的響應，但不超過超時時間的一半

                cmd_timeout = min(self.timeout / 2, 10)  # 最多等待10秒或總超時的一半

                

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

        except Exception as e:

            self.on_data(f'\n[錯誤] {e}\n', "error")

        finally:
            # 使用安全關閉方法
            self._safe_close_serial()

            # 更新狀態
            self.on_status(False)
            self.on_finish()

            log_debug("SerialWorker 執行完成")