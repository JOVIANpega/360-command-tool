# -*- coding: utf-8 -*-
"""
命令處理器模組
負責處理命令解析、執行和相關邏輯
"""

import os
import threading
from datetime import datetime
from config_core import COMMAND_FILE, save_setup, load_setup

# 使用重構版本的 worker (V2)
from transport.serial_worker_v2 import SerialWorkerV2
from transport.adb_worker_v2 import ADBWorkerV2


class CommandProcessor:
    """命令處理器類別，負責命令的解析和執行"""
    
    def __init__(self, parent):
        """
        初始化命令處理器
        
        Args:
            parent: 父級UI元件
        """
        self.parent = parent
        self.setup = parent.setup
        self.commands_by_section = {}
        self.serial_worker = None
        self.adb_worker = None
        self.last_read_path = ""

    def get_last_read_path(self):
        """獲取最後一次讀取的指令檔案路徑"""
        return self.last_read_path


    def parse_commands_by_section(self):
        """解析命令文件，按區段整理"""
        self.commands_by_section = {}
        
        try:
            # 決定使用哪個指令檔案
            command_file_path = COMMAND_FILE
            
            # 嘗試從設定中讀取
            if hasattr(self, 'setup') and self.setup:
                custom_path = self.setup.get('DUT_Control', {}).get('Command_File_Path', '')
                if custom_path and os.path.exists(custom_path):
                    command_file_path = custom_path
                    print(f"[DEBUG] 使用自訂指令檔案: {command_file_path}")
            
            self.last_read_path = command_file_path


            
            # 檢查命令文件是否存在
            if not os.path.exists(command_file_path):
                print(f"命令文件不存在: {command_file_path}")
                return {"全部指令": {}}
            
            with open(command_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"[DEBUG] 讀取指令檔案成功: {os.path.abspath(command_file_path)}")
            if lines:
                print(f"[DEBUG] 檔案前 3 行: {lines[:3]}")
            
            current_section = "未分類"
            self.commands_by_section = {"全部指令": {}}
            
            for line in lines:
                line = line.strip()
                # 跳過空行或註解行 (#, ;, //)
                if not line or line.startswith('#') or line.startswith(';') or line.startswith('//'):
                    continue
                
                # 檢查是否為區段標題
                header_match = False
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1].strip()
                    header_match = True
                elif line.startswith('=') and line.endswith('=') and line.count('=') >= 2:
                    # 至少要有兩個等號 (例如 ==Section== 或 ===Section===)
                    current_section = line.strip('=').strip()
                    header_match = True
                
                if header_match:
                    if not current_section: 
                        current_section = "未命名分類"
                    if current_section not in self.commands_by_section:
                        self.commands_by_section[current_section] = {}
                else:
                    # 這是一個命令
                    if current_section not in self.commands_by_section:
                         self.commands_by_section[current_section] = {}
                    
                    # 決定分段符號
                    main_sep = self.setup.get('DUT_Control', {}).get('Command_Separator', '=')
                    
                    found_sep = None
                    if main_sep in line:
                        found_sep = main_sep
                    elif '=' in line:
                        found_sep = '='
                    
                    if found_sep:
                        parts = line.split(found_sep, 1)
                        cmd_name = parts[0].strip()
                        cmd_value = parts[1].strip()
                        
                        # 清理開頭的分隔符號殘留 (如 =>, ==>, ### 等)
                        # 如果符號是 ==> 或 =，則清理 = 和 >
                        # 如果符號是 ##，則清理 #
                        chars_to_strip = "=>" if "=" in found_sep or ">" in found_sep else ""
                        chars_to_strip += found_sep.strip()
                        
                        while cmd_value and any(cmd_value.startswith(c) for c in chars_to_strip):
                            cmd_value = cmd_value[1:].strip()
                            
                        if cmd_name:
                            self.commands_by_section[current_section][cmd_name] = cmd_value
                            # 同步到全部指令
                            self.commands_by_section["全部指令"][cmd_name] = cmd_value
                    else:
                        # 純指令名稱與指令相同
                        cmd_name = line.strip()
                        self.commands_by_section[current_section][cmd_name] = cmd_name
                        # 同步到全部指令
                        self.commands_by_section["全部指令"][cmd_name] = cmd_name
            
            # 將結果同步到 parent 以確保 UIHandlers 可以讀取到完整的對應關係
            if hasattr(self.parent, 'commands_by_section'):
                self.parent.commands_by_section = self.commands_by_section
            
            print(f"[DEBUG] 解析到 {len(self.commands_by_section)} 個區段")
            for section, commands in self.commands_by_section.items():
                print(f"[DEBUG] 區段 '{section}': {len(commands)} 個命令")
                
            return self.commands_by_section
                
        except Exception as e:
            print(f"解析命令文件時發生錯誤: {e}")
            return {}
    
    def get_sections(self):
        """獲取所有區段名稱"""
        return list(self.commands_by_section.keys())
    
    def get_commands_for_section(self, section):
        """獲取指定區段的命令列表"""
        return self.commands_by_section.get(section, [])
    
    def update_cmd_list(self, section_var, cmd_var):
        """更新命令列表"""
        section = section_var.get()
        
        # 獲取該區段的命令
        commands = self.get_commands_for_section(section)
        
        # 更新命令下拉選單
        if hasattr(self.parent.components, 'combobox_cmd'):
            self.parent.components.combobox_cmd['values'] = commands
            
            # 如果有命令，設定第一個為預設值
            if commands:
                if cmd_var.get() not in commands:
                    cmd_var.set(commands[0])
            else:
                cmd_var.set("")
        
        print(f"[DEBUG] 區段 '{section}' 包含 {len(commands)} 個命令")
    
    def execute_command(self, com_port, command, timeout, end_string, on_data_callback, on_finish_callback, transport_mode="Console"):
        """
        執行命令

        Args:
            com_port: COM端口 (僅在 Console 模式使用)
            command: 要執行的命令
            timeout: 超時時間
            end_string: 結束字符串
            on_data_callback: 數據接收回調函數
            on_finish_callback: 完成回調函數
            transport_mode: 傳輸模式 ("Console" 或 "ADB")
        """
        try:
            # 檢查是否已有工作器在運行
            if (self.serial_worker and self.serial_worker.is_alive()) or (self.adb_worker and self.adb_worker.is_alive()):
                print("[WARNING] 已有命令在執行中")
                return False

            if transport_mode == "ADB":
                # 使用 ADB 模式
                print(f"[DEBUG] 使用 ADB 模式執行命令: {command}")

                # 分割指令 - 使用設定中的間隔符號
                separator = self.setup.get('DUT_Control', {}).get('Command_Separator', '|')
                cmd_list = command.split(separator)

                # 獲取單個指令超時時間和間隔
                try:
                    cmd_timeout = float(self.setup.get('DUT_Control', {}).get('Single_Command_Timeout', 30.0))
                    cmd_interval = float(self.setup.get('DUT_Control', {}).get('Command_Interval', 1.0))
                except (ValueError, TypeError):
                    cmd_timeout = 30.0
                    cmd_interval = 1.0

                # 創建新的 ADB 工作器 (使用 V2)
                self.adb_worker = ADBWorkerV2(
                    cmd_list=cmd_list,
                    end_str=end_string,
                    timeout=timeout,
                    on_data=on_data_callback,
                    on_status=lambda connected: None,  # ADB 不需要狀態燈
                    on_progress=lambda p: None,  # 進度由外部處理
                    on_finish=on_finish_callback,
                    stop_event=self.parent.stop_event,
                    cmd_timeout=cmd_timeout,
                    cmd_interval=cmd_interval
                )

                # 啟動 ADB 工作器
                self.adb_worker.start()

            else:
                # 使用 Console 模式 (原有邏輯)
                print(f"[DEBUG] 使用 Console 模式執行命令: {command}")

                # 分割指令 - 使用設定中的間隔符號
                separator = self.setup.get('DUT_Control', {}).get('Command_Separator', '|')
                cmd_list = command.split(separator)
                
                # 去除每個指令的多餘空白
                cmd_list = [c.strip() for c in cmd_list if c.strip()]

                # 獲取單個指令超時時間和間隔
                try:
                    cmd_timeout = float(self.setup.get('DUT_Control', {}).get('Single_Command_Timeout', 10.0))
                    cmd_interval = float(self.setup.get('DUT_Control', {}).get('Command_Interval', 1.0))
                except (ValueError, TypeError):
                    cmd_timeout = 10.0
                    cmd_interval = 1.0

                # 創建新的串口工作器 (使用 V2)
                self.serial_worker = SerialWorkerV2(
                    com=com_port,
                    cmd_list=cmd_list,  # 傳遞拆分後的列表
                    end_str=end_string,
                    timeout=timeout,
                    on_data=on_data_callback,
                    on_status=lambda connected: None,
                    on_progress=lambda p: None,
                    on_finish=on_finish_callback,
                    stop_event=self.parent.stop_event,
                    cmd_timeout=cmd_timeout,
                    cmd_interval=cmd_interval
                )

                # 啟動串口工作器
                self.serial_worker.start()

            return True

        except Exception as e:
            print(f"執行命令時發生錯誤: {e}")
            return False
    
    def stop_command(self):
        """停止當前執行的命令"""
        try:
            stopped = False

            # 停止串口工作器
            if self.serial_worker and self.serial_worker.is_alive():
                # 設置停止事件
                self.parent.stop_event.set()

                # 等待工作器結束
                self.serial_worker.join(timeout=2.0)

                if self.serial_worker.is_alive():
                    print("[WARNING] 串口工作器未能正常結束")
                else:
                    print("[DEBUG] 串口命令執行已停止")

                stopped = True

            # 停止 ADB 工作器
            if self.adb_worker and self.adb_worker.is_alive():
                # 設置停止事件
                self.parent.stop_event.set()

                # 等待工作器結束
                self.adb_worker.join(timeout=2.0)

                if self.adb_worker.is_alive():
                    print("[WARNING] ADB 工作器未能正常結束")
                else:
                    print("[DEBUG] ADB 命令執行已停止")

                stopped = True

            if stopped:
                # 清除停止事件
                self.parent.stop_event.clear()
                return True
            else:
                print("[DEBUG] 沒有正在執行的命令")
                return False

        except Exception as e:
            print(f"停止命令時發生錯誤: {e}")
            return False
    
    def is_command_running(self):
        """檢查是否有命令正在執行"""
        return (self.serial_worker and self.serial_worker.is_alive()) or (self.adb_worker and self.adb_worker.is_alive())
    
    def ping_device(self, com_port, timeout, on_data_callback, on_finish_callback):
        """
        Ping設備
        
        Args:
            com_port: COM端口
            timeout: 超時時間
            on_data_callback: 數據接收回調函數
            on_finish_callback: 完成回調函數
        """
        try:
            # 使用空命令進行ping測試
            ping_command = ""
            
            return self.execute_command(
                com_port=com_port,
                command=ping_command,
                timeout=timeout,
                end_string="",
                on_data_callback=on_data_callback,
                on_finish_callback=on_finish_callback
            )
            
        except Exception as e:
            print(f"Ping設備時發生錯誤: {e}")
            return False
    
    def validate_command_parameters(self, com_port, command, timeout):
        """
        驗證命令參數
        
        Args:
            com_port: COM端口
            command: 命令
            timeout: 超時時間
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # 檢查COM端口
            if not com_port or com_port.strip() == "":
                return False, "請選擇COM端口"
            
            # 檢查命令
            if not command or command.strip() == "":
                return False, "請選擇要執行的命令"
            
            # 檢查超時時間
            try:
                timeout_value = float(timeout)
                if timeout_value <= 0:
                    return False, "超時時間必須大於0"
                if timeout_value > 300:  # 最大5分鐘
                    return False, "超時時間不能超過300秒"
            except ValueError:
                return False, "超時時間必須是有效的數字"
            
            return True, ""
            
        except Exception as e:
            return False, f"參數驗證時發生錯誤: {e}"
    
    def get_command_history(self):
        """獲取命令執行歷史"""
        try:
            setup = load_setup()
            return setup.get('command_history', [])
        except Exception as e:
            print(f"獲取命令歷史時發生錯誤: {e}")
            return []
    
    def save_command_to_history(self, com_port, command, result):
        """
        保存命令到歷史記錄
        
        Args:
            com_port: COM端口
            command: 執行的命令
            result: 執行結果
        """
        try:
            setup = load_setup()
            
            # 獲取現有歷史記錄
            history = setup.get('command_history', [])
            
            # 創建新的歷史記錄項目
            history_item = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'com_port': com_port,
                'command': command,
                'result': result[:100] if len(result) > 100 else result  # 限制結果長度
            }
            
            # 添加到歷史記錄開頭
            history.insert(0, history_item)
            
            # 限制歷史記錄數量（最多保留50條）
            if len(history) > 50:
                history = history[:50]
            
            # 保存回設定檔
            setup['command_history'] = history
            save_setup(setup)
            
            print(f"[DEBUG] 命令已保存到歷史記錄")
            
        except Exception as e:
            print(f"保存命令歷史時發生錯誤: {e}")
    
    def clear_command_history(self):
        """清除命令執行歷史"""
        try:
            setup = load_setup()
            setup['command_history'] = []
            save_setup(setup)
            print("[DEBUG] 命令歷史已清除")
            return True
        except Exception as e:
            print(f"清除命令歷史時發生錯誤: {e}")
            return False
