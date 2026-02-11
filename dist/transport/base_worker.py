# -*- coding: utf-8 -*-
"""
傳輸層基礎類別 (BaseWorker)
提供所有傳輸模式的共用功能
"""
import threading
import time
import re
from abc import ABC, abstractmethod
from typing import List, Callable, Optional, Tuple

# 導入核心模組
from core import (
    get_error_handler, get_async_manager, safe_execute,
    log_debug, log_info, log_error, profile
)


class BaseWorker(threading.Thread, ABC):
    """
    傳輸層基礎類別
    
    提供所有傳輸模式的共用功能：
    - 特殊指令處理 (DELAY, SHOW)
    - 進度管理
    - 錯誤處理
    - 回調管理
    
    子類需要實現：
    - connect() - 建立連線
    - execute_command() - 執行單個指令
    - disconnect() - 關閉連線
    """
    
    def __init__(self, 
                 cmd_list: List[str], 
                 end_str: str, 
                 timeout: float,
                 on_data: Callable, 
                 on_status: Callable, 
                 on_progress: Callable,
                 on_finish: Callable, 
                 stop_event: threading.Event, 
                 cmd_timeout: float = 10.0):
        """
        初始化基礎工作器
        
        Args:
            cmd_list: 要執行的指令列表
            end_str: 結束字串
            timeout: 總超時時間（秒）
            on_data: 資料回調函數 (text, tag)
            on_status: 狀態回調函數 (connected)
            on_progress: 進度回調函數 (progress)
            on_finish: 完成回調函數
            stop_event: 停止事件
            cmd_timeout: 單個指令超時時間（秒）
        """
        super().__init__(daemon=True)
        
        # 初始化核心組件
        self.error_handler = get_error_handler()
        self.async_manager = get_async_manager()
        
        # 指令參數
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
        
        # 用於顯示訊息的回調函數
        self.show_message_callback: Optional[Callable] = None
        
        log_debug(f"{self.__class__.__name__} 初始化: 指令數={len(cmd_list)}, 超時={timeout}s")
    
    # ==================== 抽象方法 (子類必須實現) ====================
    
    @abstractmethod
    def connect(self) -> bool:
        """
        建立連線
        
        Returns:
            bool: 連線成功返回 True，失敗返回 False
        """
        pass
    
    @abstractmethod
    def execute_command(self, cmd: str) -> Tuple[int, str, str]:
        """
        執行單個指令
        
        Args:
            cmd: 要執行的指令
            
        Returns:
            Tuple[int, str, str]: (返回碼, 標準輸出, 標準錯誤)
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """關閉連線"""
        pass
    
    @abstractmethod
    def get_transport_name(self) -> str:
        """
        獲取傳輸方式名稱
        
        Returns:
            str: 傳輸方式名稱 (如 "Console", "ADB", "SSH")
        """
        pass
    
    # ==================== 共用方法 ====================
    
    def _handle_special_command(self, cmd: str, index: int) -> bool:
        """
        處理特殊指令 (DELAY, SHOW)
        
        Args:
            cmd: 指令字串
            index: 指令索引
            
        Returns:
            bool: 如果是特殊指令返回 True，否則返回 False
        """
        # 處理 DELAY 指令
        if self._handle_delay_command(cmd):
            return True
        
        # 處理 SHOW 指令
        if self._handle_show_command(cmd):
            return True
        
        return False
    
    def _handle_delay_command(self, cmd: str) -> bool:
        """
        處理 DELAY 指令
        
        支援格式：
        - DELAY:5 (延遲 5 秒)
        - DELAY 5 (延遲 5 秒)
        
        Args:
            cmd: 指令字串
            
        Returns:
            bool: 如果是 DELAY 指令返回 True
        """
        delay_match = re.match(r'^DELAY[:\s]+(\d+)$', cmd.strip(), re.IGNORECASE)
        if delay_match:
            delay_seconds = int(delay_match.group(1))
            self.on_data(f'\n[系統] 延遲 {delay_seconds} 秒...\n', "purple")
            
            for j in range(delay_seconds):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
                progress = ((j + 1) / delay_seconds) * 100
                self.on_progress(progress)
                self.on_data(f'剩餘 {delay_seconds - j - 1} 秒...\r', "purple")
            
            self.on_data(f'\n[系統] 延遲結束\n', "purple")
            return True
        
        return False
    
    def _handle_show_command(self, cmd: str) -> bool:
        """
        處理 SHOW 指令
        
        支援格式：
        - SHOW:訊息內容
        - SHOW 訊息內容
        
        Args:
            cmd: 指令字串
            
        Returns:
            bool: 如果是 SHOW 指令返回 True
        """
        show_match = re.match(r'^SHOW[:\s]+(.+)$', cmd.strip(), re.IGNORECASE)
        if show_match:
            message = show_match.group(1)
            self.on_data(f'\n[系統] 顯示訊息: {message}\n', "purple")
            
            # 如果有設定顯示訊息的回調函數，則呼叫
            if self.show_message_callback:
                try:
                    self.show_message_callback(message)
                except Exception as e:
                    log_error(f"顯示訊息時發生錯誤: {e}")
            
            return True
        
        return False
    
    def _execute_normal_command(self, cmd: str, index: int):
        """
        執行正常指令的通用流程
        
        Args:
            cmd: 指令字串
            index: 指令索引
        """
        # 處理指令格式 (支持 tuple 或 string)
        if isinstance(cmd, tuple):
            cmd_name, cmd_str = cmd
        else:
            cmd_name, cmd_str = "", cmd
        
        cmd_str = str(cmd_str).strip()
        if not cmd_str:
            return
        
        # 格式化輸出：顯示序號和指令
        transport_name = self.get_transport_name()
        if cmd_name:
            header = f"{index+1:02d}  發送指令 {cmd_name}={cmd_str}"
        else:
            header = f"{index+1:02d}  發送指令 {cmd_str}"
        
        self.on_data(f'\n{header}\n', "purple")
        self.on_data(f'[{transport_name} 發送] {cmd_str}\n', "send")
        
        # 執行指令
        returncode, stdout, stderr = self.execute_command(cmd_str)
        
        # 處理執行結果
        # 注意：serial_worker 已經在 execute_command 中即時輸出 stdout
        # 所以這裡不需要再輸出 stdout，只處理錯誤和結束字串檢查
        if returncode == 0:
            # 檢查是否收到結束字串
            if self.end_str and stdout and self.end_str in stdout:
                if index == len(self.cmd_list) - 1:
                    self.on_data(f'\n[結束] 收到指定結束字串 {self.end_str}\n', "end")
                    return True  # 標記完成
        else:
            # 指令執行失敗
            if stderr:
                self.on_data(f'\n[錯誤] {stderr}\n', "error")
            else:
                self.on_data(f'\n[錯誤] 指令執行失敗 (返回碼: {returncode})\n', "error")
        
        # 添加分隔線
        self.on_data('\n####################\n', "purple")
        
        # 更新進度
        progress = ((index + 1) / len(self.cmd_list)) * 100
        self.on_progress(progress)
        
        return False  # 未完成
    
    # ==================== 主執行方法 (模板方法) ====================
    
    @profile("BaseWorker.run")
    def run(self):
        """
        主執行方法 (模板方法模式)
        
        定義執行流程：
        1. 建立連線
        2. 執行所有指令
        3. 關閉連線
        """
        start_time = time.time()
        transport_name = self.get_transport_name()
        log_info(f"開始執行 {transport_name} 任務")
        
        try:
            # 步驟 1: 建立連線
            if not self.connect():
                self.on_data(f"\n[錯誤] {transport_name} 連線失敗\n", "error")
                return
            
            self.on_status(True)
            finished = False
            
            # 步驟 2: 執行所有指令
            for i, cmd in enumerate(self.cmd_list):
                if self.stop_event.is_set() or finished:
                    break
                
                # 處理特殊指令
                if self._handle_special_command(cmd, i):
                    continue
                
                # 執行正常指令
                if self._execute_normal_command(cmd, i):
                    finished = True
                    break
                
                # 指令間隔
                if i < len(self.cmd_list) - 1:  # 不是最後一個指令
                    time.sleep(1)
            
            # 步驟 3: 如果沒有收到結束字串，繼續等待最終回應
            if not finished and not self.stop_event.is_set():
                self.on_data(f'\n[{transport_name}] 所有指令已發送，等待最終回應...\n', "purple")
                
                # 如果子類有 wait_for_final_response 方法，則調用它
                if hasattr(self, 'wait_for_final_response'):
                    finished = self.wait_for_final_response(start_time)
                    if finished:
                        # 已收到結束字串
                        pass
                    else:
                        # 總超時
                        elapsed = time.time() - start_time
                        if elapsed > self.timeout:
                            self.on_data(f'\n[{transport_name}] 總超時 ({self.timeout}秒)，結束執行\n', "warning")
                else:
                    # 沒有 wait_for_final_response 方法，使用簡單等待
                    while not self.stop_event.is_set() and not finished:
                        elapsed = time.time() - start_time
                        if elapsed > self.timeout:
                            self.on_data(f'\n[{transport_name}] 總超時 ({self.timeout}秒)，結束執行\n', "warning")
                            break
                        time.sleep(0.5)
                
                # 如果仍未完成，顯示完成訊息
                if not finished:
                    self.on_data(f'\n[{transport_name}] 所有指令已執行完成\n', "purple")
            
        except Exception as e:
            self.on_data(f'\n[錯誤] {transport_name} 執行時發生錯誤: {e}\n', "error")
            log_error(f"{transport_name} 執行錯誤: {e}")
        
        finally:
            # 步驟 4: 清理
            try:
                self.disconnect()
            except Exception as e:
                log_error(f"{transport_name} 斷線時發生錯誤: {e}")
            
            # 更新狀態
            self.on_status(False)
            self.on_finish()
            
            elapsed = time.time() - start_time
            log_debug(f"{transport_name}Worker 執行完成，耗時 {elapsed:.2f}s")
    
    def set_show_message_callback(self, callback: Callable):
        """設置顯示消息框的回調函數"""
        self.show_message_callback = callback
