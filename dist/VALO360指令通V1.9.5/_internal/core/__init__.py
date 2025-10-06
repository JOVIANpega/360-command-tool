# -*- coding: utf-8 -*-
"""
核心模組 - 提供統一的錯誤處理、配置管理和資源管理功能
"""

from .error_handler import (
    ErrorHandler, 
    get_error_handler,
    safe_execute,
    retry_on_failure,
    log_debug,
    log_info, 
    log_warning,
    log_error
)

from .config_manager import (
    ConfigManager,
    get_config_manager
)

from .resource_manager import (
    ResourceManager,
    ResourceCache,
    get_resource_manager
)

from .async_manager import (
    AsyncManager,
    TaskStatus,
    Task,
    get_async_manager,
    run_async,
    wait_for_result
)

from .performance_monitor import (
    PerformanceMonitor,
    PerformanceMetrics,
    FunctionProfile,
    get_performance_monitor,
    profile
)

__all__ = [
    'ErrorHandler',
    'get_error_handler',
    'safe_execute',
    'retry_on_failure',
    'log_debug',
    'log_info',
    'log_warning',
    'log_error',
    'ConfigManager',
    'get_config_manager',
    'ResourceManager',
    'ResourceCache',
    'get_resource_manager',
    'AsyncManager',
    'TaskStatus',
    'Task',
    'get_async_manager',
    'run_async',
    'wait_for_result',
    'PerformanceMonitor',
    'PerformanceMetrics',
    'FunctionProfile',
    'get_performance_monitor',
    'profile'
]
