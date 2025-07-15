# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import json
import time
from datetime import datetime
from config_core import load_setup, save_setup

class NotificationManager:
    def __init__(self, parent_frame, setup_data):
        """
        初始化全域通知管理器
        
        Args:
            parent_frame: 父容器框架
            setup_data: 設定資料字典
        """
        self.parent_frame = parent_frame
        self.setup_data = setup_data
        self.notification_log = []
        self.current_notification_job = None
        self.notification_widget = None
        self.is_expanded = False  # 是否展開狀態
        
        # 從設定中載入通知歷史
        self.load_notification_history()
        
        # 創建通知區域
        self.create_notification_area()
        
    def create_notification_area(self):
        """創建全域通知區域 - 可伸縮的底部通知欄"""
        # 創建通知區域主容器，使用grid而非pack來更好控制佈局
        self.notification_container = ttk.Frame(self.parent_frame)
        self.notification_container.grid(row=1, column=0, sticky='ew', padx=5, pady=0)
        
        # 配置容器的grid權重
        self.notification_container.columnconfigure(0, weight=1)
        
        # 創建控制按鈕欄（永遠顯示的最小化介面）
        self.control_frame = ttk.Frame(self.notification_container)
        self.control_frame.grid(row=0, column=0, sticky='ew', pady=2)
        
        # 配置控制欄的grid
        self.control_frame.columnconfigure(1, weight=1)  # 中間區域可擴展
        
        # 左側：狀態標籤
        self.status_label = ttk.Label(
            self.control_frame, 
            text="🔔 全域通知",
            font=('Microsoft JhengHei UI', 10)
        )
        self.status_label.grid(row=0, column=0, padx=5, sticky='w')
        
        # 中央：最新訊息簡要顯示（一行）
        self.brief_message = ttk.Label(
            self.control_frame,
            text="系統就緒",
            font=('Microsoft JhengHei UI', 9),
            foreground='#666666'
        )
        self.brief_message.grid(row=0, column=1, padx=10, sticky='ew')
        
        # 右側：展開/收縮按鈕
        self.toggle_button = ttk.Button(
            self.control_frame,
            text="▲ 展開通知",
            command=self.toggle_notification_panel,
            width=12
        )
        self.toggle_button.grid(row=0, column=2, padx=5, sticky='e')
        
        # 創建可伸縮的詳細通知面板（初始隱藏）
        self.detail_frame = ttk.LabelFrame(
            self.notification_container,
            text="📋 詳細通知記錄",
            padding=(10, 5)
        )
        # 不在初始化時grid，等待用戶點擊展開
        
        # 創建詳細通知內容區域
        self.create_detail_content()
        
        # 記錄父容器的原始配置，以便展開時調整
        self.parent_original_config = {}
        self.store_parent_layout_config()
        
    def store_parent_layout_config(self):
        """儲存父容器的原始佈局配置"""
        try:
            # 獲取父容器的grid配置
            if hasattr(self.parent_frame, 'grid_info'):
                info = self.parent_frame.grid_info()
                self.parent_original_config['rowconfigure'] = {}
                
                # 獲取所有行的配置
                for row in range(10):  # 假設最多10行
                    try:
                        config = self.parent_frame.grid_rowconfigure(row)
                        if config:
                            self.parent_original_config['rowconfigure'][row] = config
                    except:
                        break
                        
                print(f"[DEBUG] 已儲存父容器原始配置: {self.parent_original_config}")
        except Exception as e:
            print(f"[ERROR] 儲存父容器配置時發生錯誤: {e}")
        
    def create_detail_content(self):
        """創建詳細通知內容區域"""
        # 通知文字顯示區域 - 4行高度，支援滾動
        text_frame = ttk.Frame(self.detail_frame)
        text_frame.pack(fill='both', expand=True)
        
        self.notification_text = tk.Text(
            text_frame,
            height=4,
            wrap=tk.WORD,
            font=('Microsoft JhengHei UI', 11, 'normal'),
            state='disabled',
            bg='#f8f9fa',
            relief='sunken',
            borderwidth=1
        )
        
        # 滾動條
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.notification_text.yview)
        self.notification_text.configure(yscrollcommand=scrollbar.set)
        
        self.notification_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 控制按鈕區域
        control_buttons_frame = ttk.Frame(self.detail_frame)
        control_buttons_frame.pack(fill='x', pady=(5, 0))
        
        # 左側：字體控制
        font_frame = ttk.Frame(control_buttons_frame)
        font_frame.pack(side=tk.LEFT)
        
        ttk.Label(font_frame, text="字體:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.font_size_var = tk.StringVar(value="11")
        font_spinbox = ttk.Spinbox(
            font_frame, 
            from_=8, to=16, width=4, 
            textvariable=self.font_size_var,
            command=self.update_notification_font
        )
        font_spinbox.pack(side=tk.LEFT, padx=2)
        font_spinbox.bind('<Return>', lambda e: self.update_notification_font())
        
        # 中央：功能按鈕
        button_frame = ttk.Frame(control_buttons_frame)
        button_frame.pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="清除", command=self.clear_notifications, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="📜 歷史", command=self.show_history, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="🔄 測試", command=self.test_notifications, width=8).pack(side=tk.LEFT, padx=2)
        
        # 配置標籤樣式
        self.notification_text.tag_configure("info", foreground="#0066cc")
        self.notification_text.tag_configure("success", foreground="#006600") 
        self.notification_text.tag_configure("warning", foreground="#cc6600")
        self.notification_text.tag_configure("error", foreground="#cc0000")
        self.notification_text.tag_configure("timestamp", foreground="#888888", font=('Microsoft JhengHei UI', 9))
        
        # 載入歷史通知
        self.load_notification_history()
        
    def toggle_notification_panel(self):
        """切換通知面板的展開/收縮狀態，並重新架構佈局"""
        if self.is_expanded:
            # 收縮面板 - 恢復原始佈局
            self.detail_frame.grid_forget()
            self.toggle_button.config(text="▲ 展開通知")
            self.is_expanded = False
            
            # 恢復父容器的原始grid配置
            self.restore_parent_layout()
            
        else:
            # 展開面板 - 調整佈局避免覆蓋
            self.adjust_parent_layout_for_expansion()
            
            # 顯示詳細面板
            self.detail_frame.grid(row=1, column=0, sticky='ew', pady=(5, 0))
            self.toggle_button.config(text="▼ 收縮通知")
            self.is_expanded = True
            
            # 滾動到最底部顯示最新訊息
            if self.notification_text:
                self.notification_text.see(tk.END)
                
    def adjust_parent_layout_for_expansion(self):
        """調整父容器佈局以容納展開的通知面板"""
        try:
            # 確保主內容區域行權重為1，通知區域行權重為0
            # 這樣通知區域展開時不會壓縮主內容，而是向下擴展
            
            # 設置主內容區域（第0行）為可縮放，但設置最小高度
            self.parent_frame.grid_rowconfigure(0, weight=1, minsize=400)
            
            # 設置通知區域（第1行）為固定高度，不可縮放
            self.parent_frame.grid_rowconfigure(1, weight=0)
            
            print("[DEBUG] 已調整父容器佈局以容納展開的通知面板")
            
        except Exception as e:
            print(f"[ERROR] 調整父容器佈局時發生錯誤: {e}")
            
    def restore_parent_layout(self):
        """恢復父容器的原始佈局"""
        try:
            # 恢復原始的grid配置
            self.parent_frame.grid_rowconfigure(0, weight=1)
            self.parent_frame.grid_rowconfigure(1, weight=0)
            
            print("[DEBUG] 已恢復父容器原始佈局")
            
        except Exception as e:
            print(f"[ERROR] 恢復父容器佈局時發生錯誤: {e}")
    
    def show_notification(self, message, msg_type="info"):
        """
        顯示全域通知訊息
        
        Args:
            message: 要顯示的訊息內容
            msg_type: 訊息類型 ("info", "success", "warning", "error")
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 更新簡要顯示（控制欄中的一行訊息）
        brief_text = message[:50] + "..." if len(message) > 50 else message
        self.brief_message.config(text=brief_text)
        
        # 根據訊息類型設定顏色
        color_map = {
            "info": "#0066cc",
            "success": "#006600", 
            "warning": "#cc6600",
            "error": "#cc0000"
        }
        self.brief_message.config(foreground=color_map.get(msg_type, "#666666"))
        
        # 如果面板已展開，也要更新詳細通知區域
        if self.is_expanded and self.notification_text:
            self.notification_text.config(state='normal')
            
            # 添加時間戳記
            self.notification_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
            
            # 添加訊息內容
            self.notification_text.insert(tk.END, f"{message}\n", msg_type)
            
            # 自動滾動到底部
            self.notification_text.see(tk.END)
            self.notification_text.config(state='disabled')
        
        # 記錄到歷史
        log_entry = {
            "timestamp": timestamp,
            "message": message,
            "type": msg_type
        }
        self.notification_log.append(log_entry)
        
        # 限制歷史記錄數量
        max_history = self.setup_data.get("notification_messages", {}).get("history_limit", 100)
        if len(self.notification_log) > max_history:
            self.notification_log = self.notification_log[-max_history:]
        
        # 保存歷史記錄
        self.save_notification_history()
        
        # 呼吸燈效果（僅在收縮狀態下）
        if not self.is_expanded:
            self.breathing_effect()
    
    def breathing_effect(self):
        """通知按鈕呼吸燈效果"""
        if self.current_notification_job:
            self.control_frame.after_cancel(self.current_notification_job)
        
        original_text = self.toggle_button.cget("text")
        
        def flash_step(step=0):
            if step < 6:  # 閃爍3次
                if step % 2 == 0:
                    self.toggle_button.config(text="🔔 ▲ 新通知")
                else:
                    self.toggle_button.config(text=original_text)
                self.current_notification_job = self.control_frame.after(300, lambda: flash_step(step + 1))
            else:
                self.toggle_button.config(text=original_text)
                self.current_notification_job = None
        
        flash_step()
    
    def update_notification_font(self):
        """更新通知字體大小"""
        try:
            size = int(self.font_size_var.get())
            if self.notification_text:
                font = ('Microsoft JhengHei UI', size, 'normal')
                self.notification_text.config(font=font)
                
                # 重新配置標籤字體
                self.notification_text.tag_configure("timestamp", font=('Microsoft JhengHei UI', max(size-2, 8)))
        except ValueError:
            pass
    
    def clear_notifications(self):
        """清除所有通知"""
        if self.notification_text:
            self.notification_text.config(state='normal')
            self.notification_text.delete(1.0, tk.END)
            self.notification_text.config(state='disabled')
        
        self.notification_log.clear()
        self.brief_message.config(text="通知已清除", foreground="#666666")
        self.save_notification_history()
    
    def test_notifications(self):
        """測試各種通知類型"""
        test_messages = [
            ("測試資訊通知：系統運行正常", "info"),
            ("測試成功通知：操作完成", "success"), 
            ("測試警告通知：注意某項設定", "warning"),
            ("測試錯誤通知：發生異常狀況", "error")
        ]
        
        for i, (msg, msg_type) in enumerate(test_messages):
            self.control_frame.after(i * 1000, lambda m=msg, t=msg_type: self.show_notification(m, t))

    def show_history(self):
        """顯示通知歷史對話框"""
        history_window = tk.Toplevel(self.parent_frame)
        history_window.title("通知歷史記錄")
        history_window.geometry("600x400")
        history_window.transient(self.parent_frame)
        history_window.grab_set()
        
        # 創建文字區域顯示歷史
        text_frame = ttk.Frame(history_window)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        history_text = tk.Text(text_frame, wrap=tk.WORD, font=('Microsoft JhengHei UI', 10))
        history_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=history_text.yview)
        history_text.configure(yscrollcommand=history_scrollbar.set)
        
        history_text.pack(side="left", fill="both", expand=True)
        history_scrollbar.pack(side="right", fill="y")
        
        # 配置標籤樣式
        history_text.tag_configure("info", foreground="#0066cc")
        history_text.tag_configure("success", foreground="#006600")
        history_text.tag_configure("warning", foreground="#cc6600") 
        history_text.tag_configure("error", foreground="#cc0000")
        history_text.tag_configure("timestamp", foreground="#888888")
        
        # 載入歷史記錄
        for entry in self.notification_log[-50:]:  # 只顯示最近50條
            history_text.insert(tk.END, f"[{entry['timestamp']}] ", "timestamp")
            history_text.insert(tk.END, f"{entry['message']}\n", entry.get('type', 'info'))
        
        history_text.config(state='disabled')
        history_text.see(tk.END)
        
        # 關閉按鈕
        ttk.Button(history_window, text="關閉", command=history_window.destroy).pack(pady=5)

    def load_notification_history(self):
        """從設定檔載入通知歷史"""
        try:
            notifications = self.setup_data.get("notification_messages", {}).get("history", [])
            self.notification_log = notifications[-100:]  # 只保留最近100條
            
            # 如果有歷史記錄且面板已展開，載入到顯示區域
            if self.notification_log and hasattr(self, 'notification_text') and self.notification_text and self.is_expanded:
                self.notification_text.config(state='normal')
                self.notification_text.delete(1.0, tk.END)
                
                for entry in self.notification_log[-20:]:  # 只顯示最近20條
                    timestamp = entry.get('timestamp', '')
                    message = entry.get('message', '')
                    msg_type = entry.get('type', 'info')
                    
                    self.notification_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                    self.notification_text.insert(tk.END, f"{message}\n", msg_type)
                
                self.notification_text.see(tk.END)
                self.notification_text.config(state='disabled')
                
        except Exception as e:
            print(f"[ERROR] 載入通知歷史時發生錯誤: {e}")

    def save_notification_history(self):
        """保存通知歷史到設定檔"""
        try:
            current_setup = load_setup()
            if "notification_messages" not in current_setup:
                current_setup["notification_messages"] = {}
            
            current_setup["notification_messages"]["history"] = self.notification_log
            current_setup["notification_messages"]["last_updated"] = datetime.now().isoformat()
            
            save_setup(current_setup)
        except Exception as e:
            print(f"[ERROR] 保存通知歷史時發生錯誤: {e}")

    def set_font_size(self, size):
        """設定字體大小"""
        self.font_size_var.set(str(size))
        self.update_notification_font()

    def update_setup_data(self, new_setup_data):
        """更新設定資料"""
        self.setup_data = new_setup_data
        
        # 重新載入字體設定
        font_size = new_setup_data.get("DUT_Control", {}).get("Notification_Font_Size", "11")
        self.set_font_size(font_size) 