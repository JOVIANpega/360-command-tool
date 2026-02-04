# -*- coding: utf-8 -*-

import subprocess


import platform


from tkinter import messagebox


import json


from datetime import datetime


import os


import tkinter as tk


import threading


import logging


from config_utils import get_notification_text, get_app_version


from config_core import COMMAND_FILE, GUIDE_FILE, save_setup, list_com_ports, load_setup





class UIHandlersCore:


    def __init__(self, parent, setup, highlight_keywords=None):


        self.parent = parent


        self.setup = setup


        self.countdown_job = None


        self._progress_update_job = None  # 進度條更新任務


        # 初始化 component_label_map，用於記錄標籤對應的索引


        self.component_label_map = {}


        # 獲取高亮關鍵字


        self.highlight_keywords = highlight_keywords or {}


        if hasattr(parent, 'highlight_keywords'):


            self.highlight_keywords = parent.highlight_keywords


            print(f"[DEBUG] UIHandlers: 從 parent 獲取了 {len(self.highlight_keywords)} 個高亮關鍵字")


        # 解析指令文件中的分類和指令


        self.parse_commands_by_section()


        


    def reload_setup(self, new_setup):


        """重新載入設定"""


        self.setup = new_setup


        logging.debug("[DEBUG] UIHandlersCore setup reloaded.")


        


    def parse_commands_by_section(self):


        """解析命令文件，按區段整理"""


        # 決定指令檔路徑


        # 從設定中讀取路徑，確保每次都重新載入設定以獲取最新的路徑


        self.setup = self.parent.config.load_setup()


        command_file_from_setup = self.setup.get("DUT_Control", {}).get("Command_File_Path", "")


        print(f"[DEBUG] parse_commands_by_section: Read Command_File_Path='{command_file_from_setup}' from setup.")


        if command_file_from_setup and os.path.isfile(command_file_from_setup):


            command_path = command_file_from_setup


            print(f"[INFO] 使用者自訂指令檔: {command_path}")


        else:


            command_path = COMMAND_FILE # config_core 中的預設路徑


            print(f"[INFO] 使用預設指令檔: {command_path}")


        commands = {}


        section = "全部指令"  # 預設區段


        


        print("[DEBUG] 開始解析指令文件")

        try:


            with open(command_path, "r", encoding="utf-8") as file:


                for line in file:


                    line = line.strip()


                    if not line or line.startswith("#") or line.startswith("//"):


                        continue


                    


                    # 檢查是否為區段標記


                    if line.startswith("==") and line.endswith("=="):


                        section = line.strip("=").strip()


                        if section not in commands:


                            commands[section] = {}


                            print(f"[DEBUG] 發現新區段：{section}")


                        continue


                    


                    # 解析命令


                    parts = line.split("=", 1)


                    if len(parts) >= 2:


                        label = parts[0].strip()


                        command = parts[1].strip()


                        


                        # 檢查是否有顏色標記


                        has_color = '[COLOR:' in label


                        if has_color:


                            print(f"[DEBUG] 發現帶顏色標記的指令：{label}")


                        


                        # 將命令添加到當前區段


                        commands.setdefault(section, {})[label] = command


                        


                        # 不再自動添加到「全部指令」區段，因為我們已經在 command.txt 中維護了完整的全部指令列表


                        # 這樣避免重複添加


        except Exception as e:


            print(f"[ERROR] 解析指令文件時發生錯誤：{e}")


            import traceback


            traceback.print_exc()


            commands = {"全部指令": {}}


        


        # 將解析結果保存到實例變量中
        self.commands = commands
        
        # 確保父組件也有最新的指令列表 (供 run_script_click 使用)
        if hasattr(self.parent, 'commands_by_section'):
            self.parent.commands_by_section = commands
            print("[DEBUG] 已更新 parent.commands_by_section")
        else:
            # 如果父組件沒有該屬性，則動態添加
            self.parent.commands_by_section = commands
            print("[DEBUG] 已動態添加 parent.commands_by_section")

        # 計算並輸出每個區段的指令數量
        for section, cmds in commands.items():
            print(f"[DEBUG] 區段 '{section}' 有 {len(cmds)} 個指令")

        # 返回解析結果
        return commands


    def update_cmd_list(self):


        section = self.parent.components.section_var.get()


        


        # 檢查選擇的分類是否存在


        if section not in self.parent.commands_by_section:


            print(f"[WARNING] 選擇的分類 '{section}' 不存在，使用全部指令")


            section = '全部指令'


            self.parent.components.section_var.set('全部指令')


            


            # 顯示特定區段的指令


            self.parent.components.combobox_cmd['values'] = list(self.parent.commands_by_section.get(section, {}).keys())


        


        # 如果有指令，選擇第一個


        if self.parent.components.combobox_cmd['values']:


            self.parent.components.combobox_cmd.set(self.parent.components.combobox_cmd['values'][0])


        else:


            self.parent.components.combobox_cmd.set('')





    def refresh_com_ports(self):
        """刷新 COM 口列表"""
        # 列出所有可用的 COM 口
        ports = list_com_ports()
        print(f"[DEBUG] 找到 {len(ports)} 個COM口: {ports}")
        
        # 清空當前選擇
        self.parent.components.combobox_com.set('')
        self.parent.components.combobox_com['values'] = []
        
        if not ports:
            # 沒有 COM 口時顯示通知
            self.parent.components.show_notification(get_notification_text("no_ports"), "red", 3000)
            return
            
        # 設置 COM 口下拉選單的值
        self.parent.components.combobox_com['values'] = ports
        
        # 如果有保存的設定，使用設定中的 COM 口
        saved_com = self.setup.get('DUT_Control', {}).get('Serial_COM_Port', '')
        if saved_com and saved_com in ports:
            self.parent.components.combobox_com.set(saved_com)
            print(f"[DEBUG] refresh_com_ports: 保持選擇 {saved_com}")
        else:
            # 選擇第一個 COM 口
            self.parent.components.combobox_com.set(ports[0])
            print(f"[DEBUG] refresh_com_ports: 選擇第一個 COM 口 {ports[0]}")
            # 更新設定並立即保存
            if 'DUT_Control' not in self.setup:
                self.setup['DUT_Control'] = {}
            self.setup['DUT_Control']['Serial_COM_Port'] = ports[0]
            # 立即保存COM口設定
            save_setup(self.setup, manual_save=True)
            print(f"[DEBUG] refresh_com_ports: COM口設定已保存到 setup.json")
    
    def on_com_port_changed(self, event=None):
        """當COM口選擇變更時立即保存設定"""
        try:
            selected_com = self.parent.components.combobox_com.get()
            if selected_com and selected_com != '無可用COM口':
                # 更新設定
                if 'DUT_Control' not in self.setup:
                    self.setup['DUT_Control'] = {}
                self.setup['DUT_Control']['Serial_COM_Port'] = selected_com
                
                # 立即保存設定
                save_setup(self.setup, manual_save=True)
                print(f"[DEBUG] on_com_port_changed: COM口已變更為 {selected_com} 並保存到 setup.json")
                
                # 顯示通知
                if hasattr(self.parent, 'components') and hasattr(self.parent.components, 'show_notification'):
                    self.parent.components.show_notification(f"COM口已設定為: {selected_com}", "green", 2000)
        except Exception as e:
            print(f"[ERROR] 保存COM口設定時發生錯誤: {e}")
            import traceback
            traceback.print_exc()


    def clear_output(self, event=None):
        """清空輸出區域"""
        if hasattr(self.parent.components, 'text_output'):
            self.parent.components.text_output.configure(state='normal')
            self.parent.components.text_output.delete(1.0, tk.END)
            self.parent.components.text_output.configure(state='disabled')
            # 如果有圖片ID，需要先刪除所有圖片標籤，以避免內存洩漏
            if hasattr(self.parent.components, 'image_refs'):
                self.parent.components.image_refs = []
            # 顯示清空通知
            self.parent.components.show_notification(get_notification_text("output_cleared"), "blue", 2000)

    def backup_output(self):
        """備份輸出內容到檔案"""


        try:


            # 獲取當前輸出內容


            content = self.parent.components.text_output.get(1.0, tk.END)


            


            # 生成備份檔名


            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')


            backup_file = f"backup/backup_{timestamp}.txt"


            


            # 寫入備份檔


            with open(backup_file, 'w', encoding='utf-8') as f:


                f.write(content)


                


            # 顯示通知


            self.parent.components.show_notification(f"已備份輸出內容至: {backup_file}", "green", 3000)


        except Exception as e:


            print(f"[ERROR] 備份輸出內容時發生錯誤: {e}")


            self.parent.components.show_notification(f"備份失敗: {e}", "red", 3000) 