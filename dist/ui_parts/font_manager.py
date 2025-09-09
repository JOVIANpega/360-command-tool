# -*- coding: utf-8 -*-
"""
字體管理器模組
負責管理整個應用程式的字體設定和更新
"""

import tkinter as tk
import tkinter.ttk as ttk


class FontManager:
    """字體管理器類別，負責統一管理應用程式的字體設定"""
    
    def __init__(self, parent):
        """
        初始化字體管理器
        
        Args:
            parent: 父級UI元件
        """
        self.parent = parent
        self.ui_font_family = 'Microsoft JhengHei UI'
        self.content_font_family = 'Consolas'
        self.default_ui_size = 12
        self.default_content_size = 12
    
    def change_ui_font_size(self, size):
        """
        更改UI字體大小
        
        Args:
            size: 字體大小
        """
        try:
            # 更新當前元件的UI字體
            self._update_current_ui_fonts(size)
            
            # 更新全域UI字體
            self.update_global_ui_fonts(size)
            
            print(f"[DEBUG] UI字體大小已更新為: {size}")
        except Exception as e:
            print(f"更改UI字體大小時發生錯誤: {e}")
    
    def change_content_font_size(self, size):
        """
        更改內容字體大小
        
        Args:
            size: 字體大小
        """
        try:
            # 更新當前元件的內容字體
            self._update_current_content_fonts(size)
            
            # 更新全域內容字體
            self.update_global_content_fonts(size)
            
            print(f"[DEBUG] 內容字體大小已更新為: {size}")
        except Exception as e:
            print(f"更改內容字體大小時發生錯誤: {e}")
    
    def _update_current_ui_fonts(self, size):
        """更新當前元件的UI字體"""
        try:
            font = (self.ui_font_family, int(size))
            
            # 更新當前元件中的UI元素
            if hasattr(self.parent, 'components'):
                components = self.parent.components
                
                # 更新標籤
                for attr_name in dir(components):
                    if attr_name.startswith('label_'):
                        widget = getattr(components, attr_name, None)
                        if widget and hasattr(widget, 'config'):
                            try:
                                widget.config(font=font)
                            except:
                                pass
                
                # 更新按鈕
                for attr_name in dir(components):
                    if attr_name.startswith('button_') or attr_name.endswith('_button'):
                        widget = getattr(components, attr_name, None)
                        if widget and hasattr(widget, 'config'):
                            try:
                                widget.config(font=font)
                            except:
                                pass
        except Exception as e:
            print(f"更新當前UI字體時發生錯誤: {e}")
    
    def _update_current_content_fonts(self, size):
        """更新當前元件的內容字體"""
        try:
            font = (self.content_font_family, int(size))
            
            # 更新當前元件中的內容元素
            if hasattr(self.parent, 'components'):
                components = self.parent.components
                
                # 更新輸入框
                for attr_name in dir(components):
                    if 'combobox' in attr_name or 'entry' in attr_name:
                        widget = getattr(components, attr_name, None)
                        if widget and hasattr(widget, 'config'):
                            try:
                                widget.config(font=font)
                            except:
                                pass
                
                # 更新文字區域
                if hasattr(components, 'text_output'):
                    try:
                        components.text_output.config(font=font)
                    except:
                        pass
        except Exception as e:
            print(f"更新當前內容字體時發生錯誤: {e}")
    
    def update_global_ui_fonts(self, size):
        """更新全域UI字體大小"""
        try:
            # 獲取主視窗的TabManager
            root = self.parent.root
            if hasattr(root, 'tab_manager'):
                tab_manager = root.tab_manager
                
                # 更新各個標籤頁的UI字體
                if hasattr(tab_manager, 'settings_ui'):
                    self.update_settings_tab_fonts(tab_manager.settings_ui, size)
                
                if hasattr(tab_manager, 'dos_ui'):
                    self.update_dos_tab_fonts(tab_manager.dos_ui, size)
                
                if hasattr(tab_manager, 'guide_ui'):
                    self.update_guide_tab_fonts(tab_manager.guide_ui, size)
                
                if hasattr(tab_manager, 'fixture_ui'):
                    self.update_fixture_tab_fonts(tab_manager.fixture_ui, size)
                
                print(f"[DEBUG] 全域UI字體已更新為: {size}")
        except Exception as e:
            print(f"[ERROR] 更新全域UI字體時發生錯誤: {e}")
    
    def update_global_content_fonts(self, size):
        """更新全域內容字體大小"""
        try:
            # 獲取主視窗的TabManager
            root = self.parent.root
            if hasattr(root, 'tab_manager'):
                tab_manager = root.tab_manager
                
                # 更新各個標籤頁的內容字體
                if hasattr(tab_manager, 'settings_ui'):
                    self.update_settings_tab_content_fonts(tab_manager.settings_ui, size)
                
                if hasattr(tab_manager, 'dos_ui'):
                    self.update_dos_tab_content_fonts(tab_manager.dos_ui, size)
                
                if hasattr(tab_manager, 'guide_ui'):
                    self.update_guide_tab_content_fonts(tab_manager.guide_ui, size)
                
                if hasattr(tab_manager, 'fixture_ui'):
                    self.update_fixture_tab_content_fonts(tab_manager.fixture_ui, size)
                
                print(f"[DEBUG] 全域內容字體已更新為: {size}")
        except Exception as e:
            print(f"[ERROR] 更新全域內容字體時發生錯誤: {e}")
    
    def update_settings_tab_fonts(self, settings_ui, size):
        """更新設定標籤頁的UI字體"""
        try:
            font = (self.ui_font_family, int(size))
            # 更新設定標籤頁中的所有標籤
            for widget in settings_ui.parent_frame.winfo_children():
                self._update_widget_font_recursive(widget, font, ['Label', 'Button'])
        except Exception as e:
            print(f"[ERROR] 更新設定標籤頁字體時發生錯誤: {e}")
    
    def update_dos_tab_fonts(self, dos_ui, size):
        """更新DOS標籤頁的UI字體"""
        try:
            font = (self.ui_font_family, int(size))
            # 更新DOS標籤頁中的所有標籤和按鈕
            for widget in dos_ui.parent_frame.winfo_children():
                self._update_widget_font_recursive(widget, font, ['Label', 'Button'])
        except Exception as e:
            print(f"[ERROR] 更新DOS標籤頁字體時發生錯誤: {e}")
    
    def update_guide_tab_fonts(self, guide_ui, size):
        """更新使用說明標籤頁的UI字體"""
        try:
            font = (self.ui_font_family, int(size))
            # 更新使用說明標籤頁中的所有標籤和按鈕
            for widget in guide_ui.parent_frame.winfo_children():
                self._update_widget_font_recursive(widget, font, ['Label', 'Button'])
        except Exception as e:
            print(f"[ERROR] 更新使用說明標籤頁字體時發生錯誤: {e}")
    
    def update_fixture_tab_fonts(self, fixture_ui, size):
        """更新治具控制標籤頁的UI字體"""
        try:
            font = (self.ui_font_family, int(size))
            # 更新治具控制標籤頁中的所有標籤和按鈕
            if hasattr(fixture_ui, 'parent_frame'):
                for widget in fixture_ui.parent_frame.winfo_children():
                    self._update_widget_font_recursive(widget, font, ['Label', 'Button'])
        except Exception as e:
            print(f"[ERROR] 更新治具控制標籤頁字體時發生錯誤: {e}")
    
    def update_settings_tab_content_fonts(self, settings_ui, size):
        """更新設定標籤頁的內容字體"""
        try:
            font = (self.content_font_family, int(size))
            # 更新設定標籤頁中的輸入框和下拉選單
            for widget in settings_ui.parent_frame.winfo_children():
                self._update_widget_font_recursive(widget, font, ['Entry', 'Combobox', 'Text'])
        except Exception as e:
            print(f"[ERROR] 更新設定標籤頁內容字體時發生錯誤: {e}")
    
    def update_dos_tab_content_fonts(self, dos_ui, size):
        """更新DOS標籤頁的內容字體"""
        try:
            font = (self.content_font_family, int(size))
            # 更新DOS標籤頁中的文字區域
            for widget in dos_ui.parent_frame.winfo_children():
                self._update_widget_font_recursive(widget, font, ['Entry', 'Text'])
        except Exception as e:
            print(f"[ERROR] 更新DOS標籤頁內容字體時發生錯誤: {e}")
    
    def update_guide_tab_content_fonts(self, guide_ui, size):
        """更新使用說明標籤頁的內容字體"""
        try:
            font = (self.content_font_family, int(size))
            # 更新使用說明標籤頁中的文字區域
            for widget in guide_ui.parent_frame.winfo_children():
                self._update_widget_font_recursive(widget, font, ['Text'])
        except Exception as e:
            print(f"[ERROR] 更新使用說明標籤頁內容字體時發生錯誤: {e}")
    
    def update_fixture_tab_content_fonts(self, fixture_ui, size):
        """更新治具控制標籤頁的內容字體"""
        try:
            font = (self.content_font_family, int(size))
            # 更新治具控制標籤頁中的輸入框和文字區域
            if hasattr(fixture_ui, 'parent_frame'):
                for widget in fixture_ui.parent_frame.winfo_children():
                    self._update_widget_font_recursive(widget, font, ['Entry', 'Combobox', 'Text'])
        except Exception as e:
            print(f"[ERROR] 更新治具控制標籤頁內容字體時發生錯誤: {e}")
    
    def _update_widget_font_recursive(self, widget, font, widget_types):
        """遞歸更新widget及其子widget的字體"""
        try:
            widget_class = widget.winfo_class()
            if any(wtype in widget_class for wtype in widget_types):
                try:
                    widget.config(font=font)
                except:
                    pass
            
            # 遞歸處理子widget
            for child in widget.winfo_children():
                self._update_widget_font_recursive(child, font, widget_types)
        except Exception as e:
            pass  # 忽略錯誤，繼續處理其他widget
