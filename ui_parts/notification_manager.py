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
        self.breathing_job = None  # 呼吸顯示效果的任務ID
        self.message_lines = []    # 分割後的訊息行
        self.current_line_index = 0  # 當前顯示的行索引
        self.font_size = 11  # 預設字體大小
        
        # 從設定中載入通知歷史
        self.load_notification_history()
        
        # 創建通知區域
        self.create_notification_area()
        
    def create_notification_area(self):
        """創建全域通知區域 - 固定的底部通知欄"""
        # 創建通知區域主容器，使用grid而非pack來更好控制佈局
        self.notification_container = ttk.Frame(self.parent_frame)
        self.notification_container.grid(row=1, column=0, sticky='ew', padx=5, pady=0)
        
        # 配置容器的grid權重
        self.notification_container.columnconfigure(0, weight=1)
        
        # 創建控制按鈕欄（永遠顯示的介面）
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
            font=('Microsoft JhengHei UI', self.font_size),
            foreground='#666666'
        )
        self.brief_message.grid(row=0, column=1, padx=10, sticky='ew')
        
        # 右側：字體大小控制按鈕
        self.font_control_frame = ttk.Frame(self.control_frame)
        self.font_control_frame.grid(row=0, column=2, padx=5, sticky='e')
        
        # 減小字體按鈕
        self.font_minus_btn = ttk.Button(
            self.font_control_frame, 
            text="-", 
            width=2,
            command=self.decrease_font_size
        )
        self.font_minus_btn.pack(side='left', padx=2)
        
        # 增大字體按鈕
        self.font_plus_btn = ttk.Button(
            self.font_control_frame, 
            text="+", 
            width=2,
            command=self.increase_font_size
        )
        self.font_plus_btn.pack(side='left', padx=2)
        
        # 創建通知文字區域 (直接顯示，不需要展開)
        self.create_notification_text()
        
        # 記錄父容器的原始配置
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
        
    def create_notification_text(self):
        """創建通知文字顯示區域 - 簡化版本，只保留全域通知功能"""
        # 移除詳細通知記錄區域，只保留基本通知功能
        # 原本的 detail_frame、notification_text、控制按鈕等都被移除
        
        # 配置標籤樣式（保留用於可能的未來擴展）
        # 載入歷史通知（保留數據但不顯示UI）
        self.load_notification_history()
    
    def show_notification(self, message, msg_type="info", duration=0):
        """
        顯示全域通知訊息 - 支援呼吸顯示效果
        
        Args:
            message: 要顯示的訊息內容
            msg_type: 訊息類型 ("info", "success", "warning", "error")
            duration: 顯示時間(毫秒)，0表示不自動消失
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 取消先前的呼吸顯示任務
        self.cancel_breathing_display()
        
        # 根據訊息類型設定顏色
        color_map = {
            "info": "#0066cc",
            "success": "#006600", 
            "warning": "#cc6600",
            "error": "#cc0000"
        }
        text_color = color_map.get(msg_type, "#666666")
        
        # 分割長訊息為多行
        self.split_message_into_lines(message)
        
        # 如果只有一行訊息，直接顯示
        if len(self.message_lines) <= 1:
            self.brief_message.config(text=message, foreground=text_color)
        else:
            # 有多行訊息，啟動呼吸顯示效果
            self.current_line_index = 0
            self.start_breathing_display(text_color)
        
        # 記錄到歷史（保留數據功能）
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
        
        # 如果設定了自動消失時間，安排清除通知
        if duration > 0:
            if self.current_notification_job:
                self.parent_frame.after_cancel(self.current_notification_job)
            self.current_notification_job = self.parent_frame.after(duration, self.clear_notification)
    
    def split_message_into_lines(self, message):
        """將長訊息分割為多行"""
        # 獲取視窗寬度來計算每行字元數
        try:
            window_width = self.parent_frame.winfo_width()
            # 根據視窗寬度計算合適的每行字元數 (估算值)
            chars_per_line = max(40, min(50, int(window_width / 12)))
        except:
            chars_per_line = 45  # 預設值
        
        # 分割訊息
        self.message_lines = []
        if len(message) <= chars_per_line:
            self.message_lines = [message]
        else:
            # 將長訊息分割為多行
            start = 0
            while start < len(message):
                end = min(start + chars_per_line, len(message))
                # 避免在單詞中間斷行
                if end < len(message) and message[end] != ' ' and message[end-1] != ' ':
                    # 向前尋找空格
                    space_pos = message.rfind(' ', start, end)
                    if space_pos > start:
                        end = space_pos + 1
                self.message_lines.append(message[start:end])
                start = end
    
    def start_breathing_display(self, text_color):
        """開始呼吸顯示效果"""
        def show_next_line():
            if not self.message_lines:
                return
            
            # 顯示當前行
            current_line = self.message_lines[self.current_line_index]
            self.brief_message.config(text=current_line, foreground=text_color)
            
            # 更新索引，準備顯示下一行
            self.current_line_index = (self.current_line_index + 1) % len(self.message_lines)
            
            # 安排下一次顯示 (2.5秒後)
            self.breathing_job = self.parent_frame.after(2500, show_next_line)
        
        # 開始顯示第一行
        show_next_line()
    
    def cancel_breathing_display(self):
        """取消呼吸顯示效果"""
        if self.breathing_job:
            self.parent_frame.after_cancel(self.breathing_job)
            self.breathing_job = None
    
    def increase_font_size(self):
        """增加通知字體大小"""
        if self.font_size < 20:  # 設定上限
            self.font_size += 1
            self.update_font_size()
            self.save_font_size_to_setup()
    
    def decrease_font_size(self):
        """減少通知字體大小"""
        if self.font_size > 8:  # 設定下限
            self.font_size -= 1
            self.update_font_size()
            self.save_font_size_to_setup()
    
    def update_font_size(self):
        """更新字體大小"""
        self.brief_message.config(font=('Microsoft JhengHei UI', self.font_size))
    
    def save_font_size_to_setup(self):
        """將字體大小保存到設定檔"""
        try:
            current_setup = load_setup()
            if "DUT_Control" not in current_setup:
                current_setup["DUT_Control"] = {}
            
            current_setup["DUT_Control"]["Notification_Font_Size"] = str(self.font_size)
            save_setup(current_setup)
            print(f"[INFO] 已保存通知字體大小: {self.font_size}")
        except Exception as e:
            print(f"[ERROR] 保存通知字體大小時發生錯誤: {e}")
    
    def update_notification_font(self):
        """更新通知字體大小 - 已移除，保留方法避免錯誤"""
        pass
    
    def clear_notifications(self):
        """清除所有通知 - 已移除，保留方法避免錯誤"""
        pass
    
    def clear_notification(self):
        """清除目前顯示的通知"""
        try:
            # 取消呼吸顯示效果
            self.cancel_breathing_display()
            self.message_lines = []
            self.current_line_index = 0
            
            # 清除顯示
            self.brief_message.config(text="系統就緒", foreground='#666666')
        except Exception as e:
            print(f"[ERROR] 清除通知時發生錯誤: {e}")
    
    def test_notifications(self):
        """測試各種通知類型 - 已移除，保留方法避免錯誤"""
        pass

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
        """從設定檔載入通知歷史 - 簡化版本"""
        try:
            notifications = self.setup_data.get("notification_messages", {}).get("history", [])
            self.notification_log = notifications[-100:]  # 只保留最近100條
            print(f"[INFO] 已載入 {len(self.notification_log)} 條通知歷史")
            
            # 載入字體大小設定
            self.font_size = int(self.setup_data.get("DUT_Control", {}).get("Notification_Font_Size", "11"))
                
        except Exception as e:
            print(f"[ERROR] 載入通知歷史時發生錯誤: {e}")
            self.notification_log = []
            self.font_size = 11

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
        try:
            self.font_size = int(size)
            self.update_font_size()
        except:
            print(f"[ERROR] 無效的字體大小: {size}")

    def update_setup_data(self, new_setup_data):
        """更新設定資料"""
        self.setup_data = new_setup_data
        
        # 重新載入字體設定
        font_size = new_setup_data.get("DUT_Control", {}).get("Notification_Font_Size", "11")
        self.set_font_size(font_size) 