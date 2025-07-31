# -*- coding: utf-8 -*-
"""
統一配置管理器
提供配置的載入、保存、快取和同步功能
"""
import os
import sys
import json
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from copy import deepcopy

from .error_handler import get_error_handler, safe_execute, retry_on_failure


class ConfigManager:
    """統一配置管理器"""
    
    def __init__(self, config_file: str = "setup.json"):
        self.config_file = config_file
        self.error_handler = get_error_handler()
        self._config_cache = {}
        self._cache_lock = threading.RLock()
        self._last_modified = 0
        self._backup_dir = "backup"
        self._ensure_directories()
        
        # 預設配置
        self.default_config = {
            'version': '1.6.3.3',
            'Window_Title': '指令通',
            'Window_Width': '1536',
            'Window_Height': '793',
            'UIFontSize': '13',
            'ContentFontSize': '11',
            'DUT_Control': {
                'Serial_COM_Port': '',
                'Command_Timeout_Seconds': '30',
                'Command_End_String': 'root',
                'Command_Separator': '==>',
                'UI_Font_Size': '13',
                'Content_Font_Size': '11',
                'Window_Title': '指令通',
                'Available_End_Strings': ['root'],
                'Default_IP_Address': '192.168.11.143',
                'IP_History': [],
                'Window_Width': '1536',
                'Window_Height': '793',
                'Last_Selected_Command_Section': '全部指令',
                'Pane_Sash_Position': '636',
                'Auto_Execute': False,
                'Command_File_Path': '',
                'Notification_Font_Size': '10'
            },
            'Fixture_Control': {
                'Fixture_COM_Port': '',
                'Current_Command': '',
                'Test_Category_FUNCTION': False,
                'Test_Category_MB': True,
                'Test_Category_Original_Commands': False,
                'Fixture_Font_Size': '11'
            },
            'tab_names': {
                'tab0': 'DUT 控制',
                'tab1': '治具控制',
                'tab2': '使用說明',
                'tab3': '設定'
            },
            'UI_Settings': {
                'ToolTip_Enabled': False
            },
            'notification_messages': {
                "app_started": "指令通 已啟動",
                "settings_updated": "設定已更新！",
                "cmd_reloaded": "• 指令檔案已重新載入",
                "com_updated": "• COM口設定已更新",
                "end_string_updated": "• 結束字串設定已更新",
                "ip_updated": "• IP地址設定已更新",
                "timeout_updated": "• 超時設定已更新"
            }
        }
    
    def _ensure_directories(self):
        """確保必要目錄存在"""
        try:
            if not os.path.exists(self._backup_dir):
                os.makedirs(self._backup_dir)
        except Exception as e:
            self.error_handler.log_error("創建備份目錄失敗", e)
    
    def _get_config_path(self) -> str:
        """獲取配置文件的完整路徑"""
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, self.config_file)
    
    def _is_config_modified(self) -> bool:
        """檢查配置文件是否被修改"""
        try:
            config_path = self._get_config_path()
            if os.path.exists(config_path):
                current_modified = os.path.getmtime(config_path)
                return current_modified > self._last_modified
            return False
        except Exception:
            return True  # 如果無法檢查，假設已修改
    
    @safe_execute(get_error_handler(), show_user_error=False)
    def _backup_config(self, config_data: Dict[str, Any]):
        """備份配置文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self._backup_dir, f'setup_backup_{timestamp}.json')
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            self.error_handler.log_debug(f"配置已備份至: {backup_file}")
            self._cleanup_old_backups()
            
        except Exception as e:
            self.error_handler.log_error("備份配置失敗", e)
    
    def _cleanup_old_backups(self, keep_count: int = 30):
        """清理舊的備份文件"""
        try:
            if not os.path.exists(self._backup_dir):
                return
                
            backup_files = [
                os.path.join(self._backup_dir, f) 
                for f in os.listdir(self._backup_dir) 
                if f.startswith('setup_backup_') and f.endswith('.json')
            ]
            
            backup_files.sort(key=os.path.getmtime, reverse=True)
            
            for old_file in backup_files[keep_count:]:
                try:
                    os.remove(old_file)
                    self.error_handler.log_debug(f"已刪除舊備份: {old_file}")
                except Exception as e:
                    self.error_handler.log_warning(f"無法刪除舊備份 {old_file}", e)
                    
        except Exception as e:
            self.error_handler.log_error("清理舊備份失敗", e)
    
    @retry_on_failure(max_retries=3, delay=0.5)
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """載入配置，支援快取和自動重載"""
        with self._cache_lock:
            config_path = self._get_config_path()
            
            # 檢查是否需要重新載入
            if not force_reload and self._config_cache and not self._is_config_modified():
                return deepcopy(self._config_cache)
            
            try:
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # 備份現有配置
                    self._backup_config(config)
                    
                    # 確保所有必要字段存在
                    config = self._ensure_required_fields(config)
                    
                    # 更新快取
                    self._config_cache = deepcopy(config)
                    self._last_modified = os.path.getmtime(config_path)
                    
                    self.error_handler.log_debug("配置載入成功")
                    return deepcopy(config)
                    
                else:
                    # 配置文件不存在，創建預設配置
                    self.error_handler.log_info("配置文件不存在，創建預設配置")
                    default_config = deepcopy(self.default_config)
                    self.save_config(default_config)
                    return default_config
                    
            except Exception as e:
                self.error_handler.log_error("載入配置失敗", e, show_user=True)
                return deepcopy(self.default_config)
    
    def _ensure_required_fields(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """確保配置包含所有必要字段"""
        def merge_dict(target: Dict, source: Dict):
            for key, value in source.items():
                if key not in target:
                    target[key] = deepcopy(value)
                elif isinstance(value, dict) and isinstance(target[key], dict):
                    merge_dict(target[key], value)
        
        merge_dict(config, self.default_config)
        return config
    
    @retry_on_failure(max_retries=3, delay=0.5)
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置"""
        with self._cache_lock:
            try:
                config_path = self._get_config_path()
                
                # 備份現有配置
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            old_config = json.load(f)
                        self._backup_config(old_config)
                    except Exception as e:
                        self.error_handler.log_warning("備份現有配置失敗", e)
                
                # 保存新配置
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                # 更新快取
                self._config_cache = deepcopy(config)
                self._last_modified = os.path.getmtime(config_path)
                
                self.error_handler.log_debug("配置保存成功")
                return True
                
            except Exception as e:
                self.error_handler.log_error("保存配置失敗", e, show_user=True)
                return False
    
    def get_section(self, section_name: str) -> Dict[str, Any]:
        """獲取配置的特定區段"""
        config = self.load_config()
        return config.get(section_name, {})
    
    def update_section(self, section_name: str, section_data: Dict[str, Any]) -> bool:
        """更新配置的特定區段"""
        config = self.load_config()
        config[section_name] = section_data
        return self.save_config(config)
    
    def get_value(self, key_path: str, default: Any = None) -> Any:
        """獲取配置值，支援點號路徑 (例如: 'DUT_Control.Serial_COM_Port')"""
        config = self.load_config()
        keys = key_path.split('.')
        
        current = config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def set_value(self, key_path: str, value: Any) -> bool:
        """設置配置值，支援點號路徑"""
        config = self.load_config()
        keys = key_path.split('.')
        
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        return self.save_config(config)


# 全局配置管理器實例
_global_config_manager = None

def get_config_manager() -> ConfigManager:
    """獲取全局配置管理器"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager
