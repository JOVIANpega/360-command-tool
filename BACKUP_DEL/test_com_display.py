#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 COM 口顯示功能
"""

from config_core import list_com_ports, extract_com_port_name

def test_com_display():
    """測試 COM 口顯示功能"""
    print("=== COM 口顯示測試 ===")
    
    # 獲取 COM 口列表
    com_ports = list_com_ports()
    print(f"找到 {len(com_ports)} 個 COM 口:")
    
    for i, port in enumerate(com_ports, 1):
        actual_port = extract_com_port_name(port)
        print(f"{i}. 顯示名稱: {port}")
        print(f"   實際 COM 口: {actual_port}")
        print()

if __name__ == "__main__":
    test_com_display()
