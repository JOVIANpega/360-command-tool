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

    def __init__(self, widget, text='', delay=200, wraplen=250, side='bottom'):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplen = wraplen
        self.side = side # 新增側邊參數: 'bottom' 或 'right'
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
            # (雖然下面有通用的滑動錨點邏輯，但在決定是否畫線時，大型元件仍需特殊處理以避免線條穿過元件過多)
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
        
        # 決定位置的邏輯
        is_on_primary_screen = (0 <= widget_x < screen_w)
        is_above = False
        is_left_side = False

        if self.side == 'right':
            # --- 右側顯示模式 ---
            target_y_base = widget_y + (widget_h // 2) - (text_height // 2)
            box_left = widget_x + widget_w + 20
            box_top = target_y_base
            
            if is_on_primary_screen:
                if box_left + text_width > screen_w:
                    box_left = widget_x - text_width - 20
                    is_left_side = True
                if box_top + text_height > screen_h:
                    box_top = screen_h - text_height - 10
                if box_top < 0:
                    box_top = 10
            
            if is_left_side:
                target_x = widget_x
            else:
                target_x = widget_x + widget_w
            target_y = widget_y + (widget_h // 2)
        else:
            # --- 預設：上下顯示模式 (原本最穩定的邏輯) ---
            box_x_offset = -text_width // 2
            box_left = (widget_x + widget_w // 2) + box_x_offset
            box_top = widget_y + widget_h + 20
            
            if is_on_primary_screen:
                if box_left + text_width > screen_w:
                    box_left = screen_w - text_width - 10
                if box_left < 0:
                    box_left = 10
                
                if box_top + text_height > screen_h:
                    box_top = widget_y - text_height - 20
                    is_above = True
            
            target_x = widget_x + (widget_w // 2)
            if is_above:
                target_y = widget_y
            else:
                target_y = widget_y + widget_h

        # 優化：所有元件都使用「滑動錨點」邏輯
        # 讓指引線指向元件上最接近 Tooltip 的點，減少線段長度
        box_center_x_abs = box_left + text_width // 2
        # 將目標點 clamp 在元件的左右邊界之間
        target_x = max(widget_x, min(widget_x + widget_w, box_center_x_abs))

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
        
        # 計算線長
        line_dx = cv_target_x - box_center_x
        line_dy = cv_target_y - box_center_y
        line_len_sq = line_dx*line_dx + line_dy*line_dy
        
        # 只有在滿足以下條件時才畫線：
        # 1. 不是大型元件重疊 (vertical distance check)
        # 2. 線長度不過長 (例如 > 500px 可能是異常座標)
        should_draw_line = True
        if is_large_widget and abs(cv_target_y - box_center_y) <= 30:
            should_draw_line = False
        
        # 如果線長超過 500px，視為異常（例如多螢幕座標轉換問題），不畫線以免干擾視線
        if line_len_sq > 500 * 500:
            should_draw_line = False

        if should_draw_line:
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

    def update_text(self, text):
        """更新提示文字內容"""
        self.text = text
        if self.tw:
            try:
                self.tw.destroy()
            except:
                pass
            self.tw = None

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
        """獲取內建的 tooltip 配置 - 完整版本（每個欄位提供詳細操作說明）"""
        return {
            # ===== DUT 控制標籤頁 - 按鈕 =====
            'btn_refresh': '重新掃描電腦上所有可用的 COM 通訊埠\n插拔裝置後請點此刷新',
            'btn_execute': '將目前下拉選單中選定的指令\n透過 COM 埠送出到 DUT 執行',
            'btn_ping': '對目前輸入的 IP 位址執行 ping 測試\n用於確認 DUT 是否在線上',
            'btn_save_ip': '將目前輸入的 IP 位址加入歷史記錄\n下次可直接從下拉選單選取',
            'btn_delete_ip': '從歷史記錄中移除目前選取的 IP 位址',
            'btn_clear_ip': '清空所有已儲存的 IP 位址歷史記錄',
            'btn_clear': '清空右側的回應輸出區域\n不影響已備份的記錄',
            'btn_backup': '將右側回應區域的內容\n匯出儲存為 TXT 文字檔案',
            'btn_guide': '開啟使用說明文件\n包含操作教學與常見問題',
            'btn_ui_font_plus': '放大左側介面的文字大小（+1）',
            'btn_ui_font_minus': '縮小左側介面的文字大小（-1）',
            'btn_content_font_plus': '放大右側回應區域的文字大小（+1）',
            'btn_content_font_minus': '縮小右側回應區域的文字大小（-1）',
            'btn_remove_end': '移除目前選擇的結束判斷字串\n從下拉選單中永久刪除此選項',
            'btn_open_cmd_table': '開啟指令檔案 (TXT) 編輯器\n可直接新增、修改、刪除指令',
            'btn_fixture_execute': '執行治具控制指令\n透過治具 COM 埠送出指令',
            'btn_fixture_clear': '清空治具控制頁面的回應輸出區域',
            'btn_manual_execute': '執行手動輸入的自訂指令\n支援多行指令依序送出',
            'btn_manual_clear': '清空手動輸入頁面的回應輸出區域',
            'btn_open_cmd': '開啟 Windows 命令提示字元 (CMD)',
            'btn_open_powershell': '開啟 Windows PowerShell',
            'btn_browse_batch': '瀏覽並選取要執行的批次檔 (.bat)',
            'btn_execute_batch': '執行已選取的批次檔',
            'btn_manual_save': '將設定頁面中的所有修改\n一次性儲存到 setup.json',
            'btn_browse_file': '選取新的指令 TXT 檔案\n選完後會自動儲存並即時更新指令清單',
            
            # ===== DUT 控制標籤頁 - 輸入框與下拉選單 =====
            'entry_window_title': '設定主視窗上方顯示的標題文字\n最多 30 個字元',
            'entry_window_width': '設定程式視窗的寬度（像素）\n調整後需重啟程式生效',
            'entry_window_height': '設定程式視窗的高度（像素）\n調整後需重啟程式生效',
            'entry_version': '目前程式的版本號\n修改後需重新打包 EXE 才會生效',
            'entry_com_port': '選擇 DUT 連接的 COM 通訊埠\n如果沒有顯示，請點擊刷新按鈕',
            'entry_timeout': '單個指令送出後等待回應的最長秒數\n超時後會自動停止等待並顯示錯誤',
            'entry_end_string': '用於判斷指令執行完畢的字串\n當回應中出現此字串時，視為執行完成\n常用：root、admin、$',
            'entry_separator': '多重指令的分隔符號\n系統會依據此符號拆分指令逐一送出',
            'entry_ip_address': '預設的 DUT IP 位址\n用於 SSH 連線或 ping 測試',
            'entry_pane_position': '左右面板的分隔線位置（像素）\n數值越大，左側面板越寬',
            'entry_command_file': '指令檔案 (TXT) 的完整路徑\n所有 DUT 指令都從此檔案載入',
            'entry_device_label': 'DUT 控制頁面中「清空回應」按鈕下方\n顯示的設備識別文字',
            'entry_startup_label': 'DUT 控制頁面左上方綠色標籤的文字\n用於標示目前測試的產品或專案名稱',
            'entry_tab_name': '設定各分頁的顯示名稱\n最多 10 個字元',
            'entry_manual_hint': '手動輸入指令頁面中\n輸入框上方顯示的灰色提示文字',
            'entry_custom_separator': '輸入自訂分隔符號\n按 + 新增，按 - 移除',
            'combobox_transport': '選擇指令傳輸方式\nConsole：透過 COM 埠直接傳送\nSSH：透過網路 SSH 連線傳送\nADB：透過 Android Debug Bridge 傳送',
            'combobox_separator': '選擇或自訂多重指令的分隔符號\n用於 command.txt 中的指令分割',
            'checkbox_tooltip': '啟用或停用所有元件的滑鼠懸停提示\n停用後滑鼠移上去不會再顯示說明',
            'checkbox_auto_execute': '勾選後，程式啟動時會自動執行\n第一個指令（無需手動點擊執行）',
            'combobox_com': '選擇要連接的 COM 通訊埠\n下拉選單會顯示所有可用埠號',
            'combobox_cmd': '選擇要執行的指令\n指令來源為指令檔案 (TXT)',
            'combobox_end': '選擇指令結束的判斷字串\n回應中出現此字串則視為執行完成',
            'entry_ip': '輸入要連線或測試的 IP 位址\n支援從歷史記錄中選取',
            'auto_exec_checkbox': '勾選後，程式啟動時自動執行第一個指令',
            
            # ===== 標籤與區域 =====
            'label_com': 'COM 通訊埠選擇區',
            'label_cmd': '指令選擇區',
            'label_ip': 'IP 位址輸入區',
            'label_end': '結束字串設定區',
            'label_timeout': '指令超時設定區',
            'label_ui_font': '介面字體大小調整',
            'label_content_font': '回應內容字體大小調整',
            'ui_font_scale': '拖動滑桿調整左側介面的字體大小',
            'content_font_scale': '拖動滑桿調整右側回應內容的字體大小',
            'text_output': '顯示指令執行後 DUT 回傳的結果\n支援關鍵字高亮與自動捲動',
            'progress': '顯示指令執行的進度\n綠色：執行中\n灰色：閒置',
            'left_panel': '左側控制面板\n包含指令選擇、IP 設定等操作區',
            'right_panel': '右側回應顯示面板\n顯示 DUT 回傳的所有資訊',
            'main_frame': '主要內容區域',
            'section_description': '目前選擇的指令分類描述',
            'editor_text': '指令檔案編輯區域\n可直接修改指令內容',
            'save_button': '儲存修改後的指令檔案',
            'reload_button': '重新載入指令檔案\n放棄所有未儲存的修改',
            'close_button': '關閉編輯器視窗'
        }
    
    def _force_use_builtin_config(self):
        """強制使用內建配置 - 確保 tooltip 功能正常"""
        # print("[DEBUG] 強制使用內建配置以確保 tooltip 功能正常")
        self.tooltip_config = self._get_builtin_config()
        self.enabled = True
        return True
    
    def add_tooltip(self, widget, widget_name, side='bottom'):
        """
        為元件添加 tooltip
        widget: 要添加 tooltip 的元件
        widget_name: 在 tooltips.ini 中對應的鍵名
        side: 顯示位置 ('bottom' 或 'right')
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
            tooltip = ToolTip(widget, tooltip_text, side=side)
            self.tooltips[widget_id] = tooltip
            
        except Exception:
            pass
    
    def add_tooltip_with_text(self, widget, text, side='bottom'):
        """
        直接用文字為元件添加 tooltip
        """
        if not widget or not text:
            return
            
        try:
            widget_id = id(widget)
            # [核心修正]：如果已經存在，只更新文字與方向，不要重新綁定事件
            if widget_id in self.tooltips:
                tip = self.tooltips[widget_id]
                tip.update_text(text)
                tip.side = side
                return
            
            # 如果不存在，才建立新的
            tooltip = ToolTip(widget, text, side=side)
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