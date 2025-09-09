# -*- coding: utf-8 -*-
"""
Tooltip 系統 - 重構版本
支援所有 tkinter 元件類型的工具提示
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
        """顯示 tooltip"""
        if self.tw or not self.text or not self.enabled:
            return

        # 獲取元件的螢幕座標
        try:
            x = self.widget.winfo_rootx()
            y = self.widget.winfo_rooty()
            w = self.widget.winfo_width()
            h = self.widget.winfo_height()
        except tk.TclError:
            # 元件可能已被銷毀
            return

        # 創建 tooltip 視窗
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        
        # 設定視窗樣式
        try:
            # 嘗試設定視窗樣式 (Windows)
            self.tw.wm_attributes("-topmost", True)
            if hasattr(self.tw, 'wm_attributes'):
                try:
                    self.tw.wm_attributes("-alpha", 0.9)
                except tk.TclError:
                    pass  # 某些系統可能不支援透明度
        except tk.TclError:
            pass

        # 創建標籤
        label = tk.Label(self.tw, 
                        text=self.text, 
                        justify='left',
                        background="#ffffe0",
                        foreground="#000000",
                        relief='solid',
                        borderwidth=1,
                        wraplength=self.wraplen,
                        font=('Tahoma', 9))
        label.pack()

        # 計算位置
        tooltip_width = label.winfo_reqwidth() + 10
        tooltip_height = label.winfo_reqheight() + 10
        
        # 預設顯示在元件下方
        tooltip_x = x + (w - tooltip_width) // 2
        tooltip_y = y + h + 5
        
        # 檢查是否超出螢幕邊界
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()
        
        if tooltip_x + tooltip_width > screen_width:
            tooltip_x = screen_width - tooltip_width - 5
        if tooltip_y + tooltip_height > screen_height:
            tooltip_y = y - tooltip_height - 5
        if tooltip_x < 0:
            tooltip_x = 5
        if tooltip_y < 0:
            tooltip_y = 5

        self.tw.geometry(f"{tooltip_width}x{tooltip_height}+{tooltip_x}+{tooltip_y}")

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
                    print(f"[DEBUG] 方法1 - 資源管理器路徑: {config_path}")
                    if os.path.exists(config_path):
                        print(f"[DEBUG] 方法1 成功找到配置文件")
                    else:
                        print(f"[DEBUG] 方法1 路徑不存在，嘗試其他方法")
                        config_path = None
                except Exception as e:
                    print(f"[DEBUG] 方法1 失敗: {e}")
                    config_path = None
            
            # 方法2: 檢查打包後的路徑（優先級提高）
            if not config_path and hasattr(sys, '_MEIPASS'):
                try:
                    meipass_path = os.path.join(sys._MEIPASS, 'tooltips.ini')
                    print(f"[DEBUG] 方法2 - _MEIPASS 路徑: {meipass_path}")
                    if os.path.exists(meipass_path):
                        config_path = meipass_path
                        print(f"[DEBUG] 方法2 成功找到配置文件")
                    else:
                        print(f"[DEBUG] 方法2 路徑不存在")
                except Exception as e:
                    print(f"[DEBUG] 方法2 失敗: {e}")
            
            # 方法3: 檢查執行檔目錄（打包後環境的優先選擇）
            if not config_path and is_frozen:
                try:
                    exe_dir = os.path.dirname(sys.executable)
                    exe_path = os.path.join(exe_dir, 'tooltips.ini')
                    print(f"[DEBUG] 方法3 - 執行檔目錄路徑: {exe_path}")
                    if os.path.exists(exe_path):
                        config_path = exe_path
                        print(f"[DEBUG] 方法3 成功找到配置文件")
                    else:
                        print(f"[DEBUG] 方法3 路徑不存在")
                except Exception as e:
                    print(f"[DEBUG] 方法3 失敗: {e}")
            
            # 方法4: 檢查當前工作目錄
            if not config_path:
                try:
                    cwd_path = os.path.join(os.getcwd(), 'tooltips.ini')
                    print(f"[DEBUG] 方法4 - 當前工作目錄路徑: {cwd_path}")
                    if os.path.exists(cwd_path):
                        config_path = cwd_path
                        print(f"[DEBUG] 方法4 成功找到配置文件")
                    else:
                        print(f"[DEBUG] 方法4 路徑不存在")
                except Exception as e:
                    print(f"[DEBUG] 方法4 失敗: {e}")
            
            # 方法5: 檢查相對路徑
            if not config_path:
                try:
                    relative_paths = [
                        'tooltips.ini',
                        'ui_parts/tooltips.ini',
                        '../tooltips.ini',
                        '../../tooltips.ini'
                    ]
                    
                    for rel_path in relative_paths:
                        test_path = os.path.abspath(rel_path)
                        print(f"[DEBUG] 方法5 - 測試相對路徑: {test_path}")
                        if os.path.exists(test_path):
                            config_path = test_path
                            print(f"[DEBUG] 方法5 成功找到配置文件: {rel_path}")
                            break
                except Exception as e:
                    print(f"[DEBUG] 方法5 失敗: {e}")
            
            # 如果找到配置文件，嘗試載入
            if config_path:
                print(f"[DEBUG] 最終使用配置文件: {config_path}")
                try:
                    config = configparser.ConfigParser()
                    config.read(config_path, encoding='utf-8')
                    
                    if config.has_section('Tooltips'):
                        self.tooltip_config = dict(config['Tooltips'])
                        print(f"[DEBUG] 成功載入 {len(self.tooltip_config)} 個tooltip配置")
                        self.enabled = True
                        return
                    else:
                        print("[WARNING] tooltip 配置文件中找不到 [Tooltips] 區段")
                except Exception as e:
                    print(f"[ERROR] 載入配置文件失敗: {e}")
            
            # 如果所有方法都失敗，使用內建配置
            print("[WARNING] 無法找到或載入 tooltips.ini 配置文件，使用內建配置")
            return self._force_use_builtin_config()
            
        except Exception as e:
            print(f"[ERROR] 載入 tooltip 配置時發生錯誤: {e}")
            print("[DEBUG] 使用內建配置作為備用")
            return self._force_use_builtin_config()
    
    def _get_builtin_config(self):
        """獲取內建的 tooltip 配置 - 完整版本"""
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
            
            # 治具控制標籤頁
            'btn_fixture_execute': '執行治具控制指令',
            'btn_fixture_clear': '清空治具控制回應內容',
            
            # 手動輸入標籤頁
            'btn_manual_execute': '執行手動輸入的指令',
            'btn_manual_clear': '清空手動輸入回應內容',
            
            # DOS標籤頁
            'btn_open_cmd': '開啟命令提示字元',
            'btn_open_powershell': '開啟PowerShell',
            'btn_browse_batch': '瀏覽批次檔',
            'btn_execute_batch': '執行批次檔',
            
            # 設定標籤頁
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
            
            # 通用組件
            'combobox_com': '選擇要連接的設備通訊埠',
            'combobox_cmd': '選擇要執行的指令',
            'combobox_end': '選擇指令結束的判斷字串',
            'entry_ip': '輸入或選擇要測試的網路位址',
            'auto_exec_checkbox': '程式啟動時自動執行指令',
            
            # 標籤組件
            'label_com': 'COM通訊埠標籤',
            'label_cmd': '指令選擇標籤',
            'label_ip': 'IP位址標籤',
            'label_end': '結束字串標籤',
            'label_timeout': '超時設定標籤',
            'label_ui_font': '介面字體大小標籤',
            'label_content_font': '內容字體大小標籤',
            
            # 控制組件
            'ui_font_scale': '調整介面字體大小的滑桿',
            'content_font_scale': '調整內容字體大小的滑桿',
            
            # 顯示組件
            'text_output': '指令執行結果顯示區域',
            'progress': '進度條顯示區域',
            
            # 框架組件
            'left_panel': '左側控制面板',
            'right_panel': '右側顯示面板',
            'main_frame': '主要內容框架',
            
            # 編輯器組件
            'section_description': '指令區段描述',
            'editor_text': '指令檔案編輯區域',
            'save_button': '儲存指令檔案',
            'reload_button': '重新載入指令檔案',
            'close_button': '關閉編輯器視窗'
        }
    
    def _force_use_builtin_config(self):
        """強制使用內建配置 - 確保 tooltip 功能正常"""
        print("[DEBUG] 強制使用內建配置以確保 tooltip 功能正常")
        self.tooltip_config = self._get_builtin_config()
        self.enabled = True
        print(f"[DEBUG] 已載入內建配置，共 {len(self.tooltip_config)} 個 tooltip")
        return True
    
    def add_tooltip(self, widget, widget_name):
        """
        為元件添加 tooltip
        widget: 要添加 tooltip 的元件
        widget_name: 在 tooltips.ini 中對應的鍵名
        """
        if not self.enabled or not widget:
            print(f"[DEBUG] add_tooltip 跳過: enabled={self.enabled}, widget={widget}")
            return
            
        tooltip_text = self.tooltip_config.get(widget_name, '')
        if not tooltip_text:
            print(f"[DEBUG] add_tooltip 跳過: 找不到配置 {widget_name}")
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
            print(f"[DEBUG] 為元件 {widget_name} 添加 tooltip: {tooltip_text[:30]}...")
            
        except Exception as e:
            print(f"[ERROR] 添加 tooltip 失敗 ({widget_name}): {e}")
    
    def add_tooltip_with_text(self, widget, text):
        """
        直接用文字為元件添加 tooltip
        """
        if not widget or not text:
            print(f"[DEBUG] add_tooltip_with_text 跳過: widget={widget}, text={text}")
            return
            
        try:
            widget_id = id(widget)
            if widget_id in self.tooltips:
                self.tooltips[widget_id].hide_tooltip()
                del self.tooltips[widget_id]
            
            tooltip = ToolTip(widget, text)
            self.tooltips[widget_id] = tooltip
            print(f"[DEBUG] 為元件添加文字 tooltip: {text[:30]}...")
            
        except Exception as e:
            print(f"[ERROR] 添加文字 tooltip 失敗: {e}")
    
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
        print(f"[DEBUG] 設定所有 tooltip 啟用狀態: {enabled}")
    
    def destroy_all(self):
        """銷毀所有 tooltip"""
        for tooltip in self.tooltips.values():
            tooltip.hide_tooltip()
        self.tooltips.clear()

# 創建全域 tooltip 管理器實例
def get_tooltip_manager():
    """獲取全域 tooltip 管理器實例"""
    if not hasattr(get_tooltip_manager, '_instance'):
        get_tooltip_manager._instance = ToolTipManager()
    return get_tooltip_manager._instance

# 為了向後兼容，保留全域變數
tooltip_manager = get_tooltip_manager()