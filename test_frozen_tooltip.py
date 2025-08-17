# -*- coding: utf-8 -*-
"""
測試打包後環境的 tooltip 功能
"""

# 模擬打包後的環境
import sys
sys.frozen = True
sys._MEIPASS = "C:\\fake_meipass"

# 導入 tooltip 管理器
from ui_parts.tooltip import get_tooltip_manager

def test_frozen_tooltip():
    """測試打包後環境的 tooltip 功能"""
    print("=== 測試打包後環境的 tooltip 功能 ===")
    
    try:
        # 獲取 tooltip 管理器
        tm = get_tooltip_manager()
        
        print(f"配置數量: {len(tm.tooltip_config)}")
        print(f"啟用狀態: {tm.enabled}")
        
        # 檢查一些關鍵的 tooltip 配置
        key_configs = [
            'btn_refresh',
            'entry_window_title',
            'combobox_transport',
            'checkbox_tooltip'
        ]
        
        print("\n關鍵 tooltip 配置檢查:")
        for key in key_configs:
            if key in tm.tooltip_config:
                print(f"✅ {key}: {tm.tooltip_config[key][:30]}...")
            else:
                print(f"❌ {key}: 找不到配置")
        
        print(f"\n總配置數量: {len(tm.tooltip_config)}")
        
        if tm.enabled and len(tm.tooltip_config) > 0:
            print("✅ tooltip 功能應該正常")
        else:
            print("❌ tooltip 功能有問題")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_frozen_tooltip()
