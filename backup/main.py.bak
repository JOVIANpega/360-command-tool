import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import traceback
from config_core import load_commands, load_highlight_keywords
from ui_parts.ui_main import SerialUI, TabManager
import re
import threading

# è¨­ç½®è·¯å?
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

ui_parts_dir = os.path.join(current_dir, 'ui_parts')
if ui_parts_dir not in sys.path:
    sys.path.insert(0, ui_parts_dir)

def write_log(msg):
    try:
        with open("run_log.txt", "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

write_log("main.py ?Ÿå?")

try:
    from ui_parts.ui_main import TabManager
    write_log("?å? import TabManager")
except Exception as e:
    write_log("import TabManager å¤±æ?ï¼? + traceback.format_exc())
    messagebox.showerror('?¯èª¤', f'å°å…¥æ¨¡ç?å¤±æ?: {e}')
    sys.exit(1)

def main():
    # ?ˆæœ¬è¨Šæ¯
    VERSION = "V1.38"
    print(f"===== VALO360 ?‡ä»¤??{VERSION} =====")

    # è¼‰å…¥?½ä»¤æ¸…å–®
    commands = load_commands()
    
    # è¼‰å…¥?œéµå­—é?äº®è¨­å®?
    highlight_keywords = load_highlight_keywords()
    print(f"[DEBUG] main ?½æ•¸è¼‰å…¥?„é??µå?é«˜äº®è¨­å?: {highlight_keywords}")
    
    # ?å???Tkinter
    root = tk.Tk()
    root.title(f"VALO360 ?‡ä»¤??{VERSION}")
    try:
        root.iconbitmap('app.ico')
    except:
        pass
    
    # å»ºç??¸é??¡ç®¡?†å™¨ä¸¦å?å§‹å? UI
    app = TabManager(root, highlight_keywords)
    
    # ä»‹é¢ç½®ä¸­é¡¯ç¤º
    root.update_idletasks()  # ?´æ–°?ƒä»¶å°ºå¯¸
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # ?Ÿå??‰ç”¨ç¨‹å?
    root.mainloop()

if __name__ == "__main__":
    main()
    write_log("__main__ çµæ?")
