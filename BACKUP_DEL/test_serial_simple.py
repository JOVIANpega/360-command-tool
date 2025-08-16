#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單串口測試腳本
"""

import serial
import time
import sys

def test_serial_connection(com_port, command, timeout=3):
    """測試串口連接和指令執行"""
    try:
        print(f"正在連接到 {com_port}...")
        
        # 創建串口連接
        ser = serial.Serial(com_port, 115200, timeout=timeout)
        print(f"✓ 成功連接到 {com_port}")
        
        # 發送指令
        print(f"發送指令: {command}")
        ser.write(f"{command}\r\n".encode('utf-8'))
        
        # 讀取回應
        response = ""
        start_time = time.time()
        
        print("正在讀取回應...")
        while time.time() - start_time < timeout:
            if ser.in_waiting:
                data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                response += data
                print(f"收到數據: {repr(data)}")
                time.sleep(0.1)
            else:
                time.sleep(0.1)
        
        # 關閉串口
        ser.close()
        print("✓ 串口已關閉")
        
        if response:
            print(f"✓ 收到回應: {response}")
        else:
            print("⚠ 無回應")
            
        return response
        
    except Exception as e:
        print(f"✗ 錯誤: {e}")
        return None

if __name__ == "__main__":
    # 測試參數
    com_port = "COM3"  # 請根據實際情況修改
    command = "ls"
    
    print("=== 串口測試 ===")
    print(f"COM Port: {com_port}")
    print(f"指令: {command}")
    print()
    
    result = test_serial_connection(com_port, command)
    
    if result:
        print("\n✓ 測試成功")
    else:
        print("\n✗ 測試失敗") 