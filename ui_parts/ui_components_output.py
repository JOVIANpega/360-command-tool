# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import sys

# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

class UIComponentsOutput:
    def init_output_components(self):
        try:
            # 建立輸出區域
            self.text_output = scrolledtext.ScrolledText(
                self.right_panel,
                wrap=tk.WORD,
                width=50,
                height=20,
                font=('Microsoft JhengHei UI', int(self.parent.setup.get('Content_Font_Size', '12')))
            )
            self.text_output.grid(row=0, column=0, sticky='nsew')
            self.right_panel.grid_rowconfigure(0, weight=1)
            self.right_panel.grid_columnconfigure(0, weight=1)
            
            # 設定 tag
            self.text_output.tag_configure("send", foreground="blue")
            self.text_output.tag_configure("end", foreground="green")  # 收到結束字串為綠色
            self.text_output.tag_configure("timeout", foreground="red")  # 超時為紅色
            self.text_output.tag_configure("purple", foreground="#800080")  # 紫色
            self.text_output.tag_configure("guide_title", foreground="#006400", font=('Microsoft JhengHei UI', int(self.parent.setup.get('Content_Font_Size', '12')) + 2, 'bold'))  # 使用說明標題
            self.text_output.tag_configure("error", foreground="red")  # 錯誤訊息為紅色
            self.text_output.tag_configure("success", foreground="green")  # 成功訊息為綠色
            self.text_output.tag_configure("warning", foreground="orange")  # 警告訊息為橙色
            
            # 為高亮關鍵字定義標籤
            print(f"[DEBUG] 初始化關鍵字高亮標籤，parent={self.parent}")
            if hasattr(self.parent, 'highlight_keywords'):
                print(f"[DEBUG] highlight_keywords={self.parent.highlight_keywords}")
                # 創建關鍵字到標籤的映射
                self.keyword_tag_map = {}
                
                for keyword, color in self.parent.highlight_keywords.items():
                    print(f"[DEBUG] 創建關鍵字標籤: {keyword} -> {color}")
                    # 為每個關鍵字創建唯一的標籤名稱
                    tag_name = f"keyword_{keyword}_{color}"
                    try:
                        self.text_output.tag_configure(tag_name, foreground=color)
                        # 記錄關鍵字到標籤的映射
                        self.keyword_tag_map[keyword] = tag_name
                    except Exception as e:
                        print(f"[ERROR] 無法創建標籤 {tag_name}，錯誤: {e}")
                        # 使用預設標籤
                        self.keyword_tag_map[keyword] = "send"
            else:
                print(f"[WARNING] parent 沒有 highlight_keywords 屬性")
            
            # 設定唯讀
            self.text_output.config(state='disabled')
            
            # 添加右鍵菜單
            self.output_context_menu = tk.Menu(self.text_output, tearoff=0)
            self.output_context_menu.add_command(label="複製", command=self.copy_selected_text)
            self.output_context_menu.add_command(label="全選", command=self.select_all_text)
            self.output_context_menu.add_separator()
            self.output_context_menu.add_command(label="清空", command=self.parent.handlers.clear_output)
            self.text_output.bind("<Button-3>", self.show_output_context_menu)
            
        except Exception as e:
            print(f"Error in init_output_components: {e}")
            import traceback
            traceback.print_exc()
            raise

    def init_progress_components(self):
        """初始化進度條組件"""
        self.progress = ttk.Progressbar(
            self.right_panel,
            mode='determinate',
            style="gray.Horizontal.TProgressbar",
            length=200
        )
        self.progress.grid(row=1, column=0, sticky='ew', pady=5)
        self.progress['value'] = 0
        # 確保進度條始終顯示
        self.progress.grid_remove()  # 初始隱藏
        self.right_panel.rowconfigure(1, weight=0)  # 進度條行不擴展

    def show_progress(self, show=True):
        """控制進度條顯示/隱藏"""
        print(f"[DEBUG] show_progress: show={show}")
        if show:
            self.progress.grid()
        else:
            self.progress.grid_remove()

    def update_progress(self, value, style="blue.Horizontal.TProgressbar"):
        """更新進度條值和樣式"""
        print(f"[DEBUG] update_progress: value={value}, style={style}")
        self.progress.config(style=style, value=value)
        self.progress.grid()  # 確保進度條顯示

    def reset_progress(self):
        """重置進度條並隱藏"""
        try:
            print("[DEBUG] reset_progress: set progress to 0 and hide")
            self.progress['value'] = 0
            self.show_progress(False)  # 隱藏進度條
            
            # 取消所有與進度條相關的定時器
            if hasattr(self.parent, 'root'):
                # 檢查是否有標記的進度條更新任務
                if hasattr(self.parent.handlers, '_progress_update_job') and self.parent.handlers._progress_update_job:
                    try:
                        self.parent.root.after_cancel(self.parent.handlers._progress_update_job)
                        self.parent.handlers._progress_update_job = None
                        print("[DEBUG] 已取消進度條更新任務")
                    except Exception as e:
                        print(f"[ERROR] 取消進度條更新任務時發生錯誤: {e}")
        except Exception as e:
            print(f"[ERROR] 重置進度條時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def add_to_buffer(self, text, tag=None):
        # 如果正在顯示使用說明，則不添加內容
        if hasattr(self.parent, 'showing_guide') and self.parent.showing_guide:
            return
            
        # 設為可編輯狀態
        self.text_output.configure(state='normal')
        
        # 若是 [送出] 開頭自動用 send tag
        if text.startswith('[發送]'):
            self.text_output.insert(tk.END, text, "send")
        # 若是 [結束] 開頭自動用 end tag
        elif text.startswith('[結束]'):
            self.text_output.insert(tk.END, text, "end")
        # 若是包含 inserted 的行，使用 purple tag
        elif "inserted" in text:
            self.text_output.insert(tk.END, text, "purple")
        # 其他情況使用指定的 tag
        elif tag:
            self.text_output.insert(tk.END, text, tag)
        else:
            # 檢查是否包含關鍵字，如果有則只高亮關鍵字部分
            if hasattr(self.parent, 'highlight_keywords') and self.parent.highlight_keywords and hasattr(self, 'keyword_tag_map'):
                # 先插入文字
                start_pos = self.text_output.index(tk.END)
                self.text_output.insert(tk.END, text)
                
                # 檢查關鍵字並應用標籤
                for keyword, tag_name in self.keyword_tag_map.items():
                    # 不區分大小寫的關鍵字檢查
                    text_lower = text.lower()
                    keyword_lower = keyword.lower()
                    
                    if keyword_lower in text_lower:
                        # 獲取插入點的行號
                        line = start_pos.split('.')[0]
                        
                        # 在文本中查找所有關鍵字出現的位置
                        start_idx = 0
                        while True:
                            idx = text_lower.find(keyword_lower, start_idx)
                            if idx == -1:
                                break
                                
                            # 計算在文本中的實際位置
                            start_col = int(start_pos.split('.')[1]) + idx
                            pos = f"{line}.{start_col}"
                            
                            # 計算關鍵字結束位置
                            end_col = start_col + len(keyword)
                            end_pos = f"{line}.{end_col}"
                            
                            # 應用標籤 - 只對關鍵字本身應用
                            try:
                                self.text_output.tag_add(tag_name, pos, end_pos)
                            except Exception as e:
                                print(f"[ERROR] 應用標籤時發生錯誤: {e}")
                            
                            # 更新搜索起點
                            start_idx = idx + len(keyword_lower)
            else:
                # 如果沒有關鍵字，直接插入文字
                self.text_output.insert(tk.END, text)
                
        # 自動捲到最底
        self.text_output.see(tk.END)
        # 設回唯讀狀態
        self.text_output.configure(state='disabled')

    def flush_buffer(self):
        """將緩衝區的文字一次性添加到輸出區域"""
        if not hasattr(self.parent, 'text_buffer') or not self.parent.text_buffer:
            return
            
        if not hasattr(self, 'text_output'):
            print("[ERROR] text_output 不存在，無法刷新緩衝區")
            return
            
        try:
            self.text_output.configure(state='normal')
            for text, tag in self.parent.text_buffer:
                if tag:
                    self.text_output.insert(tk.END, text, tag)
                else:
                    self.text_output.insert(tk.END, text)
            self.text_output.see(tk.END)  # 自動捲到最底
            self.text_output.configure(state='disabled')  # 設回唯讀狀態
            self.parent.text_buffer = []
        except Exception as e:
            print(f"[ERROR] 刷新緩衝區時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def copy_selected_text(self):
        """實現複製選中文字的功能"""
        try:
            selected_text = self.text_output.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.parent.root.clipboard_clear()
            self.parent.root.clipboard_append(selected_text)
            self.show_notification("已複製選中文字", "blue", 2000)
        except tk.TclError:
            # 沒有選中文字時不做任何操作
            pass

    def select_all_text(self):
        """實現全選文字的功能"""
        self.text_output.tag_add(tk.SEL, "1.0", tk.END)
        self.text_output.mark_set(tk.INSERT, "1.0")
        self.text_output.see(tk.INSERT)

    def show_output_context_menu(self, event):
        """顯示右鍵菜單"""
        try:
            self.output_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.output_context_menu.grab_release() 