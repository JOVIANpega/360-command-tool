#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試 COM 口描述信息
"""

import serial.tools.list_ports

def debug_com_ports():
    """調試 COM 口描述信息"""
    print("=== COM 口詳細信息 ===")
    
    ports = serial.tools.list_ports.comports()
    
    for i, port in enumerate(ports, 1):
        print(f"{i}. COM 口: {port.device}")
        print(f"   描述: {port.description}")
        print(f"   製造商: {port.manufacturer}")
        print(f"   硬體 ID: {port.hwid}")
        print(f"   VID:PID: {port.vid}:{port.pid}")
        print()

if __name__ == "__main__":
    debug_com_ports()
