# -*- coding: utf-8 -*-
"""
統一錯誤處理和日誌系統
提供一致的錯誤處理、日誌記錄和用戶通知功能
"""
import os
import sys
import logging
import traceback
from datetime import datetime
from typing import Optional, Any, Dict
from functools import wraps
import threading
from tkinter import messagebox


class ErrorHandler:
    """統一錯誤處理器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.logger = None
        self._setup_logging()
        self._lock = threading.Lock()
    
    def _setup_logging(self):
        """設置日誌系統"""
        try:
            # 確保日誌目錄存在
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
            
            # 創建日誌器
            self.logger = logging.getLogger('VALO360')
            self.logger.setLevel(logging.DEBUG)
            
            # 避免重複添加處理器
            if not self.logger.handlers:
                # 文件處理器 - 詳細日誌
                today = datetime.now().strftime('%Y%m%d')
                log_file = os.path.join(self.log_dir, f'app_{today}.log')
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                
                # 控制台處理器 - 重要訊息
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)
                
                # 格式化器
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                file_handler.setFormatter(formatter)
                console_handler.setFormatter(formatter)
                
                self.logger.addHandler(file_handler)
                self.logger.addHandler(console_handler)
                
        except Exception as e:
            print(f"[ERROR] 設置日誌系統失敗: {e}")
    
    def log_debug(self, message: str, context: Optional[Dict] = None):
        """記錄調試訊息"""
        with self._lock:
            if context:
                message = f"{message} | Context: {context}"
            if self.logger:
                self.logger.debug(message)
            else:
                print(f"[DEBUG] {message}")
    
    def log_info(self, message: str, context: Optional[Dict] = None):
        """記錄資訊訊息"""
        with self._lock:
            if context:
                message = f"{message} | Context: {context}"
            if self.logger:
                self.logger.info(message)
            else:
                print(f"[INFO] {message}")
    
    def log_warning(self, message: str, context: Optional[Dict] = None):
        """記錄警告訊息"""
        with self._lock:
            if context:
                message = f"{message} | Context: {context}"
            if self.logger:
                self.logger.warning(message)
            else:
                print(f"[WARNING] {message}")
    
    def log_error(self, message: str, exception: Optional[Exception] = None, 
                  context: Optional[Dict] = None, show_user: bool = False):
        """記錄錯誤訊息"""
        with self._lock:
            full_message = message
            if context:
                full_message += f" | Context: {context}"
            if exception:
                full_message += f" | Exception: {str(exception)}"
                full_message += f" | Traceback: {traceback.format_exc()}"
            
            if self.logger:
                self.logger.error(full_message)
            else:
                print(f"[ERROR] {full_message}")
            
            # 如果需要顯示給用戶
            if show_user:
                try:
                    messagebox.showerror('錯誤', message)
                except Exception:
                    pass  # 如果無法顯示對話框，不要再次拋出異常
    
    def handle_exception(self, func_name: str, exception: Exception, 
                        context: Optional[Dict] = None, show_user: bool = False):
        """統一處理異常"""
        error_msg = f"函數 {func_name} 發生錯誤"
        self.log_error(error_msg, exception, context, show_user)


def safe_execute(error_handler: ErrorHandler, show_user_error: bool = False):
    """裝飾器：安全執行函數，自動處理異常"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_exception(
                    func.__name__, e, 
                    {'args': str(args)[:100], 'kwargs': str(kwargs)[:100]},
                    show_user_error
                )
                return None
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """裝飾器：失敗時重試"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(delay)
                    else:
                        raise last_exception
            return None
        return wrapper
    return decorator


# 全局錯誤處理器實例
_global_error_handler = None

def get_error_handler() -> ErrorHandler:
    """獲取全局錯誤處理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


# 便捷函數
def log_debug(message: str, context: Optional[Dict] = None):
    get_error_handler().log_debug(message, context)

def log_info(message: str, context: Optional[Dict] = None):
    get_error_handler().log_info(message, context)

def log_warning(message: str, context: Optional[Dict] = None):
    get_error_handler().log_warning(message, context)

def log_error(message: str, exception: Optional[Exception] = None, 
              context: Optional[Dict] = None, show_user: bool = False):
    get_error_handler().log_error(message, exception, context, show_user)
