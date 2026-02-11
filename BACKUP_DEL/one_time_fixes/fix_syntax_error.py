#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復 ui_settings_tab.py 中的語法錯誤
"""

import re

def fix_syntax_error():
    """修復語法錯誤"""
    file_path = 'ui_parts/ui_settings_tab.py'
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 移除無效的中文註解和特殊字符
        patterns_to_remove = [
            r'現在讓我編譯檢查是否有語法錯誤：\n',
            r'REDACTED_SPECIAL_TOKENREDACTED_SPECIAL_TOKEN\n',
            r'run_terminal_cmd\n',
        ]
        
        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已修復 {file_path} 的語法錯誤")
        return True
        
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
        return False

if __name__ == "__main__":
    fix_syntax_error()
