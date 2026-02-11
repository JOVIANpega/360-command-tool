#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
強力修復 ui_settings_tab.py 中的語法錯誤
"""

import re

def fix_syntax_error():
    """修復語法錯誤"""
    file_path = 'ui_parts/ui_settings_tab.py'
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 移除所有無效字符和特殊標記
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # 跳過包含特殊標記的行
            if 'REDACTED_SPECIAL_TOKEN' in line:
                continue
            # 跳過空行（如果前面有特殊標記）
            if line.strip() == '' and len(cleaned_lines) > 0 and 'REDACTED_SPECIAL_TOKEN' in cleaned_lines[-1]:
                continue
            cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已修復 {file_path} 的語法錯誤")
        return True
        
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
        return False

if __name__ == "__main__":
    fix_syntax_error()
