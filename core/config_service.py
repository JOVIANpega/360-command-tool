# -*- coding: utf-8 -*-
"""
ConfigService - 統一配置服務
提供高層次的配置操作接口,所有配置讀寫的單一入口

作者: Antigravity AI
日期: 2026-02-11
版本: 1.0.0
"""

from typing import Dict, Any, Optional, Callable, List
from core.config_manager import get_config_manager


class ConfigService:
    """
    統一配置服務 - 所有配置操作的單一入口
    
    設計原則:
    1. 單一職責: 每個方法只負責一類配置
    2. 驗證優先: 所有輸入都經過驗證和預設值處理
    3. 原子操作: 配置更新要麼全部成功,要麼全部失敗
    4. 事件通知: 配置更新後通知相關組件
    """
    
    _instance = None
    
    def __new__(cls):
        """單例模式 - 確保全域只有一個 ConfigService 實例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化配置服務"""
        if self._initialized:
            return
        
        self.config_manager = get_config_manager()
        self._callbacks: List[Callable] = []  # 配置更新回調函數列表
        self._initialized = True
        print("[ConfigService] 配置服務已初始化")
    
    # ==================== 回調管理 ====================
    
    def register_callback(self, callback: Callable[[str, Any], None]):
        """
        註冊配置更新回調函數
        
        Args:
            callback: 回調函數,接收 (key_path, new_value) 參數
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            print(f"[ConfigService] 已註冊回調函數: {callback.__name__}")
    
    def unregister_callback(self, callback: Callable):
        """取消註冊回調函數"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            print(f"[ConfigService] 已取消註冊回調函數: {callback.__name__}")
    
    def _notify_callbacks(self, key_path: str, new_value: Any):
        """通知所有回調函數配置已更新"""
        for callback in self._callbacks:
            try:
                callback(key_path, new_value)
            except Exception as e:
                print(f"[ConfigService] 回調函數執行失敗: {callback.__name__}, 錯誤: {e}")
    
    # ==================== 字體大小管理 ====================
    
    def update_font_size(
        self, 
        ui_size: Optional[int] = None, 
        content_size: Optional[int] = None, 
        fixture_size: Optional[int] = None
    ) -> bool:
        """
        更新字體大小 - 統一入口
        
        Args:
            ui_size: UI 字體大小 (8-20)
            content_size: 內容字體大小 (8-20)
            fixture_size: 治具字體大小 (8-20)
        
        Returns:
            bool: 儲存是否成功
        """
        try:
            config = self.config_manager.load_config()
            updated = False
            
            # 更新 UI 字體大小
            if ui_size is not None:
                ui_size = max(8, min(20, int(ui_size)))  # 限制範圍 8-20
                ui_size_str = str(ui_size)
                
                config['UIFontSize'] = ui_size_str
                config['DUT_Control']['UI_Font_Size'] = ui_size_str
                
                print(f"[ConfigService] 更新 UI 字體大小: {ui_size}")
                self._notify_callbacks('font.ui_size', ui_size)
                updated = True
            
            # 更新內容字體大小
            if content_size is not None:
                content_size = max(8, min(20, int(content_size)))
                content_size_str = str(content_size)
                
                config['ContentFontSize'] = content_size_str
                config['DUT_Control']['Content_Font_Size'] = content_size_str
                
                print(f"[ConfigService] 更新內容字體大小: {content_size}")
                self._notify_callbacks('font.content_size', content_size)
                updated = True
            
            # 更新治具字體大小
            if fixture_size is not None:
                fixture_size = max(8, min(20, int(fixture_size)))
                fixture_size_str = str(fixture_size)
                
                config['Fixture_Control']['Fixture_Font_Size'] = fixture_size_str
                
                print(f"[ConfigService] 更新治具字體大小: {fixture_size}")
                self._notify_callbacks('font.fixture_size', fixture_size)
                updated = True
            
            # 如果有更新,則儲存
            if updated:
                result = self.config_manager.save_config(config, manual_save=True)
                if result:
                    print("[ConfigService] 字體大小已成功儲存")
                else:
                    print("[ConfigService] 字體大小儲存失敗")
                return result
            
            return True
            
        except Exception as e:
            print(f"[ConfigService] 更新字體大小時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_font_size(self, font_type: str = 'ui') -> int:
        """
        獲取字體大小
        
        Args:
            font_type: 字體類型 ('ui', 'content', 'fixture')
        
        Returns:
            int: 字體大小
        """
        config = self.config_manager.load_config()
        
        if font_type == 'ui':
            size = config.get('DUT_Control', {}).get('UI_Font_Size') or config.get('UIFontSize', '12')
        elif font_type == 'content':
            size = config.get('DUT_Control', {}).get('Content_Font_Size') or config.get('ContentFontSize', '12')
        elif font_type == 'fixture':
            size = config.get('Fixture_Control', {}).get('Fixture_Font_Size', '11')
        else:
            size = '12'
        
        try:
            return int(size) if size else 12
        except (ValueError, TypeError):
            return 12
    
    # ==================== 視窗設定管理 ====================
    
    def update_window_settings(
        self, 
        title: Optional[str] = None, 
        width: Optional[int] = None, 
        height: Optional[int] = None
    ) -> bool:
        """
        更新視窗設定
        
        Args:
            title: 視窗標題
            width: 視窗寬度
            height: 視窗高度
        
        Returns:
            bool: 儲存是否成功
        """
        try:
            config = self.config_manager.load_config()
            updated = False
            
            # 更新視窗標題
            if title:
                config['Window_Title'] = title
                config['DUT_Control']['Window_Title'] = title
                print(f"[ConfigService] 更新視窗標題: {title}")
                self._notify_callbacks('window.title', title)
                updated = True
            
            # 更新視窗大小
            if width and height:
                if width > 100 and height > 100:  # 確保視窗大小有效
                    config['Window_Width'] = str(width)
                    config['Window_Height'] = str(height)
                    config['DUT_Control']['Window_Width'] = str(width)
                    config['DUT_Control']['Window_Height'] = str(height)
                    print(f"[ConfigService] 更新視窗大小: {width}x{height}")
                    self._notify_callbacks('window.size', (width, height))
                    updated = True
            
            # 如果有更新,則儲存
            if updated:
                return self.config_manager.save_config(config, manual_save=True)
            
            return True
            
        except Exception as e:
            print(f"[ConfigService] 更新視窗設定時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ==================== DUT 控制設定管理 ====================
    
    def update_dut_settings(self, **kwargs) -> bool:
        """
        更新 DUT 控制設定
        
        Args:
            **kwargs: 要更新的設定 (key=value)
        
        Returns:
            bool: 儲存是否成功
        
        Example:
            config_service.update_dut_settings(
                Command_End_String='root',
                Command_Timeout_Seconds='30'
            )
        """
        try:
            config = self.config_manager.load_config()
            updated = False
            
            for key, value in kwargs.items():
                # 只更新非空值
                if value is not None and value != '':
                    config['DUT_Control'][key] = value
                    print(f"[ConfigService] 更新 DUT 設定: {key} = {value}")
                    self._notify_callbacks(f'dut.{key}', value)
                    updated = True
            
            # 如果有更新,則儲存
            if updated:
                return self.config_manager.save_config(config, manual_save=True)
            
            return True
            
        except Exception as e:
            print(f"[ConfigService] 更新 DUT 設定時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ==================== Fixture 控制設定管理 ====================
    
    def update_fixture_settings(self, **kwargs) -> bool:
        """
        更新 Fixture 控制設定
        
        Args:
            **kwargs: 要更新的設定 (key=value)
        
        Returns:
            bool: 儲存是否成功
        """
        try:
            config = self.config_manager.load_config()
            updated = False
            
            for key, value in kwargs.items():
                if value is not None:
                    config['Fixture_Control'][key] = value
                    print(f"[ConfigService] 更新 Fixture 設定: {key} = {value}")
                    self._notify_callbacks(f'fixture.{key}', value)
                    updated = True
            
            # 如果有更新,則儲存
            if updated:
                return self.config_manager.save_config(config, manual_save=True)
            
            return True
            
        except Exception as e:
            print(f"[ConfigService] 更新 Fixture 設定時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ==================== 通用配置操作 ====================
    
    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """
        獲取配置值 (支援路徑如 'DUT_Control.UI_Font_Size')
        
        Args:
            key_path: 配置路徑,用 '.' 分隔
            default: 預設值
        
        Returns:
            配置值,如果不存在則返回預設值
        
        Example:
            ui_font_size = config_service.get_setting('DUT_Control.UI_Font_Size', '12')
        """
        try:
            config = self.config_manager.load_config()
            keys = key_path.split('.')
            value = config
            
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                    if value is None:
                        return default
                else:
                    return default
            
            # 如果值是空字串,返回預設值
            return value if value != '' else default
            
        except Exception as e:
            print(f"[ConfigService] 獲取配置值時發生錯誤: {key_path}, 錯誤: {e}")
            return default
    
    def reload_config(self) -> Dict[str, Any]:
        """重新載入配置"""
        print("[ConfigService] 重新載入配置")
        return self.config_manager.load_config()


# ==================== 全域單例獲取函數 ====================

_config_service_instance = None


def get_config_service() -> ConfigService:
    """獲取全域 ConfigService 實例"""
    global _config_service_instance
    if _config_service_instance is None:
        _config_service_instance = ConfigService()
    return _config_service_instance


# ==================== 使用範例 ====================

if __name__ == '__main__':
    # 範例: 使用 ConfigService
    
    # 1. 獲取服務實例
    config_service = get_config_service()
    
    # 2. 更新字體大小
    config_service.update_font_size(ui_size=14, content_size=12)
    
    # 3. 獲取字體大小
    ui_size = config_service.get_font_size('ui')
    print(f"UI 字體大小: {ui_size}")
    
    # 4. 更新視窗設定
    config_service.update_window_settings(title="PEGA指令通", width=1200, height=800)
    
    # 5. 更新 DUT 設定
    config_service.update_dut_settings(
        Command_End_String='root',
        Command_Timeout_Seconds='30'
    )
    
    # 6. 獲取配置值
    end_string = config_service.get_setting('DUT_Control.Command_End_String', 'root')
    print(f"命令結束字串: {end_string}")
