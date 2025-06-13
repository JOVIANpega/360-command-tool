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
            for cmd in self.cmd_list:
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
                time.sleep(1)  # 指令間隔1秒

            # 等待回應
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
                time.sleep(0.1)  # 讓進度條平滑更新

            ser.flush()
        except Exception as e:
            self.on_data(f'\n[錯誤] {e}\n', "error")
        finally:
            self.stop_event.set()  # 確保 thread 狀態重設
            self.on_status(False)
            self.on_finish()