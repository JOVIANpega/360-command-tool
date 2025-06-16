import serial
import threading
import time
import re
import tkinter as tk
from tkinter import messagebox

class SerialWorker(threading.Thread):
    def __init__(self, com, cmd_list, end_str, timeout, on_data, on_status, on_progress, on_finish, stop_event):
        super().__init__()
        self.com = com
        self.cmd_list = cmd_list
        self.end_str = end_str
        self.timeout = timeout
        self.on_data = on_data
        self.on_status = on_status
        self.on_progress = on_progress
        self.on_finish = on_finish
        self.stop_event = stop_event
        self.daemon = True
        # 用於顯示訊息的回調函數，將在初始化時由外部設置
        self.show_message_callback = None

    def run(self):
        start_time = time.time()
        try:
            ser = serial.Serial(self.com, 115200, timeout=0.1)
            self.on_status(True)
            buffer = ""
            finished = False

            # 執行所有指令
            for i, cmd in enumerate(self.cmd_list):
                if self.stop_event.is_set():
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
                    for i in range(delay_seconds):
                        if self.stop_event.is_set():
                            break
                        time.sleep(1)
                        progress = ((i + 1) / delay_seconds) * 100
                        self.on_progress(progress)
                        self.on_data(f'剩餘 {delay_seconds - i - 1} 秒...\r', "purple")
                    
                    self.on_data(f'\n[系統] 延遲結束\n', "purple")
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
                        self.show_message_callback(message, lambda: message_confirmed.set())
                        
                        # 等待用戶確認或停止事件
                        while not message_confirmed.is_set() and not self.stop_event.is_set():
                            time.sleep(0.1)
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
                
                while not self.stop_event.is_set():
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
                while not self.stop_event.is_set():
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
            self.stop_event.set()  # 確保 thread 狀態重設
            self.on_status(False)
            self.on_finish()