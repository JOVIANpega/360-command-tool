# -*- coding: utf-8 -*-
"""
從 setup.json 讀取版本號並輸出供 BAT 使用
"""
import json
import sys

try:
    with open('setup.json', 'r', encoding='utf-8') as f:
        setup = json.load(f)
    
    version = setup.get('version', '2.5.0')
    print(version)
    sys.exit(0)
    
except Exception as e:
    print(f"讀取版本號失敗: {e}", file=sys.stderr)
    print("2.5.0")  # 預設版本號
    sys.exit(1)
