# -*- coding: utf-8 -*-
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# 設置路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def main():
    root = tk.Tk()
    root.title("測試應用程式")
    root.geometry("800x600")
    
    # 創建一個簡單的標籤
    label = ttk.Label(root, text="這是一個測試窗口")
    label.pack(pady=20)
    
    # 創建一個按鈕
    button = ttk.Button(root, text="點擊我", command=lambda: messagebox.showinfo("訊息", "按鈕已點擊"))
    button.pack(pady=10)
    
    # 顯示窗口
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        with open("test_error.txt", "w", encoding="utf-8") as f:
            f.write(f"An unexpected error occurred: {e}\n")
            f.write(traceback.format_exc())
        print(f"An error occurred. Details have been written to test_error.txt") 