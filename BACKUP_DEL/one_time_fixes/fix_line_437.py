#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復 ui_settings_tab.py 第437行的```問題
"""

def fix_line_437():
    """修復第437行"""
    file_path = 'ui_parts/ui_settings_tab.py'
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 修復第437行（索引436）
        if len(lines) > 436 and '```' in lines[436]:
            lines[436] = '\n'  # 替換為空行
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"✅ 已修復第437行")
        return True
        
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
        return False

if __name__ == "__main__":
    fix_line_437()
