# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import json
import time
from datetime import datetime
from config_core import load_setup, save_setup
import scrolledtext # Added for scrolledtext

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
        
        # 從設定中載入字體大小
        self.font_size = self.setup_data.get("DUT_Control", {}).get("Notification_Font_Size", 11)
        try:
            self.font_size = int(self.font_size)
        except (ValueError, TypeError):
            self.font_size = 11
        
        # 標準 UI 參數
        self.ui_font = "Segoe UI"  # Windows 預設字體
        self.ui_padding = 5        # 元件間距
        
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
            font=(self.ui_font, 10)
        )
        self.status_label.grid(row=0, column=0, padx=5, sticky='w')
        
        # 中央：最新訊息簡要顯示（一行）
        self.brief_message = ttk.Label(
            self.control_frame,
            text="系統就緒",
            font=(self.ui_font, self.font_size),
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
            command=self.decrease_font_size,
            style="Notification.TButton"
        )
        self.font_minus_btn.pack(side='left', padx=2)
        
        # 顯示當前字體大小
        self.font_size_label = ttk.Label(
            self.font_control_frame,
            text=str(self.font_size),
            width=2,
            anchor='center',
            font=(self.ui_font, 10)
        )
        self.font_size_label.pack(side='left', padx=2)
        
        # 增大字體按鈕
        self.font_plus_btn = ttk.Button(
            self.font_control_frame, 
            text="+", 
            width=2,
            command=self.increase_font_size,
            style="Notification.TButton"
        )
        self.font_plus_btn.pack(side='left', padx=2)
        
        # 為按鈕添加 ToolTip
        try:
            from ui_parts.tooltip import ToolTip
            ToolTip(self.font_minus_btn, "減小通知字體")
            ToolTip(self.font_plus_btn, "增大通知字體")
        except ImportError:
            pass
        
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
                # 找到合適的分割點
                end = min(start + chars_per_line, len(message))
                
                # 如果不是在字符串的末尾，嘗試在空格或標點符號處分割
                if end < len(message):
                    # 從分割點向前尋找空格或標點符號
                    for i in range(end, start, -1):
                        if message[i-1] in ' ,.;:!?':
                            end = i
                            break
                        # 如果搜索了10個字符還沒找到合適的分割點，就強制分割
                        if i <= end - 10:
                            break
                
                self.message_lines.append(message[start:end])
                start = end
    
    def start_breathing_display(self, text_color):
        """開始呼吸顯示效果"""
        def show_next_line():
            """顯示下一行訊息"""
            if not self.message_lines:
                return
            
            # 顯示當前行
            current_line = self.message_lines[self.current_line_index]
            self.brief_message.config(text=current_line, foreground=text_color)
            
            # 更新索引，準備顯示下一行
            self.current_line_index = (self.current_line_index + 1) % len(self.message_lines)
            
            # 安排下一次顯示 (2.5秒後)
            self.breathing_job = self.parent_frame.after(2500, show_next_line)
        
        # 開始顯示
        show_next_line()
    
    def cancel_breathing_display(self):
        """取消呼吸顯示效果"""
        if self.breathing_job:
            self.parent_frame.after_cancel(self.breathing_job)
            self.breathing_job = None
    
    def increase_font_size(self):
        """增大通知字體"""
        if self.font_size < 20:  # 設定上限
            self.font_size += 1
            self.update_font_size()
            self.save_font_size_to_setup()
    
    def decrease_font_size(self):
        """減小通知字體"""
        if self.font_size > 8:  # 設定下限
            self.font_size -= 1
            self.update_font_size()
            self.save_font_size_to_setup()
    
    def update_font_size(self):
        """更新通知字體大小"""
        self.brief_message.config(font=(self.ui_font, self.font_size))
        self.font_size_label.config(text=str(self.font_size))
    
    def save_font_size_to_setup(self):
        """保存字體大小設定到 setup.json"""
        try:
            # 更新內部設定
            if "DUT_Control" not in self.setup_data:
                self.setup_data["DUT_Control"] = {}
            self.setup_data["DUT_Control"]["Notification_Font_Size"] = self.font_size
            
            # 保存到檔案
            save_setup(self.setup_data)
            print(f"[DEBUG] 已保存通知字體大小: {self.font_size}")
        except Exception as e:
            print(f"[ERROR] 保存字體大小設定時發生錯誤: {e}")
    
    def update_notification_font(self):
        """更新通知字體 (供外部調用)"""
        self.update_font_size()
    
    def clear_notifications(self):
        """清除所有通知"""
        self.clear_notification()
    
    def clear_notification(self):
        """清除當前通知"""
        # 取消呼吸顯示
        self.cancel_breathing_display()
        
        # 清空訊息
        self.brief_message.config(text="", foreground="#666666")
        
        # 取消自動消失任務
        if self.current_notification_job:
            self.parent_frame.after_cancel(self.current_notification_job)
            self.current_notification_job = None
    
    def test_notifications(self):
        """測試通知功能"""
        self.show_notification("這是一條測試通知，用於測試全域通知系統的功能。", "info", 5000)
    
    def show_history(self):
        """顯示通知歷史"""
        # 這個方法在簡化版中不再顯示歷史記錄UI
        # 但我們保留這個方法以保持API兼容性
        
        # 如果需要，可以在這裡添加一個彈出窗口來顯示歷史記錄
        try:
            history_window = tk.Toplevel(self.parent_frame)
            history_window.title("通知歷史")
            history_window.geometry("600x400")
            history_window.minsize(400, 300)
            
            # 創建文本框
            history_text = scrolledtext.ScrolledText(
                history_window, 
                wrap=tk.WORD, 
                font=(self.ui_font, 10)
            )
            history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 顯示歷史記錄
            for entry in self.notification_log:
                timestamp = entry.get("timestamp", "")
                message = entry.get("message", "")
                msg_type = entry.get("type", "info")
                
                # 根據類型設定顏色
                tag = f"type_{msg_type}"
                if not tag in history_text.tag_names():
                    color_map = {
                        "info": "#0066cc",
                        "success": "#006600", 
                        "warning": "#cc6600",
                        "error": "#cc0000"
                    }
                    history_text.tag_configure(tag, foreground=color_map.get(msg_type, "#666666"))
                
                # 插入內容
                history_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                history_text.insert(tk.END, f"{message}\n", tag)
            
            # 滾動到底部
            history_text.see(tk.END)
            
            # 設定為只讀
            history_text.config(state=tk.DISABLED)
            
            # 添加關閉按鈕
            close_btn = ttk.Button(history_window, text="關閉", command=history_window.destroy)
            close_btn.pack(pady=10)
            
            # 設定模態
            history_window.transient(self.parent_frame)
            history_window.grab_set()
            self.parent_frame.wait_window(history_window)
        except Exception as e:
            print(f"[ERROR] 顯示通知歷史時發生錯誤: {e}")
    
    def load_notification_history(self):
        """載入通知歷史"""
        try:
            history = self.setup_data.get("notification_messages", {}).get("history", [])
            if history and isinstance(history, list):
                self.notification_log = history
                print(f"[DEBUG] 已載入 {len(history)} 條通知歷史")
        except Exception as e:
            print(f"[ERROR] 載入通知歷史時發生錯誤: {e}")
            self.notification_log = []
    
    def save_notification_history(self):
        """保存通知歷史"""
        try:
            if "notification_messages" not in self.setup_data:
                self.setup_data["notification_messages"] = {}
            self.setup_data["notification_messages"]["history"] = self.notification_log
            # 不立即保存到檔案，避免頻繁寫入
        except Exception as e:
            print(f"[ERROR] 保存通知歷史時發生錯誤: {e}")
    
    def set_font_size(self, size):
        """設定字體大小"""
        try:
            size = int(size)
            if 8 <= size <= 20:
                self.font_size = size
                self.update_font_size()
        except (ValueError, TypeError):
            pass
    
    def update_setup_data(self, new_setup_data):
        """更新設定數據"""
        self.setup_data = new_setup_data
        # 重新載入字體大小
        font_size = self.setup_data.get("DUT_Control", {}).get("Notification_Font_Size", 11)
        try:
            self.font_size = int(font_size)
            self.update_font_size()
        except (ValueError, TypeError):
            pass 