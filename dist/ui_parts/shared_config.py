# -*- coding: utf-8 -*-
"""
統一設定管理器 - 負責管理所有GUI元件之間的變數同步
避免重複建立變數導致資料未同步的問題
"""

import tkinter as tk
from config_core import load_setup, save_setup
import threading

class SharedConfigManager:
    """統一設定管理器"""
    
    def __init__(self, root=None):
        # 主要設定變數 - 只有在root窗口可用時才創建Tkinter變數
        self.vars = {}
        
        # 設定資料快取
        self.setup_data = {}
        
        # 回調函數列表 - 當設定變更時通知相關元件
        self.callbacks = {}
        
        # 線程鎖，確保設定讀寫的安全性
        self.lock = threading.Lock()
        
        # 保存root窗口引用
        self.root = root
        
        # 初始化標記
        self.initialized = False

        # 自動保存控制標記
        self._auto_save_enabled = False

        # 延遲保存控制
        self._save_timer = None
        self._save_delay_ms = 2000  # 2秒延遲保存

        # 載入初始設定資料
        self.load_from_setup()
    
    def init_vars(self, root):
        """當root窗口可用時初始化所有設定變數"""
        if self.initialized:
            return
            
        self.root = root
        
        # DUT控制相關設定
        self.vars['dut_com_port'] = tk.StringVar(root)
        self.vars['dut_timeout'] = tk.StringVar(root)
        self.vars['dut_end_string'] = tk.StringVar(root)
        self.vars['dut_ip_address'] = tk.StringVar(root)
        self.vars['dut_ui_font_size'] = tk.StringVar(root)
        self.vars['dut_content_font_size'] = tk.StringVar(root)
        self.vars['dut_notification_font_size'] = tk.StringVar(root)
        self.vars['dut_command_file_path'] = tk.StringVar(root)
        self.vars['dut_auto_execute'] = tk.BooleanVar(root)
        # 指令傳輸方式（Console/ADB）
        self.vars['command_transport_mode'] = tk.StringVar(root)
        
        # 治具控制相關設定
        self.vars['fixture_com_port'] = tk.StringVar(root)
        self.vars['fixture_font_size'] = tk.StringVar(root)
        self.vars['fixture_baudrate'] = tk.StringVar(root)
        self.vars['fixture_bytesize'] = tk.StringVar(root)
        self.vars['fixture_stopbits'] = tk.StringVar(root)
        self.vars['fixture_parity'] = tk.StringVar(root)
        self.vars['fixture_timeout'] = tk.StringVar(root)
        
        # 測試類別設定
        self.vars['fixture_test_function'] = tk.BooleanVar(root)
        self.vars['fixture_test_mb'] = tk.BooleanVar(root)
        self.vars['fixture_test_original'] = tk.BooleanVar(root)
        
        # 應用程式全域設定
        self.vars['app_version'] = tk.StringVar(root)
        self.vars['window_title'] = tk.StringVar(root)
        self.vars['window_width'] = tk.StringVar(root)
        self.vars['window_height'] = tk.StringVar(root)
        
        # 標籤頁名稱設定
        for i in range(4):
            self.vars[f'tab_name_{i}'] = tk.StringVar(root)
        
        # UI設定
        self.vars['tooltip_enabled'] = tk.BooleanVar(root)
        
        # 為所有變數綁定變更監聽
        self.bind_var_changes()
        
        # 將設定資料載入到變數中
        self.load_data_to_vars()

        # 啟用自動保存
        self._auto_save_enabled = True

        self.initialized = True
        print("[DEBUG] SharedConfigManager: Tkinter變數初始化完成")
    
    def bind_var_changes(self):
        """為所有變數綁定變更監聽"""
        # 暫時禁用自動保存，避免無限循環
        self._auto_save_enabled = False
        for var_name, var in self.vars.items():
            # 使用 trace 方法監聽變數變更
            var.trace('w', lambda name, index, mode, vn=var_name: self.on_var_changed(vn))
    
    def load_data_to_vars(self):
        """將設定資料載入到Tkinter變數中"""
        if not self.initialized:
            return
            
        try:
            # 載入 DUT 控制設定
            dut_settings = self.setup_data.get('DUT_Control', {})
            self.vars['dut_com_port'].set(dut_settings.get('Serial_COM_Port', ''))
            self.vars['dut_timeout'].set(dut_settings.get('Command_Timeout_Seconds', '30'))
            self.vars['dut_end_string'].set(dut_settings.get('Command_End_String', 'root'))
            self.vars['dut_ip_address'].set(dut_settings.get('Default_IP_Address', '192.168.11.143'))
            self.vars['dut_ui_font_size'].set(dut_settings.get('UI_Font_Size', '12'))
            self.vars['dut_content_font_size'].set(dut_settings.get('Content_Font_Size', '11'))
            self.vars['dut_notification_font_size'].set(dut_settings.get('Notification_Font_Size', '10'))
            self.vars['dut_command_file_path'].set(dut_settings.get('Command_File_Path', ''))
            self.vars['dut_auto_execute'].set(dut_settings.get('Auto_Execute', False))
            # 載入 指令傳輸方式（頂層）
            self.vars['command_transport_mode'].set(self.setup_data.get('Command_Transport_Mode', 'Console'))
            
            # 載入治具控制設定
            fixture_settings = self.setup_data.get('Fixture_Control', {})
            self.vars['fixture_com_port'].set(fixture_settings.get('Fixture_COM_Port', 'COM5'))
            self.vars['fixture_font_size'].set(fixture_settings.get('Fixture_Font_Size', '11'))
            
            # 載入測試類別設定
            self.vars['fixture_test_function'].set(fixture_settings.get('Test_Category_FUNCTION', True))
            self.vars['fixture_test_mb'].set(fixture_settings.get('Test_Category_MB', False))
            self.vars['fixture_test_original'].set(fixture_settings.get('Test_Category_Original_Commands', False))
            
            # 載入串列設定
            serial_settings = fixture_settings.get('Serial_Settings', {})
            self.vars['fixture_baudrate'].set(serial_settings.get('Baudrate', '9600'))
            self.vars['fixture_bytesize'].set(serial_settings.get('Bytesize', '8'))
            self.vars['fixture_stopbits'].set(serial_settings.get('Stopbits', '1'))
            self.vars['fixture_parity'].set(serial_settings.get('Parity', 'None'))
            self.vars['fixture_timeout'].set(serial_settings.get('Timeout', '1.0'))
            
            # 載入全域設定
            self.vars['app_version'].set(self.setup_data.get('version', 'V1.5.0.8'))
            self.vars['window_title'].set(self.setup_data.get('Window_Title', 'VALO360 指令通'))
            self.vars['window_width'].set(self.setup_data.get('Window_Width', '1024'))
            self.vars['window_height'].set(self.setup_data.get('Window_Height', '768'))
            
            # 載入標籤頁名稱
            tab_names = self.setup_data.get('tab_names', {})
            default_tab_names = ['DUT 控制', '治具控制', '使用說明', '設定']
            for i in range(4):
                self.vars[f'tab_name_{i}'].set(tab_names.get(f'tab{i}', default_tab_names[i]))
            
            # 載入UI設定
            ui_settings = self.setup_data.get('UI_Settings', {})
            self.vars['tooltip_enabled'].set(ui_settings.get('ToolTip_Enabled', True))
            
            print("[DEBUG] SharedConfigManager: 設定資料已載入到變數")
            
        except Exception as e:
            print(f"[ERROR] SharedConfigManager 載入資料到變數時發生錯誤: {e}")
    
    def on_var_changed(self, var_name):
        """當變數變更時調用"""
        # 只更新UI顯示，不自動保存到檔案
        print(f"[DEBUG] SharedConfigManager: 變數 {var_name} 已變更，等待手動保存")

        # 通知相關的回調函數
        if var_name in self.callbacks:
            for callback in self.callbacks[var_name]:
                try:
                    callback(var_name, self.vars[var_name].get())
                except Exception as e:
                    print(f"[ERROR] 執行回調函數時發生錯誤 ({var_name}): {e}")
    
    def register_callback(self, var_name, callback):
        """註冊變數變更回調函數"""
        if var_name not in self.callbacks:
            self.callbacks[var_name] = []
        self.callbacks[var_name].append(callback)
    
    def unregister_callback(self, var_name, callback):
        """取消註冊變數變更回調函數"""
        if var_name in self.callbacks and callback in self.callbacks[var_name]:
            self.callbacks[var_name].remove(callback)

    def _schedule_delayed_save(self):
        """安排延遲保存"""
        try:
            # 如果已經有保存計時器，取消它
            if self._save_timer:
                # 假設我們有root引用來取消計時器
                if hasattr(self, 'root') and self.root:
                    self.root.after_cancel(self._save_timer)

            # 安排新的延遲保存
            if hasattr(self, 'root') and self.root:
                self._save_timer = self.root.after(self._save_delay_ms, self._delayed_save)
                print(f"[DEBUG] SharedConfigManager: 已安排 {self._save_delay_ms}ms 後保存配置")

        except Exception as e:
            print(f"[ERROR] SharedConfigManager: 安排延遲保存時發生錯誤: {e}")

    def _delayed_save(self):
        """延遲保存執行"""
        try:
            self._save_timer = None
            self.save_to_setup()
            print("[DEBUG] SharedConfigManager: 延遲保存已執行")
        except Exception as e:
            print(f"[ERROR] SharedConfigManager: 延遲保存時發生錯誤: {e}")
    
    def load_from_setup(self):
        """從 setup.json 載入設定資料（不依賴Tkinter變數）"""
        with self.lock:
            try:
                self.setup_data = load_setup()
                print("[DEBUG] SharedConfigManager: 設定資料載入完成")
            except Exception as e:
                print(f"[ERROR] SharedConfigManager 載入設定時發生錯誤: {e}")
                self.setup_data = {}
    
    def save_to_setup(self):
        """將設定儲存到 setup.json"""
        with self.lock:
            try:
                if not self.initialized:
                    print("[WARNING] SharedConfigManager: 尚未初始化Tkinter變數，無法儲存")
                    return
                    
                setup = load_setup()
                
                # 更新 DUT 控制設定
                if 'DUT_Control' not in setup:
                    setup['DUT_Control'] = {}
                
                dut_settings = setup['DUT_Control']
                dut_settings['Serial_COM_Port'] = self.vars['dut_com_port'].get()
                dut_settings['Command_Timeout_Seconds'] = self.vars['dut_timeout'].get()
                dut_settings['Command_End_String'] = self.vars['dut_end_string'].get()
                dut_settings['Default_IP_Address'] = self.vars['dut_ip_address'].get()
                dut_settings['UI_Font_Size'] = self.vars['dut_ui_font_size'].get()
                dut_settings['Content_Font_Size'] = self.vars['dut_content_font_size'].get()
                dut_settings['Notification_Font_Size'] = self.vars['dut_notification_font_size'].get()
                dut_settings['Command_File_Path'] = self.vars['dut_command_file_path'].get()
                dut_settings['Auto_Execute'] = self.vars['dut_auto_execute'].get()
                # 保存 指令傳輸方式（頂層）
                setup['Command_Transport_Mode'] = self.vars['command_transport_mode'].get() or 'Console'
                
                # 更新治具控制設定
                if 'Fixture_Control' not in setup:
                    setup['Fixture_Control'] = {}
                
                fixture_settings = setup['Fixture_Control']
                fixture_settings['Fixture_COM_Port'] = self.vars['fixture_com_port'].get()
                fixture_settings['Fixture_Font_Size'] = self.vars['fixture_font_size'].get()
                fixture_settings['Test_Category_FUNCTION'] = self.vars['fixture_test_function'].get()
                fixture_settings['Test_Category_MB'] = self.vars['fixture_test_mb'].get()
                fixture_settings['Test_Category_Original_Commands'] = self.vars['fixture_test_original'].get()
                
                # 更新串列設定
                if 'Serial_Settings' not in fixture_settings:
                    fixture_settings['Serial_Settings'] = {}
                
                serial_settings = fixture_settings['Serial_Settings']
                serial_settings['Baudrate'] = self.vars['fixture_baudrate'].get()
                serial_settings['Bytesize'] = self.vars['fixture_bytesize'].get()
                serial_settings['Stopbits'] = self.vars['fixture_stopbits'].get()
                serial_settings['Parity'] = self.vars['fixture_parity'].get()
                serial_settings['Timeout'] = self.vars['fixture_timeout'].get()
                
                # 更新全域設定
                setup['version'] = self.vars['app_version'].get()
                setup['Window_Title'] = self.vars['window_title'].get()
                setup['Window_Width'] = self.vars['window_width'].get()
                setup['Window_Height'] = self.vars['window_height'].get()
                
                # 更新標籤頁名稱
                if 'tab_names' not in setup:
                    setup['tab_names'] = {}
                
                for i in range(4):
                    setup['tab_names'][f'tab{i}'] = self.vars[f'tab_name_{i}'].get()
                
                # 更新UI設定
                if 'UI_Settings' not in setup:
                    setup['UI_Settings'] = {}
                setup['UI_Settings']['ToolTip_Enabled'] = self.vars['tooltip_enabled'].get()
                
                # 儲存設定
                save_setup(setup)
                self.setup_data = setup  # 更新本地快取
                print("[DEBUG] SharedConfigManager: 設定儲存完成")
                
            except Exception as e:
                print(f"[ERROR] SharedConfigManager 儲存設定時發生錯誤: {e}")
    
    def get_var(self, var_name):
        """取得指定的設定變數"""
        if self.initialized and var_name in self.vars:
            return self.vars[var_name]
        else:
            # 如果Tkinter變數還沒初始化，返回設定資料中的值
            return self.get_data_value(var_name)
    
    def get_data_value(self, var_name):
        """從設定資料中取得值（不依賴Tkinter變數）"""
        # 映射變數名稱到設定路徑
        mapping = {
            'dut_com_port': ('DUT_Control', 'Serial_COM_Port', ''),
            'dut_timeout': ('DUT_Control', 'Command_Timeout_Seconds', '30'),
            'dut_end_string': ('DUT_Control', 'Command_End_String', 'root'),
            'dut_ip_address': ('DUT_Control', 'Default_IP_Address', '192.168.11.143'),
            'dut_ui_font_size': ('DUT_Control', 'UI_Font_Size', '12'),
            'dut_content_font_size': ('DUT_Control', 'Content_Font_Size', '11'),
            'dut_notification_font_size': ('DUT_Control', 'Notification_Font_Size', '10'),
            'dut_command_file_path': ('DUT_Control', 'Command_File_Path', ''),
            'dut_auto_execute': ('DUT_Control', 'Auto_Execute', False),
            'command_transport_mode': ('__TOP__', 'Command_Transport_Mode', 'Console'),
            'fixture_com_port': ('Fixture_Control', 'Fixture_COM_Port', 'COM5'),
            'fixture_font_size': ('Fixture_Control', 'Fixture_Font_Size', '11'),
            'fixture_test_function': ('Fixture_Control', 'Test_Category_FUNCTION', True),
            'fixture_test_mb': ('Fixture_Control', 'Test_Category_MB', False),
            'fixture_test_original': ('Fixture_Control', 'Test_Category_Original_Commands', False),
            'fixture_baudrate': ('Fixture_Control.Serial_Settings', 'Baudrate', '9600'),
            'fixture_bytesize': ('Fixture_Control.Serial_Settings', 'Bytesize', '8'),
            'fixture_stopbits': ('Fixture_Control.Serial_Settings', 'Stopbits', '1'),
            'fixture_parity': ('Fixture_Control.Serial_Settings', 'Parity', 'None'),
            'fixture_timeout': ('Fixture_Control.Serial_Settings', 'Timeout', '1.0'),
        }
        
        if var_name in mapping:
            section, key, default = mapping[var_name]
            if section == '__TOP__':
                return self.setup_data.get(key, default)
            if '.' in section:  # 處理嵌套設定
                main_section, sub_section = section.split('.')
                return self.setup_data.get(main_section, {}).get(sub_section, {}).get(key, default)
            else:
                return self.setup_data.get(section, {}).get(key, default)
        
        return None
    
    def set_var(self, var_name, value):
        """設定指定的設定變數值"""
        if self.initialized and var_name in self.vars:
            self.vars[var_name].set(value)
    
    def update_ui_fonts(self, size):
        """更新所有UI字體大小"""
        if self.initialized:
            self.vars['dut_ui_font_size'].set(str(size))
        # 這裡會觸發回調函數來更新相關UI元件
    
    def update_fixture_fonts(self, size):
        """更新治具字體大小"""
        if self.initialized:
            self.vars['fixture_font_size'].set(str(size))
        # 這裡會觸發回調函數來更新相關UI元件

    def disable_auto_save(self):
        """禁用自動保存"""
        self._auto_save_enabled = False
        print("[DEBUG] SharedConfigManager: 自動保存已禁用")

    def enable_auto_save(self):
        """啟用自動保存"""
        self._auto_save_enabled = True
        print("[DEBUG] SharedConfigManager: 自動保存已啟用")

    def force_save_all(self):
        """強制保存所有待保存的設定"""
        try:
            print("[DEBUG] SharedConfigManager: 開始強制保存所有設定...")

            # 載入當前完整的 setup 資料
            setup = load_setup()

            if self.initialized:
                # 如果已初始化，從 Tkinter 變數收集設定
                print("[DEBUG] SharedConfigManager: 從 Tkinter 變數收集設定...")

                # 更新 DUT 控制設定
                if 'DUT_Control' not in setup:
                    setup['DUT_Control'] = {}

                # 映射 Tkinter 變數到設定路徑
                var_mapping = {
                    'dut_com_port': 'Serial_COM_Port',
                    'dut_timeout': 'Command_Timeout_Seconds',
                    'dut_end_string': 'Command_End_String',
                    'dut_ip_address': 'Default_IP_Address',
                    'dut_ui_font_size': 'UI_Font_Size',
                    'dut_content_font_size': 'Content_Font_Size',
                    'dut_notification_font_size': 'Notification_Font_Size',
                    'dut_command_file_path': 'Command_File_Path',
                    'dut_auto_execute': 'Auto_Execute',
                    'window_width': 'Window_Width',
                    'window_height': 'Window_Height',
                    'window_title': 'Window_Title'
                }

                # 更新 DUT_Control 設定
                for var_name, setup_key in var_mapping.items():
                    if var_name in self.vars:
                        try:
                            value = self.vars[var_name].get()
                            setup['DUT_Control'][setup_key] = value
                            print(f"[DEBUG] SharedConfigManager: 更新 DUT_Control.{setup_key} = {value}")
                        except Exception as e:
                            print(f"[WARNING] SharedConfigManager: 無法獲取變數 {var_name}: {e}")

                # 更新全域設定
                global_mapping = {
                    'app_version': 'version',
                    'window_title': 'Window_Title',
                    'window_width': 'Window_Width',
                    'window_height': 'Window_Height',
                    'command_transport_mode': 'Command_Transport_Mode',
                }

                for var_name, setup_key in global_mapping.items():
                    if var_name in self.vars:
                        try:
                            value = self.vars[var_name].get()
                            setup[setup_key] = value
                            print(f"[DEBUG] SharedConfigManager: 更新全域 {setup_key} = {value}")
                        except Exception as e:
                            print(f"[WARNING] SharedConfigManager: 無法獲取變數 {var_name}: {e}")

                # 更新標籤頁名稱
                if 'tab_names' not in setup:
                    setup['tab_names'] = {}

                for i in range(4):
                    var_name = f'tab_name_{i}'
                    if var_name in self.vars:
                        try:
                            value = self.vars[var_name].get()
                            setup['tab_names'][f'tab{i}'] = value
                            print(f"[DEBUG] SharedConfigManager: 更新標籤頁 tab{i} = {value}")
                        except Exception as e:
                            print(f"[WARNING] SharedConfigManager: 無法獲取標籤頁變數 {var_name}: {e}")

                # 更新UI設定
                if 'UI_Settings' not in setup:
                    setup['UI_Settings'] = {}

                if 'tooltip_enabled' in self.vars:
                    try:
                        value = self.vars['tooltip_enabled'].get()
                        setup['UI_Settings']['ToolTip_Enabled'] = value
                        print(f"[DEBUG] SharedConfigManager: 更新 UI_Settings.ToolTip_Enabled = {value}")
                    except Exception as e:
                        print(f"[WARNING] SharedConfigManager: 無法獲取 tooltip_enabled: {e}")

            # 如果有 root 窗口，獲取當前視窗狀態
            if self.root and hasattr(self.root, 'winfo_exists') and self.root.winfo_exists():
                try:
                    # 獲取當前視窗大小
                    width = self.root.winfo_width()
                    height = self.root.winfo_height()

                    if width > 100 and height > 100:  # 確保視窗大小有效
                        setup['Window_Width'] = str(width)
                        setup['Window_Height'] = str(height)
                        setup['DUT_Control']['Window_Width'] = str(width)
                        setup['DUT_Control']['Window_Height'] = str(height)
                        print(f"[DEBUG] SharedConfigManager: 更新視窗大小: {width}x{height}")

                    # 獲取當前視窗標題（去除版本號）
                    current_title = self.root.title()
                    window_title = current_title
                    if "_" in current_title:
                        parts = current_title.split("_")
                        if len(parts) >= 2:
                            window_title = "_".join(parts[:-1])
                    elif " V" in current_title:
                        window_title = current_title.split(" V")[0]

                    setup['Window_Title'] = window_title
                    setup['DUT_Control']['Window_Title'] = window_title
                    print(f"[DEBUG] SharedConfigManager: 更新視窗標題: {window_title}")

                except Exception as e:
                    print(f"[WARNING] SharedConfigManager: 獲取視窗狀態失敗: {e}")

            # 強制保存到檔案
            save_setup(setup, manual_save=True)
            self.setup_data = setup  # 更新本地快取
            print(f"[DEBUG] SharedConfigManager: 強制保存完成")

        except Exception as e:
            print(f"[ERROR] SharedConfigManager: 強制保存失敗: {e}")
            import traceback
            traceback.print_exc()

# 全域設定管理器實例
shared_config = None

def get_shared_config(root=None):
    """取得全域設定管理器實例"""
    global shared_config
    if shared_config is None:
        shared_config = SharedConfigManager(root)
    
    # 如果有root窗口且尚未初始化Tkinter變數，則進行初始化
    if root and not shared_config.initialized:
        shared_config.init_vars(root)
    
    return shared_config 