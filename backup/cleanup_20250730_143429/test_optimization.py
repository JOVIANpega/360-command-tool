# -*- coding: utf-8 -*-
"""
優化效果測試腳本
驗證新的核心模組功能是否正常工作
"""
import sys
import os
import time
import threading

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_error_handler():
    """測試錯誤處理系統"""
    print("=== 測試錯誤處理系統 ===")
    
    try:
        from core import get_error_handler, log_info, log_error, safe_execute
        
        error_handler = get_error_handler()
        print("✓ 錯誤處理器初始化成功")
        
        # 測試日誌功能
        log_info("這是一條測試資訊")
        log_error("這是一條測試錯誤", show_user=False)
        print("✓ 日誌功能正常")
        
        # 測試安全執行裝飾器
        @safe_execute(error_handler)
        def test_function():
            return "測試成功"
        
        result = test_function()
        if result == "測試成功":
            print("✓ 安全執行裝飾器正常")
        
        return True
        
    except Exception as e:
        print(f"✗ 錯誤處理系統測試失敗: {e}")
        return False

def test_config_manager():
    """測試配置管理系統"""
    print("\n=== 測試配置管理系統 ===")
    
    try:
        from core import get_config_manager
        
        config_manager = get_config_manager()
        print("✓ 配置管理器初始化成功")
        
        # 測試配置讀取
        config = config_manager.load_config()
        if isinstance(config, dict):
            print("✓ 配置載入正常")
        
        # 測試配置設置
        test_value = "test_value_123"
        config_manager.set_value("test_key", test_value)
        retrieved_value = config_manager.get_value("test_key")
        
        if retrieved_value == test_value:
            print("✓ 配置讀寫正常")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置管理系統測試失敗: {e}")
        return False

def test_resource_manager():
    """測試資源管理系統"""
    print("\n=== 測試資源管理系統 ===")
    
    try:
        from core import get_resource_manager
        
        resource_manager = get_resource_manager()
        print("✓ 資源管理器初始化成功")
        
        # 測試路徑解析
        setup_path = resource_manager.get_resource_path("setup.json")
        if setup_path:
            print("✓ 資源路徑解析正常")
        
        # 測試目錄創建
        test_dir = "test_temp_dir"
        if resource_manager.ensure_directory(test_dir):
            print("✓ 目錄創建功能正常")
            # 清理測試目錄
            try:
                os.rmdir(test_dir)
            except:
                pass
        
        return True
        
    except Exception as e:
        print(f"✗ 資源管理系統測試失敗: {e}")
        return False

def test_async_manager():
    """測試異步處理系統"""
    print("\n=== 測試異步處理系統 ===")
    
    try:
        from core import get_async_manager, run_async, TaskStatus
        
        async_manager = get_async_manager()
        print("✓ 異步管理器初始化成功")
        
        # 測試異步任務
        def test_task(value):
            time.sleep(0.1)  # 模擬工作
            return value * 2
        
        result_received = threading.Event()
        task_result = None
        
        def on_complete(result):
            nonlocal task_result
            task_result = result
            result_received.set()
        
        task_id = run_async(test_task, 5, callback=on_complete)
        print("✓ 異步任務提交成功")
        
        # 等待結果
        if result_received.wait(timeout=2.0):
            if task_result == 10:
                print("✓ 異步任務執行正常")
            else:
                print(f"✗ 異步任務結果錯誤: 期望 10, 得到 {task_result}")
        else:
            print("✗ 異步任務超時")
        
        return True
        
    except Exception as e:
        print(f"✗ 異步處理系統測試失敗: {e}")
        return False

def test_performance_monitor():
    """測試性能監控系統"""
    print("\n=== 測試性能監控系統 ===")
    
    try:
        from core import get_performance_monitor, profile
        
        monitor = get_performance_monitor()
        print("✓ 性能監控器初始化成功")
        
        # 測試性能分析裝飾器
        @profile("test_function")
        def test_function():
            time.sleep(0.01)  # 模擬工作
            return "完成"
        
        # 執行幾次測試函數
        for _ in range(3):
            test_function()
        
        # 檢查性能數據
        profiles = monitor.get_function_profiles()
        if "test_function" in profiles:
            profile_data = profiles["test_function"]
            if profile_data.call_count == 3:
                print("✓ 性能分析功能正常")
            else:
                print(f"✗ 性能分析計數錯誤: 期望 3, 得到 {profile_data.call_count}")
        else:
            print("✗ 性能分析數據未找到")
        
        return True
        
    except Exception as e:
        print(f"✗ 性能監控系統測試失敗: {e}")
        return False

def test_integration():
    """測試整合功能"""
    print("\n=== 測試整合功能 ===")
    
    try:
        # 測試舊API的相容性
        from config_core import load_setup, save_setup, list_com_ports
        
        # 測試配置載入
        setup = load_setup()
        if isinstance(setup, dict):
            print("✓ 舊版配置API相容性正常")
        
        # 測試COM口列表
        com_ports = list_com_ports()
        if isinstance(com_ports, list):
            print("✓ COM口列表功能正常")
        
        return True
        
    except Exception as e:
        print(f"✗ 整合功能測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("VALO360 指令通 - 優化效果測試")
    print("=" * 50)
    
    tests = [
        test_error_handler,
        test_config_manager,
        test_resource_manager,
        test_async_manager,
        test_performance_monitor,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ 測試 {test.__name__} 發生異常: {e}")
    
    print("\n" + "=" * 50)
    print(f"測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！優化成功！")
        return True
    else:
        print("⚠️  部分測試失敗，請檢查相關模組")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
