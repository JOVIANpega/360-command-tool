# -*- coding: utf-8 -*-
"""
異步處理管理器
提供非阻塞的序列埠通訊和長時間運行任務的管理
"""
import threading
import queue
import time
from typing import Callable, Any, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
from enum import Enum

from .error_handler import get_error_handler, safe_execute


class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """任務資料結構"""
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    callback: Optional[Callable] = None
    error_callback: Optional[Callable] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class AsyncManager:
    """異步處理管理器"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.error_handler = get_error_handler()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: Dict[str, Task] = {}
        self._task_counter = 0
        self._lock = threading.RLock()
        self._shutdown = False
        
        # 結果隊列，用於主線程獲取結果
        self._result_queue = queue.Queue()
        
        # 啟動結果處理線程
        self._result_thread = threading.Thread(target=self._process_results, daemon=True)
        self._result_thread.start()
    
    def submit_task(self, func: Callable, *args, 
                   callback: Optional[Callable] = None,
                   error_callback: Optional[Callable] = None,
                   task_id: Optional[str] = None, **kwargs) -> str:
        """提交異步任務"""
        with self._lock:
            if self._shutdown:
                raise RuntimeError("AsyncManager 已關閉")
            
            # 生成任務ID
            if task_id is None:
                self._task_counter += 1
                task_id = f"task_{self._task_counter}"
            
            # 創建任務
            task = Task(
                id=task_id,
                func=func,
                args=args,
                kwargs=kwargs,
                callback=callback,
                error_callback=error_callback
            )
            
            self._tasks[task_id] = task
            
            # 提交到線程池
            future = self._executor.submit(self._execute_task, task)
            
            self.error_handler.log_debug(f"提交任務: {task_id}")
            return task_id
    
    @safe_execute(get_error_handler())
    def _execute_task(self, task: Task):
        """執行任務"""
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = time.time()
            
            self.error_handler.log_debug(f"開始執行任務: {task.id}")
            
            # 執行任務函數
            result = task.func(*task.args, **task.kwargs)
            
            # 更新任務狀態
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            
            # 將結果放入隊列
            self._result_queue.put(('completed', task))
            
            self.error_handler.log_debug(f"任務完成: {task.id}")
            
        except Exception as e:
            task.error = e
            task.status = TaskStatus.FAILED
            task.completed_at = time.time()
            
            self.error_handler.log_error(f"任務執行失敗: {task.id}", e)
            
            # 將錯誤放入隊列
            self._result_queue.put(('failed', task))
    
    def _process_results(self):
        """處理任務結果"""
        while not self._shutdown:
            try:
                # 等待結果
                result_type, task = self._result_queue.get(timeout=1.0)
                
                if result_type == 'completed' and task.callback:
                    try:
                        task.callback(task.result)
                    except Exception as e:
                        self.error_handler.log_error(f"執行回調函數失敗: {task.id}", e)
                
                elif result_type == 'failed' and task.error_callback:
                    try:
                        task.error_callback(task.error)
                    except Exception as e:
                        self.error_handler.log_error(f"執行錯誤回調函數失敗: {task.id}", e)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.error_handler.log_error("處理任務結果時發生錯誤", e)
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """獲取任務狀態"""
        with self._lock:
            task = self._tasks.get(task_id)
            return task.status if task else None
    
    def get_task_result(self, task_id: str) -> Any:
        """獲取任務結果"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status == TaskStatus.COMPLETED:
                return task.result
            elif task and task.status == TaskStatus.FAILED:
                raise task.error
            else:
                return None
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任務"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                return True
            return False
    
    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> bool:
        """等待任務完成"""
        start_time = time.time()
        
        while True:
            status = self.get_task_status(task_id)
            
            if status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                return True
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            time.sleep(0.1)
    
    def get_active_tasks(self) -> Dict[str, TaskStatus]:
        """獲取活動任務列表"""
        with self._lock:
            return {
                task_id: task.status 
                for task_id, task in self._tasks.items()
                if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
            }
    
    def cleanup_completed_tasks(self, max_age_seconds: float = 3600):
        """清理已完成的舊任務"""
        with self._lock:
            current_time = time.time()
            tasks_to_remove = []
            
            for task_id, task in self._tasks.items():
                if (task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED) 
                    and task.completed_at 
                    and (current_time - task.completed_at) > max_age_seconds):
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self._tasks[task_id]
            
            if tasks_to_remove:
                self.error_handler.log_debug(f"清理了 {len(tasks_to_remove)} 個舊任務")
    
    def shutdown(self, wait: bool = True):
        """關閉異步管理器"""
        self._shutdown = True
        
        if wait:
            # 等待所有任務完成
            self._executor.shutdown(wait=True)
        else:
            # 立即關閉
            self._executor.shutdown(wait=False)
        
        self.error_handler.log_info("AsyncManager 已關閉")


# 全局異步管理器實例
_global_async_manager = None

def get_async_manager() -> AsyncManager:
    """獲取全局異步管理器"""
    global _global_async_manager
    if _global_async_manager is None:
        _global_async_manager = AsyncManager()
    return _global_async_manager


# 便捷函數
def run_async(func: Callable, *args, 
              callback: Optional[Callable] = None,
              error_callback: Optional[Callable] = None, **kwargs) -> str:
    """異步執行函數"""
    return get_async_manager().submit_task(func, *args, 
                                         callback=callback,
                                         error_callback=error_callback, **kwargs)


def wait_for_result(task_id: str, timeout: Optional[float] = None) -> Any:
    """等待並獲取任務結果"""
    manager = get_async_manager()
    if manager.wait_for_task(task_id, timeout):
        return manager.get_task_result(task_id)
    else:
        raise TimeoutError(f"任務 {task_id} 超時")
