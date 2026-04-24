
import os
import re

def patch_file(filepath, pattern, replacement):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Patched {filepath}")
        return True
    else:
        print(f"Pattern not found in {filepath}")
        return False

# 1. Patch ui_main.py (Ensure current_index is used)
patch_file('ui_parts/ui_main.py', 
           r'tab_text = self\.notebook\.tab\(selected_tab, "text"\)\s+', 
           'tab_text = self.notebook.tab(selected_tab, "text")\n        try:\n            current_index = self.notebook.index("current")\n        except:\n            current_index = -1\n')

patch_file('ui_parts/ui_main.py', 
           r'elif tab_text == \'設定\':', 
           "elif tab_text == '設定' or current_index == 4:")

# 2. Patch ui_settings_tab.py
# Add the sash change binding and tracking variable
patch_file('ui_parts/ui_settings_tab.py',
           r'# 讀取並設定分隔位置\s+self\.after\(200, self\.restore_sash\)\s+self\.after\(500, self\.restore_sash\)',
           '# 讀取並設定分隔位置\n        self.after(200, self.restore_sash)\n        self.after(500, self.restore_sash)\n        \n        # 綁定分割位置變更事件，即時記錄\n        self._last_known_sash_pos = None\n        def on_sash_pos_changed(e):\n            try:\n                pos = self.main_container.sashpos(0)\n                if pos > 100:\n                    self._last_known_sash_pos = pos\n                    print(f"[DEBUG] 記錄設定頁面分欄位置: {pos}")\n            except: pass\n        self.main_container.bind("<ButtonRelease-1>", on_sash_pos_changed)')

# Update manual_save_settings to use _last_known_sash_pos and sash_coord
patch_file('ui_parts/ui_settings_tab.py',
           r'# 獲取設定頁面分欄位置\s+try:\s+self\.update_idletasks\(\)\s+sash_pos = self\.main_container\.sashpos\(0\)',
           '# 獲取設定頁面分欄位置\n        try:\n            # 優先使用即時記錄的位置\n            sash_pos = getattr(self, "_last_known_sash_pos", None)\n            \n            # 如果沒有記錄或記錄無效，嘗試即時獲獲取\n            if sash_pos is None or sash_pos <= 100:\n                self.update_idletasks()\n                try:\n                    # 優先嘗試 sash_coord 獲取 X 軸位置\n                    sash_pos = self.main_container.sash_coord(0)[0]\n                except:\n                    sash_pos = self.main_container.sashpos(0)')

print("Patching complete.")
