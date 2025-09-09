# -*- coding: utf-8 -*-
"""
性能監控模組
提供應用程式性能監控和優化建議
"""
import time
import threading
import psutil
import os
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque

from .error_handler import get_error_handler, safe_execute


@dataclass
class PerformanceMetrics:
    """性能指標"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read: int = 0
    disk_io_write: int = 0
    network_sent: int = 0
    network_recv: int = 0
    active_threads: int = 0
    open_files: int = 0


@dataclass
class FunctionProfile:
    """函數性能分析"""
    name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_call: Optional[float] = None
    errors: int = 0

    def add_call(self, execution_time: float):
        """添加函數調用記錄"""
        self.call_count += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.call_count
        self.last_call = time.time()

    def add_error(self):
        """添加錯誤記錄"""
        self.errors += 1


class PerformanceMonitor:
    """性能監控器"""
    
    def __init__(self, max_history: int = 1000, monitor_interval: float = 5.0):
        self.max_history = max_history
        self.monitor_interval = monitor_interval
        self.error_handler = get_error_handler()
        
        # 性能歷史記錄
        self._metrics_history: deque = deque(maxlen=max_history)
        self._function_profiles: Dict[str, FunctionProfile] = {}
        
        # 監控控制
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # 進程信息
        self._process = psutil.Process()
        
        # 警告閾值
        self.cpu_warning_threshold = 80.0  # CPU使用率警告閾值
        self.memory_warning_threshold = 80.0  # 記憶體使用率警告閾值
        self.response_time_warning = 1.0  # 響應時間警告閾值（秒）
        
        # 警告回調
        self._warning_callbacks: List[Callable] = []
    
    def start_monitoring(self):
        """開始性能監控"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        self.error_handler.log_info("性能監控已啟動")
    
    def stop_monitoring(self):
        """停止性能監控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        
        self.error_handler.log_info("性能監控已停止")
    
    @safe_execute(get_error_handler())
    def _monitor_loop(self):
        """監控循環"""
        while self._monitoring:
            try:
                metrics = self._collect_metrics()
                
                with self._lock:
                    self._metrics_history.append(metrics)
                
                # 檢查警告條件
                self._check_warnings(metrics)
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                self.error_handler.log_error("收集性能指標時發生錯誤", e)
                time.sleep(self.monitor_interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """收集性能指標"""
        try:
            # CPU和記憶體
            cpu_percent = self._process.cpu_percent()
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = self._process.memory_percent()
            
            # 磁碟I/O
            try:
                io_counters = self._process.io_counters()
                disk_io_read = io_counters.read_bytes
                disk_io_write = io_counters.write_bytes
            except (AttributeError, psutil.AccessDenied):
                disk_io_read = disk_io_write = 0
            
            # 網路I/O（系統級別）
            try:
                net_io = psutil.net_io_counters()
                network_sent = net_io.bytes_sent if net_io else 0
                network_recv = net_io.bytes_recv if net_io else 0
            except (AttributeError, psutil.AccessDenied):
                network_sent = network_recv = 0
            
            # 線程和文件
            active_threads = self._process.num_threads()
            try:
                open_files = len(self._process.open_files())
            except (AttributeError, psutil.AccessDenied):
                open_files = 0
            
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                disk_io_read=disk_io_read,
                disk_io_write=disk_io_write,
                network_sent=network_sent,
                network_recv=network_recv,
                active_threads=active_threads,
                open_files=open_files
            )
            
        except Exception as e:
            self.error_handler.log_error("收集性能指標失敗", e)
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0
            )
    
    def _check_warnings(self, metrics: PerformanceMetrics):
        """檢查警告條件"""
        warnings = []
        
        if metrics.cpu_percent > self.cpu_warning_threshold:
            warnings.append(f"CPU使用率過高: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > self.memory_warning_threshold:
            warnings.append(f"記憶體使用率過高: {metrics.memory_percent:.1f}%")
        
        if metrics.active_threads > 50:
            warnings.append(f"活動線程數過多: {metrics.active_threads}")
        
        if metrics.open_files > 100:
            warnings.append(f"打開文件數過多: {metrics.open_files}")
        
        # 觸發警告回調
        for warning in warnings:
            self.error_handler.log_warning(f"性能警告: {warning}")
            for callback in self._warning_callbacks:
                try:
                    callback(warning, metrics)
                except Exception as e:
                    self.error_handler.log_error("執行警告回調失敗", e)
    
    def profile_function(self, func_name: str = None):
        """函數性能分析裝飾器"""
        def decorator(func):
            nonlocal func_name
            if func_name is None:
                func_name = f"{func.__module__}.{func.__name__}"
            
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # 記錄性能數據
                    with self._lock:
                        if func_name not in self._function_profiles:
                            self._function_profiles[func_name] = FunctionProfile(func_name)
                        self._function_profiles[func_name].add_call(execution_time)
                    
                    # 檢查響應時間警告
                    if execution_time > self.response_time_warning:
                        self.error_handler.log_warning(
                            f"函數 {func_name} 執行時間過長: {execution_time:.3f}秒"
                        )
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    
                    # 記錄錯誤
                    with self._lock:
                        if func_name not in self._function_profiles:
                            self._function_profiles[func_name] = FunctionProfile(func_name)
                        self._function_profiles[func_name].add_call(execution_time)
                        self._function_profiles[func_name].add_error()
                    
                    raise
            
            return wrapper
        return decorator
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """獲取當前性能指標"""
        with self._lock:
            return self._metrics_history[-1] if self._metrics_history else None
    
    def get_metrics_history(self, minutes: int = 60) -> List[PerformanceMetrics]:
        """獲取指定時間範圍內的性能歷史"""
        cutoff_time = time.time() - (minutes * 60)
        
        with self._lock:
            return [
                metrics for metrics in self._metrics_history
                if metrics.timestamp >= cutoff_time
            ]
    
    def get_function_profiles(self) -> Dict[str, FunctionProfile]:
        """獲取函數性能分析結果"""
        with self._lock:
            return self._function_profiles.copy()
    
    def get_performance_summary(self) -> Dict[str, any]:
        """獲取性能摘要"""
        current = self.get_current_metrics()
        if not current:
            return {}
        
        recent_metrics = self.get_metrics_history(5)  # 最近5分鐘
        
        if recent_metrics:
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_mb for m in recent_metrics) / len(recent_metrics)
        else:
            avg_cpu = current.cpu_percent
            avg_memory = current.memory_mb
        
        # 找出最慢的函數
        slowest_functions = sorted(
            self._function_profiles.values(),
            key=lambda p: p.avg_time,
            reverse=True
        )[:5]
        
        return {
            'current_cpu': current.cpu_percent,
            'current_memory_mb': current.memory_mb,
            'current_memory_percent': current.memory_percent,
            'avg_cpu_5min': avg_cpu,
            'avg_memory_5min': avg_memory,
            'active_threads': current.active_threads,
            'open_files': current.open_files,
            'slowest_functions': [
                {
                    'name': p.name,
                    'avg_time': p.avg_time,
                    'call_count': p.call_count,
                    'errors': p.errors
                }
                for p in slowest_functions
            ]
        }
    
    def add_warning_callback(self, callback: Callable):
        """添加警告回調函數"""
        self._warning_callbacks.append(callback)
    
    def reset_profiles(self):
        """重置函數性能分析數據"""
        with self._lock:
            self._function_profiles.clear()
        self.error_handler.log_info("函數性能分析數據已重置")


# 全局性能監控器實例
_global_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """獲取全局性能監控器"""
    global _global_performance_monitor
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor()
    return _global_performance_monitor


# 便捷裝飾器
def profile(func_name: str = None):
    """性能分析裝飾器"""
    return get_performance_monitor().profile_function(func_name)
