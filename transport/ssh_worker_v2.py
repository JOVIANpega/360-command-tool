# -*- coding: utf-8 -*-
"""
SSH 工作器 - 重構版本 (繼承 BaseWorker)
只實現 SSH 特定邏輯，共用邏輯由 BaseWorker 提供
"""
import threading
import time
import sys
import os
from typing import Tuple, Optional

# 延遲導入 paramiko - 只在實際需要 SSH 時才載入
# 這樣可以避免打包後因 cryptography 問題導致整個程式崩潰
paramiko = None

def _ensure_paramiko():
    """確保 paramiko 已載入"""
    global paramiko
    if paramiko is None:
        try:
            import paramiko as _pm
            paramiko = _pm
        except ImportError as e:
            raise ImportError(f"SSH 功能需要 paramiko 模組，請安裝: pip install paramiko\n錯誤: {e}")

# 添加 transport 目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from transport.base_worker import BaseWorker

# 導入核心模組
from core import log_debug, log_info, log_error, log_warning


# 全域持久連線狀態（與原版相同）
_persist_lock = threading.Lock()
_persist_client = None  # Remove explicit type hint to avoid NoneType error
_persist_connected: bool = False
_persist_last_used: float = 0.0
_persist_idle_timeout_sec: int = 600  # 閒置 10 分鐘自動斷線
_idle_monitor_started = False


def _start_idle_monitor():
    """啟動閒置監控（與原版相同）"""
    global _idle_monitor_started
    if _idle_monitor_started:
        return

    def _monitor():
        global _persist_client, _persist_connected, _persist_last_used
        while True:
            try:
                time.sleep(5)
                with _persist_lock:
                    if _persist_client and _persist_connected:
                        idle = time.time() - _persist_last_used
                        if idle >= _persist_idle_timeout_sec:
                            try:
                                _persist_client.close()
                            except Exception:
                                pass
                            _persist_client = None
                            _persist_connected = False
                            log_info("持久 SSH 連線因閒置超時已自動關閉")
            except Exception:
                pass

    t = threading.Thread(target=_monitor, daemon=True)
    t.start()
    _idle_monitor_started = True


def force_disconnect_persistent_session():
    """提供外部呼叫的 API：強制關閉持久 SSH 連線"""
    global _persist_client, _persist_connected
    with _persist_lock:
        if _persist_client:
            try:
                _persist_client.close()
            except Exception:
                pass
        _persist_client = None
        _persist_connected = False
        log_info("已手動關閉持久 SSH 連線")


class SSHWorkerV2(BaseWorker):
    """
    SSH 工作器 - 重構版本
    
    只實現 SSH 特定的邏輯：
    - SSH 連線管理
    - SSH 指令執行
    - 持久連線功能
    
    所有共用邏輯 (DELAY, SHOW, 進度管理等) 都由 BaseWorker 提供
    """
    
    def __init__(self, cmd_list, end_str: str, timeout: int,
                 host: str, port: int, username: str, password: str,
                 on_data, on_status, on_progress, on_finish, stop_event, cmd_timeout: float = 30.0):
        """
        初始化 SSH 工作器
        
        Args:
            host: SSH 主機地址
            port: SSH 埠號
            username: 使用者名稱
            password: 密碼
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
        
        # SSH 特定參數
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
        # SSH 連線
        self.ssh_client = None
        self.connected = False
        self.use_persistent = True  # 預設保持連線模式
        
        log_debug(f"SSHWorkerV2 初始化: 主機={host}:{port}, 使用者={username}")
    
    # ==================== 實現抽象方法 ====================
    
    def connect(self) -> bool:
        """
        建立 SSH 連線
        
        Returns:
            bool: 連線成功返回 True，失敗返回 False
        """
        try:
            # 確保 paramiko 已載入
            _ensure_paramiko()
            
            global _persist_client, _persist_connected, _persist_last_used
            log_info(f"正在連線到 SSH 主機 {self.host}:{self.port}")
            
            # 嘗試重用持久連線
            _start_idle_monitor()
            if self.use_persistent:
                with _persist_lock:
                    if _persist_client and _persist_connected:
                        # 驗證傳輸是否仍可用
                        transport = _persist_client.get_transport()
                        if transport and transport.is_active():
                            self.ssh_client = _persist_client
                            self.connected = True
                            _persist_last_used = time.time()
                            log_info("重用持久 SSH 連線")
                            return True
                        else:
                            # 清理失效的持久連線
                            try:
                                _persist_client.close()
                            except Exception:
                                pass
                            _persist_client = None
                            _persist_connected = False
            
            # 建立新的 SSH 客戶端
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 連線參數 - 針對 Dropbear SSH 優化
            connect_kwargs = {
                "hostname": self.host,
                "port": self.port,
                "username": self.username,
                "timeout": 30,
                "auth_timeout": 30,
                "banner_timeout": 30,
                "look_for_keys": False,
                "allow_agent": False,
                "gss_auth": False,
                "gss_kex": False,
                "disabled_algorithms": {'keys': ['rsa-sha2-256', 'rsa-sha2-512']},
                "sock": None,
            }

            # 退避重試（處理 banner 讀取/認證暫時失敗）
            backoffs = [2, 5, 10]
            last_error: Optional[Exception] = None

            for attempt, delay in enumerate(backoffs, start=1):
                time.sleep(delay)
                self.on_data(f"[提示] 裝置忙碌，{delay}s 後自動重試 (第{attempt}/3次)\n", "warning")

                try:
                    # 先嘗試不帶任何認證參數的連線
                    self.ssh_client.connect(**connect_kwargs)
                    self.connected = True
                except Exception as first_error:
                    last_error = first_error
                    log_debug(f"第一次連線嘗試失敗: {first_error}")

                    # 第二層：嘗試帶密碼（允許空密碼）
                    try:
                        connect_kwargs["password"] = self.password
                        self.ssh_client.connect(**connect_kwargs)
                        self.connected = True
                    except Exception as second_error:
                        last_error = second_error
                        log_debug(f"第二次連線嘗試失敗: {second_error}")

                        # 第三層：強制使用 none 認證
                        try:
                            self.ssh_client.close()
                            self.ssh_client = paramiko.SSHClient()
                            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                            transport = paramiko.Transport((self.host, self.port))
                            transport.start_client(timeout=30)
                            transport.auth_none(self.username)

                            self.ssh_client._transport = transport
                            self.connected = True
                            log_info("使用 none 認證成功")
                        except Exception as third_error:
                            last_error = third_error
                            log_debug(f"第三次連線嘗試失敗: {third_error}")

                # 若已連線成功，跳出重試
                if self.connected:
                    break

                # 判斷是否繼續重試
                err_text = str(last_error) if last_error else ""
                transient = (
                    "Error reading SSH protocol banner" in err_text or
                    "WinError 10054" in err_text or
                    "Authentication failed" in err_text or
                    "No authentication methods available" in err_text
                )
                if attempt < len(backoffs) and transient:
                    continue
                else:
                    break

            if not self.connected:
                if last_error:
                    raise last_error
                raise Exception("無法建立 SSH 連線")
            
            log_info(f"SSH 連線成功: {self.username}@{self.host}:{self.port}")
            
            # 設定 Keep-Alive
            transport = self.ssh_client.get_transport()
            if transport:
                transport.set_keepalive(30)
                log_debug("已設定 SSH Keep-Alive (30秒)")
            
            # 建立/更新持久連線
            if self.use_persistent:
                with _persist_lock:
                    _persist_client = self.ssh_client
                    _persist_connected = True
                    _persist_last_used = time.time()
                    log_debug("已建立持久 SSH 連線")
            
            return True
            
        except Exception as e:
            log_error(f"SSH 連線失敗: {e}")
            self.connected = False
            
            error_msg = f"SSH 連線失敗\n\n主機: {self.host}:{self.port}\n使用者: {self.username}\n\n錯誤: {str(e)}"
            self.on_data(f"\n[錯誤] {error_msg}\n", "error")
            
            return False
    
    def execute_command(self, cmd: str) -> Tuple[int, str, str]:
        """
        執行 SSH 指令
        
        Args:
            cmd: 要執行的指令
            
        Returns:
            Tuple[int, str, str]: (返回碼, 標準輸出, 標準錯誤)
        """
        try:
            if not self.connected or not self.ssh_client:
                return -1, "", "SSH 未連線"
            
            log_debug(f"執行 SSH 指令: {cmd}")
            
            # 背景執行支援
            stripped = cmd.strip()
            is_background = stripped.endswith('&')
            if is_background:
                base_cmd = stripped[:-1].strip()
                if not base_cmd:
                    return -1, "", "背景指令為空"
                escaped_base = base_cmd.replace("'", "'\"'\"'")
                ts = int(time.time())
                log_file = f"/tmp/pega_bg_{ts}.log"
                pid_file = f"/tmp/pega_bg_{ts}.pid"
                wrapped_command = (
                    "bash -l -c "
                    f"'{{ {escaped_base} >> {log_file} 2>&1 & pid=$!; echo PEGA_BG_STARTED:$pid; echo $pid > {pid_file}; echo PEGA_BG_LOG:{log_file}; }}' 2>&1 "
                    "|| "
                    "sh -l -c "
                    f"'{{ {escaped_base} >> {log_file} 2>&1 & pid=$!; echo PEGA_BG_STARTED:$pid; echo $pid > {pid_file}; echo PEGA_BG_LOG:{log_file}; }}' 2>&1"
                )
            else:
                # 使用登入 shell 執行指令
                escaped_command = cmd.replace("'", "'\"'\"'")
                wrapped_command = f"bash -l -c '{escaped_command}' 2>&1 || sh -l -c '{escaped_command}' 2>&1"
            
            log_debug(f"包裝後的指令: {wrapped_command}")
            
            # 執行指令
            stdin, stdout, stderr = self.ssh_client.exec_command(wrapped_command, timeout=self.cmd_timeout)
            
            # 讀取輸出
            stdout_data = stdout.read().decode("utf-8", errors="ignore")
            stderr_data = stderr.read().decode("utf-8", errors="ignore")
            return_code = stdout.channel.recv_exit_status()
            
            # 即時輸出結果
            if stdout_data:
                self.on_data(stdout_data, None)
            
            # 更新持久連線使用時間
            if self.use_persistent:
                with _persist_lock:
                    global _persist_last_used
                    _persist_last_used = time.time()
            
            return return_code, stdout_data, stderr_data
            
        except Exception as e:
            error_str = str(e)
            # 檢查是否為超時錯誤
            if "timed out" in error_str.lower() or "timeout" in error_str.lower():
                # 超時：顯示警告，但繼續執行（返回成功）
                self.on_data(f'\n[警告] 命令 "{cmd}" 等待響應超過 {self.cmd_timeout} 秒，繼續執行下一步\n', "warning")
                return 0, "", ""  # 返回成功，讓流程繼續
            else:
                log_error(f"執行 SSH 指令失敗: {e}")
                return -1, "", error_str
    
    def disconnect(self):
        """關閉 SSH 連線"""
        # 持久連線模式下，保持連線不關閉
        if self.use_persistent and self.ssh_client:
            with _persist_lock:
                global _persist_last_used
                _persist_last_used = time.time()
            log_debug("保持 SSH 持久連線")
        else:
            # 短連線模式：正常關閉
            if self.ssh_client:
                try:
                    self.ssh_client.close()
                    log_debug("SSH 連線已關閉")
                except Exception:
                    pass
            self.connected = False
    
    def get_transport_name(self) -> str:
        """獲取傳輸方式名稱"""
        return "SSH"
