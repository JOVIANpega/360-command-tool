# -*- coding: utf-8 -*-
"""
Tooltip 系統 - 重構版本
支援所有 tkinter 元件類型的工具提示
新增：指引線 (Leader Line) 支援與字體大小連動
"""

import tkinter as tk
from tkinter import ttk
import configparser
import os
import sys

# 導入資源管理器
try:
    from core.resource_manager import get_resource_manager
    resource_manager = get_resource_manager()
except ImportError:
    resource_manager = None

class ToolTip:
    """
    為 tkinter 元件提供工具提示的類別
    支援所有類型的 tkinter 元件
    """
    # 類別變數，用於儲存當前字體大小
    current_font_size = 9

    def __init__(self, widget, text='', delay=500, wraplen=250):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplen = wraplen
        self.id = None
        self.tw = None
        self.enabled = True
        
        # 綁定事件
        self.widget.bind("<Enter>", self.on_enter, add=True)
        self.widget.bind("<Leave>", self.on_leave, add=True)
        self.widget.bind("<Motion>", self.on_motion, add=True)
        self.widget.bind("<ButtonPress>", self.on_leave, add=True)

    def on_enter(self, event=None):
        """滑鼠進入元件"""
        if not self.enabled or not self.text:
            return
        self.schedule_tooltip()

    def on_leave(self, event=None):
        """滑鼠離開元件"""
        self.cancel_tooltip()
        self.hide_tooltip()

    def on_motion(self, event=None):
        """滑鼠移動"""
        if not self.enabled or not self.text:
            return
        # 取消當前的 tooltip 並重新安排
        self.cancel_tooltip()
        if self.tw is None:  # 只有在 tooltip 未顯示時才重新安排
            self.schedule_tooltip()

    def schedule_tooltip(self):
        """安排顯示 tooltip"""
        self.cancel_tooltip()
        self.id = self.widget.after(self.delay, self.show_tooltip)

    def cancel_tooltip(self):
        """取消 tooltip 顯示"""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show_tooltip(self):
        """顯示 tooltip（包含指引線）"""
        if self.tw or not self.text or not self.enabled:
            return

        # 獲取元件的螢幕座標
        try:
            widget_x = self.widget.winfo_rootx()
            widget_y = self.widget.winfo_rooty()
            widget_w = self.widget.winfo_width()
            widget_h = self.widget.winfo_height()
            
            # 檢查是否為大型容器元件 (如 LabelFrame, Frame)
            # 如果是大型元件，指引線可能造成視覺混亂，考慮不顯示指引線或只顯示在邊緣
            is_large_widget = (widget_w > 300 and widget_h > 150)
            
        except tk.TclError:
            # 元件可能已被銷毀
            return

        # 創建 tooltip 視窗
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        
        # 設置透明背景色
        transparent_color = '#000001' # 接近黑色但不是純黑
        self.tw.wm_attributes("-topmost", True)
        
        try:
            # Windows 支援透明顏色
            if sys.platform.startswith('win'):
                self.tw.wm_attributes("-transparentcolor", transparent_color)
            else:
                self.tw.wm_attributes("-alpha", 0.9)
        except Exception:
            pass

        # 創建 Canvas
        canvas = tk.Canvas(self.tw, bg=transparent_color, highlightthickness=0)
        canvas.pack(fill='both', expand=True)

        # 準備字體和文字
        font_size = ToolTip.current_font_size
        current_font = ('Microsoft JhengHei UI', font_size)
        
        # 計算文字大小
        temp_label = tk.Label(self.tw, text=self.text, font=current_font, wraplength=self.wraplen)
        text_width = temp_label.winfo_reqwidth()
        text_height = temp_label.winfo_reqheight()
        temp_label.destroy()

        # 決定 Tooltip Box 位置
        # 優先顯示在下方，如果空間不足則顯示在上方
        screen_w = self.widget.winfo_screenwidth()
        screen_h = self.widget.winfo_screenheight()
        
        box_x_offset = -text_width // 2 # 水平置中
        
        # 預設：元件下方 20px
        target_y_base = widget_y + widget_h
        box_top = target_y_base + 20
        box_left = (widget_x + widget_w // 2) + box_x_offset
        
        is_above = False
        
        # 邊界檢查與調整
        if box_left + text_width > screen_w:
            box_left = screen_w - text_width - 10
        if box_left < 0:
            box_left = 10
            
        if box_top + text_height > screen_h:
            # 下方空間不足，改到上方
            target_y_base = widget_y
            box_top = target_y_base - 20 - text_height
            is_above = True
        
        # 計算指引線的目標點 (widget 上的點)
        # 根據 box 的位置，選擇 widget 最近的邊緣中心點
        if is_above:
            target_x = widget_x + widget_w // 2 # 上邊緣中心
            target_y = widget_y # 上邊緣
        else:
            target_x = widget_x + widget_w // 2 # 下邊緣中心
            target_y = widget_y + widget_h # 下邊緣

        # 對於大型元件，將目標點調整到更靠近 box 的位置，避免橫跨整個元件
        if is_large_widget:
             # 如果是大型元件，將目標點 clamp 到 box_center 的水平位置
             box_center_x = box_left + text_width // 2
             target_x = max(widget_x, min(widget_x + widget_w, box_center_x))

        # 計算 Toplevel 的邊界 (包含目標點和文字框)
        tl_x = min(target_x, box_left) - 10
        tl_y = min(target_y, box_top) - 10
        br_x = max(target_x, box_left + text_width) + 10
        br_y = max(target_y, box_top + text_height) + 10
        
        tl_w = br_x - tl_x
        tl_h = br_y - tl_y
        
        self.tw.geometry(f"{tl_w}x{tl_h}+{tl_x}+{tl_y}")
        
        # 轉換座標到 Canvas 內部座標系
        cv_target_x = target_x - tl_x
        cv_target_y = target_y - tl_y
        
        cv_box_x = box_left - tl_x
        cv_box_y = box_top - tl_y
        
        # 繪製指引線 (從目標點到文字框中心)
        box_center_x = cv_box_x + text_width // 2
        box_center_y = cv_box_y + text_height // 2
        
        # 只有在非大型元件，或距離足夠時才畫線，避免視覺混亂
        if not is_large_widget or abs(cv_target_y - box_center_y) > 30:
            canvas.create_line(cv_target_x, cv_target_y, box_center_x, box_center_y, 
                              fill='#555555', width=2, arrow=tk.FIRST, arrowshape=(8,10,3))
        
        # 繪製文字背景框
        padding = 5
        bg_color = "#ffffe0"
        border_color = "#000000"
        
        canvas.create_rectangle(cv_box_x - padding, cv_box_y - padding, 
                               cv_box_x + text_width + padding, cv_box_y + text_height + padding,
                               fill=bg_color, outline=border_color, width=1)
        
        # 繪製文字
        canvas.create_text(cv_box_x, cv_box_y, 
                          text=self.text, 
                          fill="#000000", 
                          font=current_font, 
                          anchor='nw',
                          width=self.wraplen)

    def hide_tooltip(self):
        """隱藏 tooltip"""
        if self.tw:
            try:
                self.tw.destroy()
            except tk.TclError:
                pass
            finally:
                self.tw = None

    def set_enabled(self, enabled):
        """設定 tooltip 啟用狀態"""
        self.enabled = enabled
        if not enabled:
            self.hide_tooltip()

    @classmethod
    def update_class_font_size(cls, size):
        """更新類別級別的字體大小"""
        cls.current_font_size = int(size)

class ToolTipManager:
    """管理所有 tooltip 的類別"""
    
    def __init__(self):
        self.tooltips = {}
        self.tooltip_config = {}
        self.enabled = True
        self.load_tooltip_config()
        print(f"[DEBUG] ToolTipManager 初始化完成，enabled={self.enabled}")
    
    def load_tooltip_config(self):
        """載入 tooltip 配置"""
        try:
            # 檢查是否為打包後的環境
            is_frozen = getattr(sys, 'frozen', False)
            print(f"[DEBUG] 環境檢查: frozen={is_frozen}")
            
            # 在打包後的環境中，強制使用內建配置以確保功能正常
            if is_frozen:
                print("[DEBUG] 檢測到打包後的環境，強制使用內建配置以確保 tooltip 功能正常")
                return self._force_use_builtin_config()
            
            config_path = None
            
            # 方法1: 使用資源管理器
            if resource_manager:
                try:
                    config_path = resource_manager.get_resource_path('tooltips.ini')
                    if os.path.exists(config_path):
                        pass
                    else:
                        config_path = None
                except Exception:
                    config_path = None
            
            # 方法2: 檢查打包後的路徑
            if not config_path and hasattr(sys, '_MEIPASS'):
                try:
                    meipass_path = os.path.join(sys._MEIPASS, 'tooltips.ini')
                    if os.path.exists(meipass_path):
                        config_path = meipass_path
                except Exception:
                    pass
            
            # 方法3: 檢查執行檔目錄
            if not config_path and is_frozen:
                try:
                    exe_dir = os.path.dirname(sys.executable)
                    exe_path = os.path.join(exe_dir, 'tooltips.ini')
                    if os.path.exists(exe_path):
                        config_path = exe_path
                except Exception:
                    pass
            
            # 方法4: 檢查當前工作目錄
            if not config_path:
                try:
                    cwd_path = os.path.join(os.getcwd(), 'tooltips.ini')
                    if os.path.exists(cwd_path):
                        config_path = cwd_path
                except Exception:
                    pass
            
            # 如果找到配置文件，嘗試載入
            if config_path:
                print(f"[DEBUG] 最終使用配置文件: {config_path}")
                try:
                    config = configparser.ConfigParser()
                    config.read(config_path, encoding='utf-8')
                    
                    if config.has_section('Tooltips'):
                        self.tooltip_config = dict(config['Tooltips'])
                        self.enabled = True
                        return
                    else:
                        print("[WARNING] tooltip 配置文件中找不到 [Tooltips] 區段")
                except Exception as e:
                    print(f"[ERROR] 載入配置文件失敗: {e}")
            
            # 如果所有方法都失敗，使用內建配置
            return self._force_use_builtin_config()
            
        except Exception as e:
            print(f"[ERROR] 載入 tooltip 配置時發生錯誤: {e}")
            return self._force_use_builtin_config()
    
    def _get_builtin_config(self):
        """獲取內建的 tooltip 配置 - 完整版本"""
        # (保持原有的內建配置不變，這裡省略以節省空間，實際寫入時會保留)
        return {
            # DUT 控制標籤頁
            'btn_refresh': '重新掃描可用的COM通訊埠',
            'btn_execute': '執行目前選擇的指令',
            'btn_ping': '測試網路連線狀態',
            'btn_save_ip': '將目前位址加入常用清單',
            'btn_delete_ip': '從常用清單中移除目前位址',
            'btn_clear_ip': '清空所有常用位址記錄',
            'btn_clear': '清空回應內容',
            'btn_backup': '將回應內容儲存為檔案',
            'btn_guide': '顯示使用說明',
            'btn_ui_font_plus': '放大介面文字大小',
            'btn_ui_font_minus': '縮小介面文字大小',
            'btn_content_font_plus': '放大內容文字大小',
            'btn_content_font_minus': '縮小內容文字大小',
            'btn_remove_end': '移除目前選擇的結束字串',
            'btn_open_cmd_table': '開啟指令檔案編輯器',
            'btn_fixture_execute': '執行治具控制指令',
            'btn_fixture_clear': '清空治具控制回應內容',
            'btn_manual_execute': '執行手動輸入的指令',
            'btn_manual_clear': '清空手動輸入回應內容',
            'btn_open_cmd': '開啟命令提示字元',
            'btn_open_powershell': '開啟PowerShell',
            'btn_browse_batch': '瀏覽批次檔',
            'btn_execute_batch': '執行批次檔',
            'btn_manual_save': '手動儲存所有設定',
            'btn_browse_file': '瀏覽檔案',
            'entry_window_title': '設定應用程式視窗標題（最多50字元）',
            'entry_window_width': '設定視窗寬度（像素）',
            'entry_window_height': '設定視窗高度（像素）',
            'entry_version': '顯示應用程式版本號',
            'entry_com_port': '設定DUT設備的COM通訊埠',
            'entry_timeout': '設定指令執行的等待時間（秒）',
            'entry_end_string': '設定指令結束的判斷字串',
            'entry_separator': '設定指令間的分隔符號',
            'entry_ip_address': '設定預設的IP位址',
            'entry_pane_position': '設定左右面板的分隔位置',
            'entry_command_file': '設定指令檔案的路徑',
            'entry_device_label': '設定設備標籤顯示文字',
            'entry_startup_label': '設定啟動時的標籤文字',
            'entry_tab_name': '設定標籤頁的顯示名稱',
            'entry_manual_hint': '設定手動輸入區的提示文字',
            'combobox_transport': '選擇指令傳輸方式（Console或ADB）',
            'checkbox_tooltip': '啟用或禁用按鈕提示功能',
            'checkbox_auto_execute': '程式啟動時自動執行指令',
            'combobox_com': '選擇要連接的設備通訊埠',
            'combobox_cmd': '選擇要執行的指令',
            'combobox_end': '選擇指令結束的判斷字串',
            'entry_ip': '輸入或選擇要測試的網路位址',
            'auto_exec_checkbox': '程式啟動時自動執行指令',
            'label_com': 'COM通訊埠標籤',
            'label_cmd': '指令選擇標籤',
            'label_ip': 'IP位址標籤',
            'label_end': '結束字串標籤',
            'label_timeout': '超時設定標籤',
            'label_ui_font': '介面字體大小標籤',
            'label_content_font': '內容字體大小標籤',
            'ui_font_scale': '調整介面字體大小的滑桿',
            'content_font_scale': '調整內容字體大小的滑桿',
            'text_output': '指令執行結果顯示區域',
            'progress': '進度條顯示區域',
            'left_panel': '左側控制面板',
            'right_panel': '右側顯示面板',
            'main_frame': '主要內容框架',
            'section_description': '指令區段描述',
            'editor_text': '指令檔案編輯區域',
            'save_button': '儲存指令檔案',
            'reload_button': '重新載入指令檔案',
            'close_button': '關閉編輯器視窗'
        }
    
    def _force_use_builtin_config(self):
        """強制使用內建配置 - 確保 tooltip 功能正常"""
        # print("[DEBUG] 強制使用內建配置以確保 tooltip 功能正常")
        self.tooltip_config = self._get_builtin_config()
        self.enabled = True
        return True
    
    def add_tooltip(self, widget, widget_name):
        """
        為元件添加 tooltip
        widget: 要添加 tooltip 的元件
        widget_name: 在 tooltips.ini 中對應的鍵名
        """
        if not self.enabled or not widget:
            return
            
        tooltip_text = self.tooltip_config.get(widget_name, '')
        if not tooltip_text:
            return
            
        try:
            # 移除舊的 tooltip
            widget_id = id(widget)
            if widget_id in self.tooltips:
                self.tooltips[widget_id].hide_tooltip()
                del self.tooltips[widget_id]
            
            # 創建新的 tooltip
            tooltip = ToolTip(widget, tooltip_text)
            self.tooltips[widget_id] = tooltip
            
        except Exception:
            pass
    
    def add_tooltip_with_text(self, widget, text):
        """
        直接用文字為元件添加 tooltip
        """
        if not widget or not text:
            return
            
        try:
            widget_id = id(widget)
            if widget_id in self.tooltips:
                self.tooltips[widget_id].hide_tooltip()
                del self.tooltips[widget_id]
            
            tooltip = ToolTip(widget, text)
            self.tooltips[widget_id] = tooltip
            
        except Exception:
            pass
    
    def remove_tooltip(self, widget):
        """移除元件的 tooltip"""
        widget_id = id(widget)
        if widget_id in self.tooltips:
            self.tooltips[widget_id].hide_tooltip()
            del self.tooltips[widget_id]
    
    def set_all_enabled(self, enabled):
        """設定所有 tooltip 的啟用狀態"""
        self.enabled = enabled
        for tooltip in self.tooltips.values():
            tooltip.set_enabled(enabled)
    
    def destroy_all(self):
        """銷毀所有 tooltip"""
        for tooltip in self.tooltips.values():
            tooltip.hide_tooltip()
        self.tooltips.clear()

    def update_font_size(self, size):
        """
        更新所有 ToolTip 的字體大小
        size: 新的字體大小 (int)
        """
        try:
            # 更新 ToolTip 類別的靜態變數，這樣新創建的 ToolTip 就會使用新字體
            ToolTip.update_class_font_size(size)
            print(f"[DEBUG] ToolTip 字體大小已更新為: {size}")
            
            # 如果需要即時更新已顯示的 tooltips（雖然通常 tooltip 是暫時顯示的，不需要實時更新當前顯示的）
            # 但我們可以確保下次顯示時使用新字體
        except Exception as e:
            print(f"[ERROR] 更新 ToolTip 字體大小失敗: {e}")

# 創建全域 tooltip 管理器實例
def get_tooltip_manager():
    """獲取全域 tooltip 管理器實例"""
    if not hasattr(get_tooltip_manager, '_instance'):
        get_tooltip_manager._instance = ToolTipManager()
    return get_tooltip_manager._instance

# 為了向後兼容，保留全域變數
tooltip_manager = get_tooltip_manager()