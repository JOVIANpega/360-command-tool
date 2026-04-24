
import os
import re

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    skip_until = -1
    for i, line in enumerate(lines):
        if i <= skip_until:
            continue
        
        # Remove duplicate current_index block in ui_main.py
        if 'try:' in line and 'current_index = self.notebook.index("current")' in (lines[i+1] if i+1 < len(lines) else ''):
            if 'try:' in (lines[i+5] if i+5 < len(lines) else '') and 'current_index = self.notebook.index("current")' in (lines[i+6] if i+6 < len(lines) else ''):
                # We found the duplicate block
                # Keep one, skip the next one
                print(f"Found duplicate current_index block in {filepath}")
        
        new_lines.append(line)
    
    # Actually, let's use a simpler string replace for the whole block
    content = "".join(new_lines)
    
    if filepath.endswith('ui_settings_tab.py'):
        # Fix the duplicate binding and logic in ui_settings_tab.py
        pattern = r'# 讀取並設定分隔位置.*?# === 左側內容 ==='
        replacement = """# 讀取並設定分隔位置
        self.after(200, self.restore_sash)
        self.after(500, self.restore_sash)
        
        # 綁定分割位置變更事件，即時記錄
        self._last_known_sash_pos = None
        def on_sash_pos_changed_local(e):
            try:
                pos = self.main_container.sashpos(0)
                if pos > 100:
                    self._last_known_sash_pos = pos
                    print(f"[DEBUG] 記錄設定頁面分欄位置: {pos}")
            except: pass
        self.main_container.bind("<ButtonRelease-1>", on_sash_pos_changed_local)
        
        # 移除儲存按鈕區域 - 因為已經移動到DUT控制區塊了
        
        # === 左側內容 ==="""
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if filepath.endswith('ui_main.py'):
        # Clean up the duplicate try block
        pattern = r'try:\s+current_index = self\.notebook\.index\("current"\)\s+except:\s+current_index = -1\s+try:\s+current_index = self\.notebook\.index\("current"\)\s+except:\s+current_index = -1'
        replacement = """try:
            current_index = self.notebook.index("current")
        except:
            current_index = -1"""
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Cleaned {filepath}")

clean_file('ui_parts/ui_main.py')
clean_file('ui_parts/ui_settings_tab.py')
