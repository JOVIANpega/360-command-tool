# -*- coding: utf-8 -*-
"""
資源管理器
提供統一的資源存取、快取和生命週期管理
"""
import os
import sys
import threading
import weakref
from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime, timedelta
import json

from .error_handler import get_error_handler, safe_execute


class ResourceCache:
    """資源快取管理器"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache = {}
        self._access_times = {}
        self._lock = threading.RLock()
        self.error_handler = get_error_handler()
    
    def get(self, key: str) -> Optional[Any]:
        """獲取快取項目"""
        with self._lock:
            if key not in self._cache:
                return None
            
            # 檢查是否過期
            if self._is_expired(key):
                self._remove(key)
                return None
            
            # 更新存取時間
            self._access_times[key] = datetime.now()
            return self._cache[key]
    
    def set(self, key: str, value: Any):
        """設置快取項目"""
        with self._lock:
            # 如果快取已滿，移除最舊的項目
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_oldest()
            
            self._cache[key] = value
            self._access_times[key] = datetime.now()
    
    def remove(self, key: str):
        """移除快取項目"""
        with self._lock:
            self._remove(key)
    
    def clear(self):
        """清空快取"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    def _is_expired(self, key: str) -> bool:
        """檢查項目是否過期"""
        if key not in self._access_times:
            return True
        return datetime.now() - self._access_times[key] > self.ttl
    
    def _remove(self, key: str):
        """內部移除方法"""
        self._cache.pop(key, None)
        self._access_times.pop(key, None)
    
    def _evict_oldest(self):
        """移除最舊的項目"""
        if not self._access_times:
            return
        
        oldest_key = min(self._access_times.keys(), 
                        key=lambda k: self._access_times[k])
        self._remove(oldest_key)


class ResourceManager:
    """統一資源管理器"""
    
    def __init__(self):
        self.error_handler = get_error_handler()
        self._file_cache = ResourceCache(max_size=50, ttl_seconds=300)
        self._command_cache = ResourceCache(max_size=20, ttl_seconds=600)
        self._resource_locks = {}
        self._lock = threading.RLock()
        
        # 資源清理註冊
        self._cleanup_callbacks = []
        
    def get_resource_path(self, relative_path: str) -> str:
        """獲取資源的絕對路徑，支持開發環境和打包後的環境"""
        cache_key = f"path_{relative_path}"
        cached_path = self._file_cache.get(cache_key)
        
        if cached_path and os.path.exists(cached_path):
            return cached_path
        
        try:
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.abspath(".")
            
            # 處理特殊文件路徑
            resolved_path = self._resolve_special_paths(base_path, relative_path)
            
            # 快取結果
            self._file_cache.set(cache_key, resolved_path)
            return resolved_path
            
        except Exception as e:
            self.error_handler.log_error(f"獲取資源路徑失敗: {relative_path}", e)
            return os.path.join(os.path.abspath("."), relative_path)
    
    def _resolve_special_paths(self, base_path: str, relative_path: str) -> str:
        """解析特殊文件路徑"""
        # 移除開頭的斜線
        if relative_path.startswith(('/', '\\')):
            relative_path = relative_path[1:]
        
        # 處理指令文件
        if relative_path == 'command.txt':
            return self._find_command_file(base_path)
        
        # 處理治具指令文件
        if relative_path in ('Fixture_Command.txt', 'FIXTURE/Fixture_Command.txt'):
            return self._find_fixture_command_file(base_path)
        
        # 處理設定文件
        if relative_path == 'setup.json':
            return self._ensure_setup_file(base_path, relative_path)
            
        # 處理提示文件
        if relative_path == 'tooltips.ini':
            return self._find_tooltip_file(base_path)
        
        return os.path.join(base_path, relative_path)
    
    def _find_tooltip_file(self, base_path: str) -> str:
        """尋找提示文件"""
        possible_paths = [
            os.path.join(base_path, 'docs', 'tooltips.ini'),
            os.path.join(base_path, 'tooltips.ini'),
            os.path.join(os.path.dirname(base_path), 'docs', 'tooltips.ini')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.error_handler.log_debug(f"找到提示檔: {path}")
                return path
        
        default_path = os.path.join(base_path, 'docs', 'tooltips.ini')
        self.error_handler.log_warning(f"無法找到提示檔，使用預設路徑: {default_path}")
        return default_path
    
    def _find_command_file(self, base_path: str) -> str:
        """尋找指令文件"""
        possible_paths = [
            os.path.join(base_path, 'Command_TABLE', 'command.txt'),
            os.path.join(base_path, 'Command_TABLE', 'MU310_command.txt'),
            os.path.join(base_path, 'command.txt'),
            os.path.join(os.path.dirname(base_path), 'Command_TABLE', 'command.txt')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.error_handler.log_debug(f"找到指令檔: {path}")
                return path
        
        # 如果都找不到，返回預設路徑
        default_path = os.path.join(base_path, 'command.txt')
        self.error_handler.log_warning(f"無法找到指令檔，使用預設路徑: {default_path}")
        return default_path
    
    def _find_fixture_command_file(self, base_path: str) -> str:
        """尋找治具指令文件"""
        possible_paths = [
            os.path.join(base_path, 'FIXTURE', 'Fixture_Command.txt'),
            os.path.join(base_path, 'Fixture_Command.txt'),
            os.path.join(os.path.dirname(base_path), 'FIXTURE', 'Fixture_Command.txt')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.error_handler.log_debug(f"找到治具指令檔: {path}")
                return path
        
        default_path = os.path.join(base_path, 'FIXTURE', 'Fixture_Command.txt')
        self.error_handler.log_warning(f"無法找到治具指令檔，使用預設路徑: {default_path}")
        return default_path
    
    def _ensure_setup_file(self, base_path: str, relative_path: str) -> str:
        """確保設定文件存在"""
        setup_path = os.path.join(base_path, relative_path)
        
        if not os.path.exists(setup_path):
            self.error_handler.log_info("設定檔不存在，將由配置管理器創建")
        
        return setup_path
    
    @safe_execute(get_error_handler())
    def load_file_content(self, file_path: str, encoding: str = 'utf-8', 
                         use_cache: bool = True) -> Optional[str]:
        """載入文件內容，支援快取"""
        if use_cache:
            cache_key = f"file_{file_path}_{encoding}"
            cached_content = self._file_cache.get(cache_key)
            if cached_content is not None:
                return cached_content
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            if use_cache:
                self._file_cache.set(cache_key, content)
            
            return content
            
        except Exception as e:
            self.error_handler.log_error(f"載入文件失敗: {file_path}", e)
            return None
    
    @safe_execute(get_error_handler())
    def load_json_file(self, file_path: str, use_cache: bool = True) -> Optional[Dict]:
        """載入JSON文件，支援快取"""
        if use_cache:
            cache_key = f"json_{file_path}"
            cached_data = self._file_cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if use_cache:
                self._file_cache.set(cache_key, data)
            
            return data
            
        except Exception as e:
            self.error_handler.log_error(f"載入JSON文件失敗: {file_path}", e)
            return None
    
    def ensure_directory(self, dir_path: str) -> bool:
        """確保目錄存在"""
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                self.error_handler.log_info(f"已創建目錄: {dir_path}")
            return True
        except Exception as e:
            self.error_handler.log_error(f"創建目錄失敗: {dir_path}", e)
            return False
    
    def get_resource_lock(self, resource_name: str) -> threading.RLock:
        """獲取資源鎖"""
        with self._lock:
            if resource_name not in self._resource_locks:
                self._resource_locks[resource_name] = threading.RLock()
            return self._resource_locks[resource_name]
    
    def register_cleanup_callback(self, callback: Callable):
        """註冊清理回調函數"""
        self._cleanup_callbacks.append(callback)
    
    def cleanup(self):
        """清理資源"""
        try:
            # 執行清理回調
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    self.error_handler.log_error("執行清理回調失敗", e)
            
            # 清空快取
            self._file_cache.clear()
            self._command_cache.clear()
            
            self.error_handler.log_info("資源清理完成")
            
        except Exception as e:
            self.error_handler.log_error("資源清理失敗", e)
    
    def invalidate_cache(self, pattern: Optional[str] = None):
        """使快取失效"""
        if pattern is None:
            self._file_cache.clear()
            self._command_cache.clear()
        else:
            # 移除匹配模式的快取項目
            with self._file_cache._lock:
                keys_to_remove = [k for k in self._file_cache._cache.keys() 
                                if pattern in k]
                for key in keys_to_remove:
                    self._file_cache.remove(key)


# 全局資源管理器實例
_global_resource_manager = None

def get_resource_manager() -> ResourceManager:
    """獲取全局資源管理器"""
    global _global_resource_manager
    if _global_resource_manager is None:
        _global_resource_manager = ResourceManager()
    return _global_resource_manager
