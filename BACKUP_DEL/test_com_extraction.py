#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 COM 口名稱提取功能
"""

from config_core import list_com_ports, extract_com_port_name

def test_com_extraction():
    """測試 COM 口名稱提取功能"""
    print("=== COM 口名稱提取測試 ===")
    
    # 獲取 COM 口列表
    com_ports = list_com_ports()
    print(f"找到 {len(com_ports)} 個 COM 口:")
    print()
    
    for i, display_name in enumerate(com_ports, 1):
        actual_port = extract_com_port_name(display_name)
        print(f"{i}. 顯示名稱: '{display_name}'")
        print(f"   提取的 COM 口: '{actual_port}'")
        print(f"   ✓ 指令將使用: {actual_port}")
        print()
    
    # 測試邊界情況
    print("=== 邊界情況測試 ===")
    test_cases = [
        "COM3",
        "COM9 - AT PORT", 
        "COM7 - DM PORT",
        "COM8 - NMEA PORT",
        "COM10 - SOME OTHER PORT"
    ]
    
    for test_case in test_cases:
        extracted = extract_com_port_name(test_case)
        print(f"輸入: '{test_case}' -> 輸出: '{extracted}'")

if __name__ == "__main__":
    test_com_extraction()
