# -*- coding: utf-8 -*-
"""
測試關鍵字高亮功能的簡單程式
"""

import tkinter as tk
from tkinter import scrolledtext
import os
import sys

# 添加專案路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from config_core import load_color_word

def test_highlight():
    # 創建主視窗
    root = tk.Tk()
    root.title("關鍵字高亮測試")
    root.geometry("600x400")
    
    # 載入關鍵字
    keywords = load_color_word()
    print(f"載入關鍵字: {keywords}")
    
    # 創建文字區域
    text_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # 設定系統標籤
    text_widget.tag_configure("send", foreground="blue")
    text_widget.tag_configure("end", foreground="green")
    
    # 設定關鍵字標籤（使用簡化命名）
    keyword_tag_map = {}
    for keyword, color in keywords.items():
        tag_name = f"kw_{len(keyword_tag_map)}"
        text_widget.tag_configure(tag_name, foreground=color)
        keyword_tag_map[keyword] = tag_name
        # 設定最高優先權
        text_widget.tag_raise(tag_name)
        print(f"創建標籤: {tag_name} -> {keyword} ({color})")
    
    def add_test_text():
        test_messages = [
            "[發送] 測試指令",
            "BT init succeeds - 這應該是藍色的",
            "[結束] success 測試完成",  # 混合標籤測試
            "error occurred during test",
            "connection successful",
            "ping 192.168.11.143 timeout",
            "test failed with warning",
            "version check complete"
        ]
        
        for msg in test_messages:
            # 記錄插入位置
            start_pos = text_widget.index(tk.END)
            
            # 插入文字
            text_widget.insert(tk.END, msg + "\n")
            
            # 計算文字範圍
            end_pos = text_widget.index(tk.END + "-1c")
            
            # 應用系統標籤
            if msg.startswith('[發送]'):
                text_widget.tag_add("send", start_pos, end_pos)
            elif msg.startswith('[結束]'):
                text_widget.tag_add("end", start_pos, end_pos)
            
            # 應用關鍵字高亮
            for keyword, tag_name in keyword_tag_map.items():
                search_start = start_pos
                while True:
                    idx = text_widget.search(keyword, search_start, end_pos)
                    if not idx:
                        break
                    keyword_end_idx = f"{idx}+{len(keyword)}c"
                    text_widget.tag_add(tag_name, idx, keyword_end_idx)
                    print(f"應用關鍵字標籤: {keyword} 於 {idx}-{keyword_end_idx}")
                    search_start = keyword_end_idx
    
    # 添加測試按鈕
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=5)
    
    tk.Button(btn_frame, text="載入測試文字", command=add_test_text).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="清空", command=lambda: text_widget.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
    
    # 顯示說明
    info_text = f"已載入 {len(keywords)} 個關鍵字：{list(keywords.keys())}"
    text_widget.insert(tk.END, info_text + "\n" + "="*50 + "\n")
    
    root.mainloop()

if __name__ == "__main__":
    test_highlight() 