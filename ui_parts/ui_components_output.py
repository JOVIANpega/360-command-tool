# -*- coding: utf-8 -*-

import tkinter as tk


from tkinter import ttk, scrolledtext


import os


import sys


import time


from datetime import datetime


import re


from config_utils import get_notification_text





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





            # 為高亮關鍵字定義標籤，使用特殊前綴確保優先權


            print(f"[DEBUG] 初始化關鍵字高亮標籤，parent={self.parent}")


            if hasattr(self.parent, 'highlight_keywords'):


                print(f"[DEBUG] highlight_keywords={self.parent.highlight_keywords}")


                # 建立 keyword -> tag_name 對應，確保每個關鍵字唯一 tag


                self.keyword_tag_map = {}





                for keyword, color in self.parent.highlight_keywords.items():


                    print(f"[DEBUG] 創建關鍵字標籤: {keyword} -> {color}")


                    # 為每個關鍵字創建唯一的標籤名稱，使用 keyword_ 前綴避免衝突


                    tag_name = f"keyword_{keyword}_{color}_{id(self)}"


                    try:


                        # 設定關鍵字標籤，優先權設為最高


                        self.text_output.tag_configure(tag_name, foreground=color)


                        # 記錄關鍵字到標籤的映射


                        self.keyword_tag_map[keyword] = tag_name


                        print(f"[DEBUG] 成功創建關鍵字標籤: {tag_name}")


                    except Exception as e:


                        print(f"[ERROR] 無法建立標籤 {tag_name}，錯誤: {e}")


                        # 使用預設標籤


                        self.keyword_tag_map[keyword] = "send"


                # 設定標籤優先權：關鍵字標籤優先於系統標籤


                for tag_name in self.keyword_tag_map.values():


                    try:


                        self.text_output.tag_raise(tag_name)


                    except:


                        pass


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


            self.hide_progress()  # 隱藏進度條





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





    def hide_progress(self):
        """隱藏進度條"""
        try:
            self.show_progress(False)
            print("[DEBUG] 進度條已隱藏")
        except Exception as e:
            print(f"[ERROR] 隱藏進度條時發生錯誤: {e}")
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


            # 關鍵字高亮：每行只要包含 color_word.txt 的任一關鍵字就上色


            if hasattr(self.parent, 'highlight_keywords') and self.parent.highlight_keywords and hasattr(self, 'keyword_tag_map'):


                start_pos = self.text_output.index(tk.END)


                self.text_output.insert(tk.END, text)





                # 按關鍵字長度降序排列，讓較長的關鍵字優先匹配


                sorted_keywords = sorted(self.keyword_tag_map.items(), key=lambda x: len(x[0]), reverse=True)





                found_keywords = []  # 記錄找到的關鍵字，用於調試





                for keyword, tag_name in sorted_keywords:


                    search_start = start_pos


                    keyword_found = False


                    while True:


                        idx = self.text_output.search(keyword, search_start, tk.END)


                        if not idx:


                            break





                        end_idx = f"{idx}+{len(keyword)}c"


                        try:


                            # 先移除該區域的其他標籤，確保關鍵字標籤優先


                            for tag in self.text_output.tag_names(idx):


                                if not tag.startswith('keyword_'):


                                    self.text_output.tag_remove(tag, idx, end_idx)





                            self.text_output.tag_add(tag_name, idx, end_idx)





                            if not keyword_found:


                                found_keywords.append(keyword)


                                keyword_found = True





                            # print(f"[DEBUG] 成功應用關鍵字高亮: '{keyword}' 於位置 {idx}-{end_idx}, 標籤: {tag_name}")


                        except Exception as e:


                            print(f"[ERROR] tag_add 失敗: {e}")





                        search_start = end_idx





                if found_keywords:


                    # print(f"[INFO] 本行找到關鍵字: {found_keywords}")


                    pass


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


            self.show_notification(get_notification_text("text_copied"), "blue", 2000)


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