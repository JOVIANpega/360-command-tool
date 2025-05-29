import serial
import threading
import time

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