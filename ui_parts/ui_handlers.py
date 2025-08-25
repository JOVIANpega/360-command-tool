# -*- coding: utf-8 -*-
"""
UI事件處理器模組 - 重構版本
負責處理UI事件和用戶交互，已將字體管理和命令處理分離到專門的模組
"""

import subprocess
import platform
from tkinter import messagebox, scrolledtext, simpledialog
import json
from datetime import datetime
import os
import tkinter as tk
import tkinter.ttk as ttk
import threading

from config_utils import get_notification_text, get_app_version
from config_core import COMMAND_FILE, GUIDE_FILE, save_setup, list_com_ports, load_setup
from serial_worker import SerialWorker
from ui_parts.ui_handlers_core import UIHandlersCore
from ui_parts.font_manager import FontManager
from ui_parts.command_processor import CommandProcessor





class UIHandlers(UIHandlersCore):


    def __init__(self, parent, setup, highlight_keywords=None):
        """初始化UI事件處理器 - 重構版本"""
        super().__init__(parent, setup, highlight_keywords)

        self.parent = parent
        self.setup = setup
        self.countdown_job = None
        self._progress_update_job = None  # 進度條更新任務

        # 初始化專門的管理器
        self.font_manager = FontManager(parent)
        self.command_processor = CommandProcessor(parent)

        # 初始化 component_label_map，用於記錄標籤對應的索引
        self.component_label_map = {}

        # 獲取高亮關鍵字
        self.highlight_keywords = {}
        if hasattr(parent, 'highlight_keywords'):
            self.highlight_keywords = parent.highlight_keywords
            print(f"[DEBUG] UIHandlers: 從 parent 獲取了 {len(self.highlight_keywords)} 個高亮關鍵字")

        # 初始化通知管理器
        if hasattr(parent, 'notification_manager'):
            self.notification_manager = parent.notification_manager
        else:
            self.notification_manager = None

        # 初始化狀態
        self.is_guide_showing = False
        self.original_output_content = ""

        # 解析指令文件中的分類和指令（使用命令處理器）
        self.command_processor.parse_commands_by_section()





    # parse_commands_by_section 方法已移至 CommandProcessor

    def _get_command_file_path(self):
        """獲取指令檔路徑 - 重構輔助函數"""
        command_file_from_setup = self.setup.get("DUT_Control", {}).get("Command_File_Path", "")

        if command_file_from_setup and os.path.isfile(command_file_from_setup):
            command_path = command_file_from_setup
            print(f"[INFO] 使用者自訂指令檔: {command_path}")
        else:
            command_path = COMMAND_FILE  # 使用預設路徑
            print(f"[INFO] 使用預設指令檔: {command_path}")

        return command_path

    def _parse_command_line(self, line, section, commands):
        """解析單行指令 - 重構輔助函數"""
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            return section

        # 檢查是否為區段標記
        if line.startswith("==") and line.endswith("=="):
            section = line.strip("=").strip()
            if section not in commands:
                commands[section] = {}
                print(f"[DEBUG] 發現新區段：{section}")
            return section

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

        return section

    def _print_commands_summary(self, commands):
        """輸出指令摘要 - 重構輔助函數"""
        for section_name, section_cmds in commands.items():
            print(f"[DEBUG] 區段 '{section_name}' 有 {len(section_cmds)} 個指令")

            # 檢查顏色標記
            color_cmds = [cmd for cmd in section_cmds.keys() if '[COLOR:' in cmd]
            if color_cmds:
                print(f"[DEBUG] 區段 '{section_name}' 有 {len(color_cmds)} 個帶顏色標記的指令")
                for cmd in color_cmds:
                    print(f"[DEBUG] - {cmd}")

    def _legacy_parse_commands_by_section(self):


        """解析命令文件，按區段整理"""


        commands = {}


        section = "全部指令"  # 預設區段





        print("[DEBUG] 開始解析指令文件")





        try:


            # 從設定中讀取指令檔路徑


            command_file_from_setup = self.setup.get("DUT_Control", {}).get("Command_File_Path", "")





            # 決定使用哪個指令檔路徑


            if command_file_from_setup and os.path.isfile(command_file_from_setup):


                command_path = command_file_from_setup


                print(f"[INFO] 使用者自訂指令檔: {command_path}")


            else:


                command_path = COMMAND_FILE  # 使用預設路徑


                print(f"[INFO] 使用預設指令檔: {command_path}")







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


            print(f"[ERROR] 讀取命令文件時發生錯誤: {e}")


            import traceback


            traceback.print_exc()





            # 如果讀取失敗，提供一個預設命令


            if "全部指令" not in commands or not commands["全部指令"]:


                commands["全部指令"] = {"執行重啟 (預設命令)": "reboot"}





        # 輸出各區段指令數量


        for section_name, section_cmds in commands.items():


            print(f"[DEBUG] 區段 '{section_name}' 有 {len(section_cmds)} 個指令")


            # 檢查顏色標記


            color_cmds = [cmd for cmd in section_cmds.keys() if '[COLOR:' in cmd]


            if color_cmds:


                print(f"[DEBUG] 區段 '{section_name}' 有 {len(color_cmds)} 個帶顏色標記的指令")


                for cmd in color_cmds:


                    print(f"[DEBUG] - {cmd}")





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





    def on_ping(self):
        """Ping 按鈕點擊事件處理：只執行串流 Ping，不再保存IP歷史（IP管理已移至設定頁）"""
        # 執行串流 Ping（輸出到右側視窗）
        self.check_ping()





    def save_ip_to_history(self):
        """保存當前IP地址到歷史記錄並寫入setup.json"""
        try:
            current_ip = self.parent.components.entry_ip.get().strip()
            if not current_ip:
                self.parent.components.show_notification("請先輸入IP地址", "warning", 3000)
                return
            
            # 載入當前設定
            from config_core import load_setup, save_setup
            setup = load_setup()
            
            # 讀取頂層 IP_History（優先），相容舊版從 DUT_Control 讀取
            ip_history = setup.get('IP_History')
            if ip_history is None:
                ip_history = setup.get('DUT_Control', {}).get('IP_History', [])
            
            # 去重並置頂
            if current_ip in ip_history:
                ip_history.remove(current_ip)
            ip_history.insert(0, current_ip)
            # 限制 20 筆
            if len(ip_history) > 20:
                ip_history = ip_history[:20]
            
            # 寫回頂層 IP_History，並相容性同步到 DUT_Control
            setup['IP_History'] = ip_history
            if 'DUT_Control' not in setup:
                setup['DUT_Control'] = {}
            setup['DUT_Control']['IP_History'] = ip_history
            
            save_setup(setup, manual_save=True)
            
            self.parent.components.show_notification(f"IP地址 {current_ip} 已保存到歷史", "green", 3000)
            print(f"[INFO] IP地址已保存: {current_ip}")
                
        except Exception as e:
            print(f"[ERROR] 保存IP地址時發生錯誤: {e}")
            self.parent.components.show_notification("保存IP地址失敗", "error", 3000)

    def remove_ip_from_history(self):
        """從歷史記錄中移除當前IP地址"""
        try:
            current_ip = self.parent.components.entry_ip.get().strip()
            if not current_ip:
                self.parent.components.show_notification("請先輸入要移除的IP地址", "warning", 3000)
                return
            
            # 載入當前設定
            from config_core import load_setup, save_setup
            setup = load_setup()
            
            # 確保DUT_Control存在
            if 'DUT_Control' not in setup:
                setup['DUT_Control'] = {}
            
            # 獲取IP歷史記錄
            ip_history = setup['DUT_Control'].get('IP_History', [])
            
            # 如果IP在歷史中，移除它
            if current_ip in ip_history:
                ip_history.remove(current_ip)
                setup['DUT_Control']['IP_History'] = ip_history
                save_setup(setup, manual_save=True)
                
                self.parent.components.show_notification(f"IP地址 {current_ip} 已從歷史中移除", "green", 3000)
                print(f"[INFO] IP地址已移除: {current_ip}")
            else:
                self.parent.components.show_notification("IP地址不在歷史記錄中", "info", 3000)
                
        except Exception as e:
            print(f"[ERROR] 移除IP地址時發生錯誤: {e}")
            self.parent.components.show_notification("移除IP地址失敗", "error", 3000)

    def check_ping(self):


        print("check_ping called")


        # 如果已經在 PING，則終止


        if hasattr(self, 'ping_thread') and self.ping_thread is not None and self.ping_thread.is_alive():


            self.ping_stop = True


            if hasattr(self, 'ping_process') and self.ping_process is not None:


                try:


                    if self.ping_process.poll() is None:


                        self.ping_process.terminate()


                    self.parent.components.add_to_buffer("\n[Ping 已中止]\n", "error")


                except Exception as e:


                    self.parent.components.add_to_buffer(f"\n[Ping 終止失敗: {e}]\n", "error")


            self.parent.components.btn_ping.config(text='Ping')


            self.ping_process = None


            # 停止啟動標籤閃爍
            if hasattr(self.parent.components, 'startup_label_manager'):
                self.parent.components.startup_label_manager.stop_blink()


            # ping 結束時重置進度條


            self.parent.components.reset_progress()


            return


        # 定義 ping 工作函數


        def ping_worker():


            print("ping_worker started")


            try:


                # 從設定中獲取預設IP地址，使用正確的鍵名


                dut_control = self.parent.setup.get('DUT_Control', {})
                default_ip = dut_control.get('Default_IP_Address', '192.168.11.143')


                ip = self.parent.components.entry_ip.get().strip() or default_ip





                # 確保進度條已初始化


                if hasattr(self.parent.components, 'progress'):


                    self.parent.components.progress.config(style="blue.Horizontal.TProgressbar", value=0)





                # 更新狀態燈


                self.update_status_light(False)





                # 根據作業系統設定 ping 參數


                param = '-n' if platform.system().lower() == 'windows' else '-c'


                command = ['ping', param, '4', '-w', '1000', ip]





                self.ping_stop = False


                self.parent.components.btn_ping.config(text='中止PING')


                self.parent.components.add_to_buffer(f"\n=== 開始 Ping {ip} ===\n", "success")


                # 開始啟動標籤閃爍
                if hasattr(self.parent.components, 'startup_label_manager'):
                    self.parent.components.startup_label_manager.start_blink()


                self.parent.root.update_idletasks()





                # 設定 Windows 下隱藏命令視窗


                startupinfo = None


                if platform.system().lower() == 'windows':


                    startupinfo = subprocess.STARTUPINFO()


                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW


                    startupinfo.wShowWindow = subprocess.SW_HIDE





                # 執行 ping 命令


                self.ping_process = subprocess.Popen(


                    command,


                    stdout=subprocess.PIPE,


                    stderr=subprocess.PIPE,


                    text=True,


                    bufsize=1,


                    universal_newlines=True,


                    startupinfo=startupinfo


                )





                # 監控 ping 輸出


                total_packets = 4


                received_packets = 0


                last_progress = 0





                while True:


                    if self.ping_stop:


                        break





                    output = self.ping_process.stdout.readline()


                    if output == '' and self.ping_process.poll() is not None:


                        break





                    if output:


                        # 使用 lambda 函數來確保變數被正確捕獲


                        output_copy = output  # 創建一個副本


                        self.parent.root.after(0, lambda o=output_copy: self.parent.components.add_to_buffer(o, "error" if ("請求超時" in o or "無法連線" in o or "失敗" in o) else None))





                        # 更新進度


                        if "位元組" in output and "時間" in output or "請求超時" in output or "無法連線" in output or "失敗" in output:


                            received_packets += 1


                            progress = (received_packets / total_packets) * 100


                            if progress != last_progress:


                                progress_copy = progress  # 創建一個副本


                                self.parent.root.after(0, lambda p=progress_copy: self.parent.components.progress.config(value=p))


                                last_progress = progress





                # 處理錯誤輸出


                error = self.ping_process.stderr.read()


                if error:


                    self.parent.root.after(0, lambda: self.parent.components.add_to_buffer(error, "error"))





                # 根據 ping 結果更新狀態


                return_code = self.ping_process.poll()


                if not self.ping_stop and return_code == 0:


                    self.parent.root.after(0, lambda: self.parent.components.add_to_buffer("\nPing 成功！\n", "success"))


                    self.parent.root.after(0, lambda: self.update_status_light(True))


                elif not self.ping_stop:


                    self.parent.root.after(0, lambda: self.parent.components.add_to_buffer("\nPing 失敗！\n", "error"))


                    self.parent.root.after(0, lambda: self.update_status_light(False))





            except Exception as e:


                self.parent.root.after(0, lambda e=e: self.parent.components.add_to_buffer(f"Ping 執行錯誤: {str(e)}\n", "error"))


                self.parent.root.after(0, lambda: self.update_status_light(False))


                import traceback


                traceback.print_exc()


            finally:


                # ping 結束時重置進度條和按鈕


                self.parent.root.after(0, lambda: self.parent.components.reset_progress())


                self.parent.root.after(0, lambda: self.parent.components.btn_ping.config(text='Ping'))


                # 停止啟動標籤閃爍
                if hasattr(self.parent.components, 'startup_label_manager'):
                    self.parent.root.after(0, lambda: self.parent.components.startup_label_manager.stop_blink())


                self.ping_process = None





        # 創建並啟動 ping 執行緒


        import threading


        self.ping_thread = threading.Thread(target=ping_worker)


        self.ping_thread.daemon = True


        self.ping_thread.start()





    def refresh_com_ports(self):


        """刷新COM口列表並保持當前選擇（如果可能）"""


        try:


            # 保存當前選擇


            current_selection = self.parent.components.combobox_com.get()





            # 更新 COM 口列表


            new_ports = list_com_ports()


            self.parent.components.combobox_com['values'] = new_ports





            # 如果當前選擇仍在新列表中，保持選擇


            # 從顯示名稱中提取實際的 COM 口名稱進行比較
            from config_core import extract_com_port_name
            current_actual_port = extract_com_port_name(current_selection) if current_selection else ""

            # 找到匹配的顯示名稱
            matching_display_name = None
            for display_name in new_ports:
                if extract_com_port_name(display_name) == current_actual_port:
                    matching_display_name = display_name
                    break

            if matching_display_name:


                self.parent.components.combobox_com.set(matching_display_name)


                print(f"[DEBUG] refresh_com_ports: 保持選擇 {matching_display_name}")


            elif new_ports:  # 如果有可用的COM口但當前選擇不在列表中


                # 選擇第一個可用的COM口，而不是清空選擇


                # 選擇第一個可用的COM口，而不是清空選擇
                selected_display_name = new_ports[0]
                actual_com_port = extract_com_port_name(selected_display_name)
                self.parent.components.combobox_com.set(selected_display_name)


                print(f"[DEBUG] refresh_com_ports: 當前選擇 '{current_selection}' 不可用，選擇新的COM口 {selected_display_name}")





                # 自動保存新選擇的COM口到設定檔（保存實際的 COM 口名稱）


                if 'DUT_Control' not in self.parent.setup:


                    self.parent.setup['DUT_Control'] = {}


                self.parent.setup['DUT_Control']['Serial_COM_Port'] = actual_com_port





                # 保存完整的設定結構到檔案


                from config_core import load_setup, save_setup


                full_setup = load_setup()


                if 'DUT_Control' not in full_setup:


                    full_setup['DUT_Control'] = {}


                full_setup['DUT_Control']['Serial_COM_Port'] = actual_com_port


                save_setup(full_setup)


            else:


                # 如果沒有可用的COM口，才清空選擇


                self.parent.components.combobox_com.set('')


                print(f"[DEBUG] refresh_com_ports: 沒有可用的COM口，清空選擇")





            # 添加 COM 口更新通知


            if new_ports:


                self.parent.components.show_notification(f"找到 {len(new_ports)} 個 COM 口", "blue", 3000)


            else:


                self.parent.components.show_notification("未找到可用的 COM 口", "red", 3000)


        except Exception as e:


            print(f"[ERROR] refresh_com_ports 發生錯誤: {e}")


            import traceback


            traceback.print_exc()





    def clear_output(self, event=None):


        """清空回應內容視窗，如果正在顯示使用說明，則恢復到正常模式"""


        self.parent.components.text_output.configure(state='normal')


        self.parent.components.text_output.delete('1.0', 'end')


        self.parent.components.text_output.configure(state='disabled')





        # 重置標記
        was_in_special_mode = False

        if hasattr(self.parent, 'showing_guide') and self.parent.showing_guide:
            self.parent.showing_guide = False
            was_in_special_mode = True

        if hasattr(self.parent, 'script_view_mode') and self.parent.script_view_mode:
            self.parent.script_view_mode = False
            was_in_special_mode = True

        # 如果從特殊模式返回，顯示通知
        if was_in_special_mode:
            self.parent.components.show_notification(
                "已清空回應內容，回到測試模式",
                "green", 3000
            )
        else:
            # 正常清空時的通知
            self.parent.components.show_notification(
                get_notification_text("output_cleared"),
                "blue", 2000
            )





    def backup_output(self):


        try:


            backup_dir = 'backup'


            if not os.path.exists(backup_dir):


                os.makedirs(backup_dir)


            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')


            filename = os.path.join(backup_dir, f'backup_{timestamp}.txt')


            content = self.parent.components.text_output.get('1.0', 'end')


            with open(filename, 'w', encoding='utf-8') as f:


                f.write(content)


            # 使用通知功能顯示成功訊息


            self.parent.components.show_notification(


                get_notification_text("backup_success", filename),


                "green", 5000


            )


        except Exception as e:


            # 使用通知功能顯示錯誤訊息


            self.parent.components.show_notification(


                get_notification_text("backup_failed", str(e)),


                "red", 5000


            )





    def on_end_string_entered(self, event):


        new_string = self.parent.components.combobox_end.get().strip()


        if not new_string:


            return


        try:


            end_strings = json.loads(self.parent.setup.get('EndStrings', '["root"]'))


        except Exception:


            end_strings = ['root']


        if new_string not in end_strings:


            end_strings.append(new_string)


            self.parent.setup['EndStrings'] = json.dumps(end_strings, ensure_ascii=False)


            save_setup(self.parent.setup)


            self.parent.components.update_end_strings()


        self.parent.components.combobox_end.set(new_string)





    def change_ui_font_size(self, size):


        try:


            # 限制字體大小在合理範圍內


            size = max(min(int(size), 20), 8)





            # 更新 UI 字體


            self.parent.components.update_ui_fonts(size)





            # 保存設置到DUT_Control和全域設定


            self.parent.setup['UIFontSize'] = str(size)
            if 'DUT_Control' not in self.parent.setup:
                self.parent.setup['DUT_Control'] = {}
            self.parent.setup['DUT_Control']['UI_Font_Size'] = str(size)


            save_setup(self.parent.setup)

            # 通知全域字體管理器更新所有GUI元件
            self.update_global_ui_fonts(size)





            # 強制更新 UI


            self.parent.root.update_idletasks()


            # 同步更新 label_ui_font_value


            if hasattr(self.parent.components, 'label_ui_font_value'):


                self.parent.components.label_ui_font_value.config(text=str(size))


        except Exception as e:


            print(f"更改介面字體大小時發生錯誤: {e}")





    def change_content_font_size(self, size):


        try:


            # 限制字體大小在合理範圍內


            size = max(min(int(size), 20), 8)





            # 更新內容字體


            self.parent.components.update_content_fonts(size)





            # 保存設置到DUT_Control和全域設定


            self.parent.setup['ContentFontSize'] = str(size)
            if 'DUT_Control' not in self.parent.setup:
                self.parent.setup['DUT_Control'] = {}
            self.parent.setup['DUT_Control']['Content_Font_Size'] = str(size)


            save_setup(self.parent.setup)

            # 通知全域字體管理器更新所有GUI元件
            self.update_global_content_fonts(size)





            # 強制更新 UI


            self.parent.root.update_idletasks()


        except Exception as e:


            print(f"更改內容字體大小時發生錯誤: {e}")

    def update_global_ui_fonts(self, size):
        """更新全域UI字體大小"""
        try:
            # 獲取主視窗的TabManager
            root = self.parent.root
            if hasattr(root, 'tab_manager'):
                tab_manager = root.tab_manager

                # 更新全域通知管理器字體
                if hasattr(tab_manager, 'notification_manager'):
                    try:
                        current_font = tab_manager.notification_manager.notification_text.cget("font")
                        if isinstance(current_font, tuple):
                            family, old_size, style = current_font
                        else:
                            family, old_size, style = 'Microsoft JhengHei UI', 12, 'bold'

                        new_font = (family, int(size), style)
                        tab_manager.notification_manager.notification_text.config(font=new_font)
                        print(f"[DEBUG] 全域通知字體已更新為: {new_font}")
                    except Exception as e:
                        print(f"[WARNING] 更新全域通知字體時發生錯誤: {e}")

                # 更新設定標籤頁的字體
                if hasattr(tab_manager, 'settings_ui'):
                    try:
                        settings_ui = tab_manager.settings_ui
                        self.update_settings_tab_fonts(settings_ui, size)
                        print(f"[DEBUG] 設定標籤頁UI字體已更新為: {size}")
                    except Exception as e:
                        print(f"[WARNING] 更新設定標籤頁字體時發生錯誤: {e}")

                # 更新DOS標籤頁的字體
                if hasattr(tab_manager, 'dos_ui'):
                    try:
                        dos_ui = tab_manager.dos_ui
                        self.update_dos_tab_fonts(dos_ui, size)
                        print(f"[DEBUG] DOS標籤頁UI字體已更新為: {size}")
                    except Exception as e:
                        print(f"[WARNING] 更新DOS標籤頁字體時發生錯誤: {e}")

                # 更新使用說明標籤頁的字體
                if hasattr(tab_manager, 'guide_ui'):
                    try:
                        guide_ui = tab_manager.guide_ui
                        self.update_guide_tab_fonts(guide_ui, size)
                        print(f"[DEBUG] 使用說明標籤頁UI字體已更新為: {size}")
                    except Exception as e:
                        print(f"[WARNING] 更新使用說明標籤頁字體時發生錯誤: {e}")

                # 更新治具控制標籤頁的字體
                if hasattr(tab_manager, 'fixture_ui'):
                    try:
                        fixture_ui = tab_manager.fixture_ui
                        self.update_fixture_tab_fonts(fixture_ui, size)
                        print(f"[DEBUG] 治具控制標籤頁UI字體已更新為: {size}")
                    except Exception as e:
                        print(f"[WARNING] 更新治具控制標籤頁字體時發生錯誤: {e}")

        except Exception as e:
            print(f"[ERROR] 更新全域UI字體時發生錯誤: {e}")

    def update_global_content_fonts(self, size):
        """更新全域內容字體大小"""
        try:
            # 獲取主視窗的TabManager
            root = self.parent.root
            if hasattr(root, 'tab_manager'):
                tab_manager = root.tab_manager

                # 更新設定標籤頁的內容字體
                if hasattr(tab_manager, 'settings_ui'):
                    try:
                        settings_ui = tab_manager.settings_ui
                        self.update_settings_tab_content_fonts(settings_ui, size)
                        print(f"[DEBUG] 設定標籤頁內容字體已更新為: {size}")
                    except Exception as e:
                        print(f"[WARNING] 更新設定標籤頁內容字體時發生錯誤: {e}")

                # 更新DOS標籤頁的內容字體
                if hasattr(tab_manager, 'dos_ui'):
                    try:
                        dos_ui = tab_manager.dos_ui
                        self.update_dos_tab_content_fonts(dos_ui, size)
                        print(f"[DEBUG] DOS標籤頁內容字體已更新為: {size}")
                    except Exception as e:
                        print(f"[WARNING] 更新DOS標籤頁內容字體時發生錯誤: {e}")

                # 更新使用說明標籤頁的內容字體
                if hasattr(tab_manager, 'guide_ui'):
                    try:
                        guide_ui = tab_manager.guide_ui
                        self.update_guide_tab_content_fonts(guide_ui, size)
                        print(f"[DEBUG] 使用說明標籤頁內容字體已更新為: {size}")
                    except Exception as e:
                        print(f"[WARNING] 更新使用說明標籤頁內容字體時發生錯誤: {e}")

                # 更新治具控制標籤頁的內容字體
                if hasattr(tab_manager, 'fixture_ui'):
                    try:
                        fixture_ui = tab_manager.fixture_ui
                        self.update_fixture_tab_content_fonts(fixture_ui, size)
                        print(f"[DEBUG] 治具控制標籤頁內容字體已更新為: {size}")
                    except Exception as e:
                        print(f"[WARNING] 更新治具控制標籤頁內容字體時發生錯誤: {e}")

                print(f"[DEBUG] 全域內容字體已更新為: {size}")

        except Exception as e:
            print(f"[ERROR] 更新全域內容字體時發生錯誤: {e}")
    def update_settings_tab_fonts(self, settings_ui, size):
        """更新設定標籤頁的UI字體"""
        try:
            font = ('Microsoft JhengHei UI', int(size))
            # 更新設定標籤頁中的所有標籤
            for widget in settings_ui.parent_frame.winfo_children():
                self._update_widget_font_recursive(widget, font, ['Label', 'Button'])
        except Exception as e:
            print(f"[ERROR] 更新設定標籤頁字體時發生錯誤: {e}")

    def update_dos_tab_fonts(self, dos_ui, size):
        """更新DOS標籤頁的UI字體"""
        try:
            font = ('Microsoft JhengHei UI', int(size))
            # 更新DOS標籤頁中的所有標籤和按鈕
            for widget in dos_ui.parent_frame.winfo_children():
                self._update_widget_font_recursive(widget, font, ['Label', 'Button'])
        except Exception as e:
            print(f"[ERROR] 更新DOS標籤頁字體時發生錯誤: {e}")

    def update_guide_tab_fonts(self, guide_ui, size):
        """更新使用說明標籤頁的UI字體"""
        try:
            font = ('Microsoft JhengHei UI', int(size))
            # 更新使用說明標籤頁中的所有標籤和按鈕
            for widget in guide_ui.parent_frame.winfo_children():
                self._update_widget_font_recursive(widget, font, ['Label', 'Button'])
        except Exception as e:
            print(f"[ERROR] 更新使用說明標籤頁字體時發生錯誤: {e}")

    def update_fixture_tab_fonts(self, fixture_ui, size):
        """更新治具控制標籤頁的UI字體"""
        try:
            font = ('Microsoft JhengHei UI', int(size))
            # 更新治具控制標籤頁中的所有標籤和按鈕
            if hasattr(fixture_ui, 'parent_frame'):
                for widget in fixture_ui.parent_frame.winfo_children():
                    self._update_widget_font_recursive(widget, font, ['Label', 'Button'])
        except Exception as e:
            print(f"[ERROR] 更新治具控制標籤頁字體時發生錯誤: {e}")

    def update_settings_tab_content_fonts(self, settings_ui, size):
        """更新設定標籤頁的內容字體"""
        try:
            font = ('Consolas', int(size))
            # 更新設定標籤頁中的輸入框和下拉選單
            for widget in settings_ui.parent_frame.winfo_children():
                self._update_widget_font_recursive(widget, font, ['Entry', 'Combobox', 'Text'])
        except Exception as e:
            print(f"[ERROR] 更新設定標籤頁內容字體時發生錯誤: {e}")

    def update_dos_tab_content_fonts(self, dos_ui, size):
        """更新DOS標籤頁的內容字體"""
        try:
            font = ('Consolas', int(size))
            # 更新DOS標籤頁中的文字區域
            for widget in dos_ui.parent_frame.winfo_children():
                self._update_widget_font_recursive(widget, font, ['Entry', 'Text'])
        except Exception as e:
            print(f"[ERROR] 更新DOS標籤頁內容字體時發生錯誤: {e}")

    def update_guide_tab_content_fonts(self, guide_ui, size):
        """更新使用說明標籤頁的內容字體"""
        try:
            font = ('Consolas', int(size))
            # 更新使用說明標籤頁中的文字區域
            for widget in guide_ui.parent_frame.winfo_children():
                self._update_widget_font_recursive(widget, font, ['Text'])
        except Exception as e:
            print(f"[ERROR] 更新使用說明標籤頁內容字體時發生錯誤: {e}")

    def update_fixture_tab_content_fonts(self, fixture_ui, size):
        """更新治具控制標籤頁的內容字體"""
        try:
            font = ('Consolas', int(size))
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
                    widget.configure(font=font)
                except:
                    try:
                        widget['font'] = font
                    except:
                        pass

            # 遞歸處理子widget
            for child in widget.winfo_children():
                self._update_widget_font_recursive(child, font, widget_types)
        except Exception as e:
            pass  # 忽略個別widget的錯誤





    def _validate_execution_parameters(self):
        """驗證執行參數"""
        # 獲取 COM 口
        com = self.parent.components.combobox_com.get()
        if not com:
            self.parent.components.add_to_buffer("\n[錯誤] 請選擇 COM 口\n", "error")
            return False

        # 獲取指令
        cmd = self.parent.components.combobox_cmd.get()
        if not cmd:
            self.parent.components.add_to_buffer("\n[錯誤] 請選擇指令\n", "error")
            return False

        # 獲取指令內容
        section = self.parent.components.section_var.get()
        cmd_content = self.parent.commands_by_section.get(section, {}).get(cmd, "")
        if not cmd_content:
            self.parent.components.add_to_buffer(f"\n[錯誤] 找不到指令 '{cmd}' 的內容\n", "error")
            return False

        # 獲取結束字串
        end_str = self.parent.components.combobox_end.get()
        if not end_str:
            self.parent.components.add_to_buffer("\n[錯誤] 請輸入結束字串\n", "error")
            return False

        # 獲取超時時間
        try:
            timeout = int(self.parent.components.entry_timeout.get())
        except ValueError:
            self.parent.components.add_to_buffer("\n[錯誤] 超時時間必須是整數\n", "error")
            return False

        return True

    def _get_execution_parameters(self):
        """獲取執行參數"""
        # 獲取 COM 口
        com_port = self.parent.components.combobox_com.get()

        # 獲取指令
        selected_command = self.parent.components.combobox_cmd.get()

        # 獲取結束字串
        end_string = self.parent.components.combobox_end.get()

        # 獲取超時時間
        timeout = int(self.parent.components.entry_timeout.get())

        return selected_command, com_port, timeout, end_string

    def _start_execution(self, selected_command, com_port, timeout, end_string):
        """開始執行指令"""
        # 獲取指令內容
        section = self.parent.components.section_var.get()
        cmd_content = self.parent.commands_by_section.get(section, {}).get(selected_command, "")

        # 獲取傳輸模式
        transport_mode = "Console"  # 預設值
        if hasattr(self.parent.components, 'transport_mode_var'):
            transport_mode = self.parent.components.transport_mode_var.get()

        # 分割指令 - 使用設定中的間隔符號
        separator = self.setup.get('DUT_Control', {}).get('Command_Separator', '|')
        cmd_list = cmd_content.split(separator)

        # 調試信息：顯示分割後的指令
        print(f"[DEBUG] 原始指令: {cmd_content}")
        print(f"[DEBUG] 分隔符: '{separator}'")
        print(f"[DEBUG] 分割後指令列表: {cmd_list}")
        print(f"[DEBUG] 傳輸模式: {transport_mode}")

        # 顯示執行信息
        self.parent.components.add_to_buffer(f"\n=== 執行指令: {selected_command} ===\n", "purple")
        if transport_mode == "ADB":
            self.parent.components.add_to_buffer(f"傳輸模式: ADB, 超時: {timeout} 秒, 結束字串: {end_string}\n", "purple")
            # 顯示多重指令模式信息
            if len(cmd_list) > 1:
                self.parent.components.add_to_buffer(f"多重指令模式: 將執行 {len(cmd_list)} 個指令\n", "purple")
                for i, cmd in enumerate(cmd_list, 1):
                    cmd = cmd.strip()
                    if cmd:
                        self.parent.components.add_to_buffer(f"  {i}. {cmd}\n", "purple")
                self.parent.components.add_to_buffer("\n", "purple")
        else:
            self.parent.components.add_to_buffer(f"COM 口: {com_port}, 超時: {timeout} 秒, 結束字串: {end_string}\n", "purple")
            # 顯示多重指令模式信息
            if len(cmd_list) > 1:
                self.parent.components.add_to_buffer(f"多重指令模式: 將執行 {len(cmd_list)} 個指令\n", "purple")
                for i, cmd in enumerate(cmd_list, 1):
                    cmd = cmd.strip()
                    if cmd:
                        self.parent.components.add_to_buffer(f"  {i}. {cmd}\n", "purple")
                self.parent.components.add_to_buffer("\n", "purple")

        # 多重指令模式信息已在上面顯示，這裡不再重複

        # 重置進度條並顯示
        self.parent.components.reset_progress()
        self.parent.components.show_progress()

        # 重置停止事件
        self.parent.stop_event = threading.Event()

        # 根據傳輸模式創建對應的工作器
        if transport_mode == "ADB":
            # 導入 ADB 工作器
            from adb_worker import ADBWorker

            # 創建並啟動 ADB 線程
            self.parent.thread = ADBWorker(
                cmd_list, end_string, timeout,
                on_data=lambda text, tag: self.on_data(text, tag),
                on_status=lambda connected: self.parent.root.after(0, lambda: self.update_status_light(connected)),
                on_progress=lambda p: self.parent.root.after(0, lambda: self.parent.components.update_progress(p)),
                on_finish=lambda: self.parent.root.after(0, self.on_command_finish),
                stop_event=self.parent.stop_event
            )
        else:
            # 創建並啟動串口線程
            self.parent.thread = SerialWorker(
                com_port, cmd_list, end_string, timeout,
                on_data=lambda text, tag: self.on_data(text, tag),
                on_status=lambda connected: self.parent.root.after(0, lambda: self.update_status_light(connected)),
                on_progress=lambda p: self.parent.root.after(0, lambda: self.parent.components.update_progress(p)),
                on_finish=lambda: self.parent.root.after(0, self.on_command_finish),
                stop_event=self.parent.stop_event
            )

        # 設置顯示消息的回調
        if hasattr(self.parent.thread, 'show_message_callback'):
            self.parent.thread.show_message_callback = self._show_messagebox_and_callback
        elif hasattr(self.parent.thread, 'set_show_message_callback'):
            self.parent.thread.set_show_message_callback(self._show_messagebox_and_callback)

        # 開始啟動標籤閃爍
        if hasattr(self.parent.components, 'startup_label_manager'):
            self.parent.components.startup_label_manager.start_blink()

        # 啟動線程
        self.parent.thread.start()

    # 移除複雜的 _force_stop_execution 方法
    # 現在使用簡化的停止邏輯，直接在 on_execute 中處理

        # 獲取 COM 口（從顯示名稱中提取實際的 COM 口名稱）
        com_display_name = self.parent.components.combobox_com.get()
        if not com_display_name:
            self.parent.components.add_to_buffer("\n[錯誤] 請選擇 COM 口\n", "error")
            return False, "未選擇 COM 口"

        from config_core import extract_com_port_name
        com = extract_com_port_name(com_display_name)

        # 獲取指令
        cmd = self.parent.components.combobox_cmd.get()
        if not cmd:
            self.parent.components.add_to_buffer("\n[錯誤] 請選擇指令\n", "error")
            return False, "未選擇指令"

        # 獲取指令內容
        section = self.parent.components.section_var.get()
        cmd_content = self.parent.commands_by_section.get(section, {}).get(cmd, "")
        if not cmd_content:
            self.parent.components.add_to_buffer(f"\n[錯誤] 找不到指令 '{cmd}' 的內容\n", "error")
            return False, "找不到指令內容"

        # 獲取結束字串
        end_str = self.parent.components.combobox_end.get()
        if not end_str:
            self.parent.components.add_to_buffer("\n[錯誤] 請輸入結束字串\n", "error")
            return False, "未輸入結束字串"

        # 獲取超時時間
        try:
            timeout = int(self.parent.components.entry_timeout.get())
        except ValueError:
            self.parent.components.add_to_buffer("\n[錯誤] 超時時間必須是整數\n", "error")
            return False, "超時時間格式錯誤"

        return True, {
            'com': com,
            'cmd': cmd,
            'cmd_content': cmd_content,
            'end_str': end_str,
            'timeout': timeout
        }

    def _prepare_command_execution(self, params):
        """準備指令執行 - 重構輔助函數"""
        # 分割指令 - 使用設定中的間隔符號
        separator = self.setup.get('DUT_Control', {}).get('Command_Separator', '|')
        cmd_list = params['cmd_content'].split(separator)

        # 顯示執行信息
        self.parent.components.add_to_buffer(f"\n=== 執行指令: {params['cmd']} ===\n", "purple")
        self.parent.components.add_to_buffer(
            f"COM 口: {params['com']}, 超時: {params['timeout']} 秒, 結束字串: {params['end_str']}\n",
            "purple"
        )

        # 重置進度條並顯示
        self.parent.components.reset_progress()
        self.parent.components.show_progress()

        # 重置停止事件
        self.parent.stop_event = threading.Event()

        return cmd_list

    def _create_and_start_worker(self, params, cmd_list):
        """創建並啟動工作線程 - 重構輔助函數"""
        # 創建並啟動線程
        self.parent.thread = SerialWorker(
            params['com'], cmd_list, params['end_str'], params['timeout'],
            on_data=lambda text, tag: self.on_data(text, tag),
            on_status=lambda connected: self.parent.root.after(0, lambda: self.update_status_light(connected)),
            on_progress=lambda p: self.parent.root.after(0, lambda: self.parent.components.update_progress(p)),
            on_finish=lambda: self.parent.root.after(0, self.on_command_finish),
            stop_event=self.parent.stop_event
        )

        # 設置顯示消息的回調
        self.parent.thread.show_message_callback = self._show_messagebox_and_callback

        # 開始啟動標籤閃爍
        if hasattr(self.parent.components, 'startup_label_manager'):
            self.parent.components.startup_label_manager.start_blink()

        # 啟動線程
        self.parent.thread.start()

    def toggle_guide(self):
        """開啟 HTML 使用說明檔案"""
        try:
            import webbrowser
            import os
            import sys

            # 獲取 EXE 所在目錄（支援打包後的路徑）
            if getattr(sys, 'frozen', False):
                # 打包後的 EXE 環境
                exe_dir = os.path.dirname(sys.executable)
            else:
                # 開發環境
                exe_dir = os.path.dirname(os.path.dirname(__file__))

            # HTML 說明檔案路徑
            html_guide_path = os.path.join(exe_dir, 'PEGA指令通使用指南.html')

            # 檢查檔案是否存在
            if os.path.exists(html_guide_path):
                # 使用預設瀏覽器開啟 HTML 檔案
                webbrowser.open(f'file:///{html_guide_path.replace(os.sep, "/")}')

                # 顯示通知
                self.parent.components.show_notification("已開啟使用說明檔案", "success", 2000)
                print(f"[DEBUG] 開啟 HTML 使用說明: {html_guide_path}")
            else:
                # 如果 HTML 檔案不存在，顯示錯誤訊息
                self.parent.components.show_notification(f"找不到使用說明檔案：PEGA指令通使用指南.html", "error", 3000)
                print(f"[WARNING] HTML 使用說明檔案不存在: {html_guide_path}")

        except Exception as e:
            print(f"[ERROR] 開啟使用說明時發生錯誤: {e}")
            self.parent.components.show_notification(f"開啟使用說明時發生錯誤: {str(e)}", "error", 3000)

    def _show_text_guide(self):
        """顯示文字版使用說明（回退方案）"""
        try:


            # 讀取使用說明文件


            with open(GUIDE_FILE, 'r', encoding='utf-8') as f:


                content = f.read()





            # 清空回應內容視窗


            self.parent.components.text_output.configure(state='normal')


            self.parent.components.text_output.delete(tk.END)





            # 在回應內容視窗中顯示使用說明


            self.parent.components.text_output.insert('1.0', "\n=== 指令通使用說明 ===\n\n", "guide_title")


            self.parent.components.text_output.insert(tk.END, content)





            # 添加返回按鈕的提示


            self.parent.components.text_output.insert(tk.END, "\n\n按 [清空回應] 按鈕可返回正常模式。\n", "guide_title")





            # 自動捲到頂部


            self.parent.components.text_output.see('1.0')





            # 設回唯讀狀態


            self.parent.components.text_output.configure(state='disabled')





            # 標記當前正在顯示使用說明
            self.parent.showing_guide = True

            # 確保腳本檢視模式標記存在
            if not hasattr(self.parent, 'script_view_mode'):
                self.parent.script_view_mode = False





            # 在通知區域顯示提示


            self.parent.components.show_notification("已顯示使用說明，按「清空回應」按鈕可返回", "blue", 10000)





        except Exception as e:


            messagebox.showerror('錯誤', f'無法讀取使用說明文件：{e}')





    def on_execute(self):
        """執行指令按鈕點擊事件 - 簡化版本（回到穩定邏輯）"""
        try:
            # 如果正在執行，則中止（舊版穩定邏輯）
            if hasattr(self.parent, 'thread') and self.parent.thread is not None and self.parent.thread.is_alive():
                print("[DEBUG] 用戶點擊停止執行 - 使用簡化停止邏輯")
                # 只設置停止事件，讓線程自然結束
                self.parent.stop_event.set()
                self.parent.components.add_to_buffer("\n[已中止執行]\n", "error")
                self.parent.components.reset_progress()
                # 立即更新按鈕文字
                self.parent.components.btn_execute.config(text='執行指令')
                # 立即停止啟動標籤閃爍
                if hasattr(self.parent.components, 'startup_label_manager'):
                    self.parent.components.startup_label_manager.stop_blink()
                return

            # 第一次點擊：開始執行
            print("[DEBUG] 用戶點擊開始執行")

            # 驗證執行參數
            if not self._validate_execution_parameters():
                return

            # 獲取執行參數
            selected_command, com_port, timeout, end_string = self._get_execution_parameters()
            if not selected_command:
                return

            # 立即更新按鈕文字為停止
            self.parent.components.btn_execute.config(text='停止執行')

            # 立即重置進度條
            print("[DEBUG] 新指令開始，立即重置進度條")
            self.parent.components.reset_progress()

            # 開始執行
            self._start_execution(selected_command, com_port, timeout, end_string)

        except Exception as e:
            print(f"[ERROR] 執行指令時發生錯誤: {e}")
            self.parent.components.add_to_buffer(f"\n[錯誤] 執行指令時發生錯誤: {e}\n", "error")
            # 確保按鈕狀態正確
            self.parent.components.btn_execute.config(text='執行指令')





    def on_data(self, text, tag=None):


        """處理接收到的數據，自動檢測關鍵字並應用顏色"""


        # 如果已經指定了標籤，直接使用


        if tag:


            self.parent.components.add_to_buffer(text, tag)


            return





        # 直接添加文字，在 add_to_buffer 中處理關鍵字高亮


        self.parent.components.add_to_buffer(text, None)





    def _show_message_and_callback(self, message, callback):


        """在主線程中顯示消息，並在用戶確認後調用回調函數"""


        # 使用通知功能顯示訊息


        self.parent.components.show_notification(message, "blue", 5000)


        # 執行回調


        if callback:


            callback()





    def _show_messagebox_and_callback(self, message, callback):


        """在主線程中顯示消息框，並在用戶確認後調用回調函數"""


        # 使用messagebox显示消息


        messagebox.showinfo("系統訊息", message)


        # 执行回调


        if callback:


            callback()





    def on_command_finish(self):


        """指令執行完成時的處理"""


        try:


            # 立即更新按鈕文字


            self.parent.components.btn_execute.config(text='執行指令')





            # 立即停止進度條並隱藏
            self.parent.components.reset_progress()
            self.parent.components.hide_progress()





            # 立即停止啟動標籤閃爍
            if hasattr(self.parent.components, 'startup_label_manager'):
                self.parent.components.startup_label_manager.stop_blink()





            # 取消倒計時定時器


            if self.countdown_job:


                self.parent.root.after_cancel(self.countdown_job)


                self.countdown_job = None





            # 清空倒計時標籤


            if hasattr(self.parent.components, 'label_countdown'):


                self.parent.components.label_countdown.configure(text='')





            # 清理線程引用
            if hasattr(self.parent, 'thread'):
                self.parent.thread = None
                print("[DEBUG] 線程引用已清理")

            # 添加指令完成通知


            self.parent.components.show_notification(get_notification_text("cmd_done"), "green", 3000)





            # 確保所有 after 任務都已取消


            if hasattr(self, '_progress_update_job') and self._progress_update_job:


                try:


                    self.parent.root.after_cancel(self._progress_update_job)


                    self._progress_update_job = None


                except Exception as e:


                    print(f"[ERROR] 取消進度更新任務時發生錯誤: {e}")


        except Exception as e:


            print(f"[ERROR] 完成指令處理時發生錯誤: {e}")


            import traceback


            traceback.print_exc()

            # 確保在錯誤情況下也清理線程引用
            if hasattr(self.parent, 'thread'):
                self.parent.thread = None





    def update_status_light(self, connected):


        """更新連接狀態指示燈"""


        try:


            # 移除 LED 狀態燈更新邏輯 - 已改用啟動標籤閃爍
            # 連接狀態現在通過啟動標籤閃爍來顯示
            pass


            # 添加連接狀態通知
            if connected:
                self.parent.components.show_notification(get_notification_text("connected", self.parent.components.combobox_com.get()), "green", 3000)
            else:
                self.parent.components.show_notification(get_notification_text("disconnected"), "red", 3000)

        except Exception as e:
            print(f"[ERROR] 更新狀態指示燈時發生錯誤: {e}")
            import traceback
            traceback.print_exc()





    def on_save_setup(self):
        # 讀取當前的完整設定，確保不會遺失既有資料
        current_setup = load_setup()

        # 獲取當前視窗標題（不包含版本號部分）
        current_title = self.parent.title()
        window_title = current_title
        if " V" in current_title:
            window_title = current_title.split(" V")[0]

        # 保存頂層 Window_Title
        current_setup['Window_Title'] = window_title

        # 更新 DUT_Control 設定
        if 'DUT_Control' not in current_setup:
            current_setup['DUT_Control'] = {}

        current_setup['DUT_Control']['Serial_COM_Port'] = self.parent.components.combobox_com.get()
        current_setup['DUT_Control']['Command_Timeout_Seconds'] = self.parent.components.entry_timeout.get()
        current_setup['DUT_Control']['Command_End_String'] = self.parent.components.combobox_end.get()
        current_setup['DUT_Control']['UI_Font_Size'] = self.parent.components.font_size_var.get()
        current_setup['DUT_Control']['Content_Font_Size'] = self.parent.components.content_font_size_var.get()
        # 確保 DUT_Control 下的 Window_Title 與頂層一致
        current_setup['DUT_Control']['Window_Title'] = window_title

        # 保存通知字體大小設定
        if hasattr(self.parent.components, 'notification_font_size'):
            current_setup['DUT_Control']['Notification_Font_Size'] = str(self.parent.components.notification_font_size)
            print(f"[DEBUG] 保存通知字體大小設定: {self.parent.components.notification_font_size}")

        # 處理可用結束字串列表
        end_strings = self.parent.components.combobox_end['values']
        if not end_strings:
            end_strings = ["root"]
        current_setup['DUT_Control']['Available_End_Strings'] = list(end_strings)

        current_setup['DUT_Control']['Default_IP_Address'] = self.parent.components.entry_ip.get()
        current_setup['DUT_Control']['Window_Width'] = str(self.parent.winfo_width())
        current_setup['DUT_Control']['Window_Height'] = str(self.parent.winfo_height())
        current_setup['DUT_Control']['Last_Selected_Command_Section'] = self.parent.components.section_var.get()
        current_setup['DUT_Control']['Auto_Execute'] = self.parent.components.auto_execute_var.get() if hasattr(self.parent.components, 'auto_execute_var') else False

        # 更新 Fixture_Control 設定
        if 'Fixture_Control' not in current_setup:
            current_setup['Fixture_Control'] = {}

        current_setup['Fixture_Control']['Fixture_COM_Port'] = self.parent.components.fixture_com_var.get()
        current_setup['Fixture_Control']['Fixture_Font_Size'] = self.parent.components.fixture_font_size_var.get()
        current_setup['Fixture_Control']['Test_Category_MB'] = self.parent.components.mb_var.get()
        current_setup['Fixture_Control']['Current_Command'] = self.parent.components.fixture_cmd_var.get()

        # 保存設定
        save_setup(current_setup)
        messagebox.showinfo('成功', '設定已儲存')





    def on_load_setup(self):
        setup = load_setup()

        # 載入 DUT 設定
        dut_setup = setup.get('DUT_Control', {})
        self.parent.components.combobox_com.set(dut_setup.get('Serial_COM_Port', ''))
        self.parent.components.entry_timeout.delete(0, tk.END)
        self.parent.components.entry_timeout.insert(0, dut_setup.get('Command_Timeout_Seconds', '30'))
        self.parent.components.combobox_end.set(dut_setup.get('Command_End_String', 'root'))
        self.parent.components.font_size_var.set(dut_setup.get('UI_Font_Size', '12'))
        self.parent.components.content_font_size_var.set(dut_setup.get('Content_Font_Size', '12'))

        # 設定視窗標題 (優先使用頂層 Window_Title)
        window_title = setup.get('Window_Title')
        if not window_title:
            window_title = dut_setup.get('Window_Title')
        if not window_title:
            window_title = '指令通'

        print(f"[DEBUG] 載入視窗標題: {window_title}")
        self.parent.title(window_title)

        # 設定可用結束字串
        end_strings = dut_setup.get('Available_End_Strings', ['root'])
        if isinstance(end_strings, str):
            try:
                end_strings = json.loads(end_strings)
            except:
                end_strings = ['root']
        self.parent.components.combobox_end['values'] = end_strings

        self.parent.components.entry_ip.delete(0, tk.END)
        self.parent.components.entry_ip.insert(0, dut_setup.get('Default_IP_Address', '192.168.11.143'))
        self.parent.components.section_var.set(dut_setup.get('Last_Selected_Command_Section', '全部指令'))

        # 設定自動執行選項
        if hasattr(self.parent.components, 'auto_execute_var'):
            self.parent.components.auto_execute_var.set(dut_setup.get('Auto_Execute', False))

        # 載入 FIXTURE 設定
        fixture_setup = setup.get('Fixture_Control', {})
        self.parent.components.fixture_com_var.set(fixture_setup.get('Fixture_COM_Port', ''))
        self.parent.components.fixture_font_size_var.set(fixture_setup.get('Fixture_Font_Size', '12'))
        self.parent.components.mb_var.set(fixture_setup.get('Test_Category_MB', True))
        self.parent.components.fixture_cmd_var.set(fixture_setup.get('Current_Command', ''))

        # 更新字體大小
        self.parent.components.update_font_size()
        self.parent.components.update_content_font_size()
        self.parent.components.update_fixture_font_size()

        # 更新視窗大小
        try:
            width = int(dut_setup.get('Window_Width', '800'))
            height = int(dut_setup.get('Window_Height', '600'))
            self.parent.geometry(f'{width}x{height}')
        except:
            pass





    def update_countdown(self, remaining):


        if self.parent.stop_event.is_set():


            if hasattr(self.parent.components, 'label_countdown'):


                self.parent.components.label_countdown.configure(text='')


            return





        if remaining > 0:


            # 顯示倒數秒數（整數）


            if hasattr(self.parent.components, 'label_countdown'):


                self.parent.components.label_countdown.configure(text=f'倒數: {int(remaining)}')





            # 計算進度百分比（從 0 開始到 100）


            try:


                total_timeout = float(self.parent.components.entry_timeout.get())


                progress = ((total_timeout - remaining) / total_timeout) * 100


                self.parent.components.update_progress(progress, "blue.Horizontal.TProgressbar")


            except (ValueError, ZeroDivisionError):


                pass





            # 每秒更新一次


            self.countdown_job = self.parent.root.after(1000, self.update_countdown, remaining - 1)


        else:


            # 倒數結束


            if hasattr(self.parent.components, 'label_countdown'):


                self.parent.components.label_countdown.configure(text='倒數: 0')


            self.parent.components.update_progress(100, "blue.Horizontal.TProgressbar")


            # 稍微延遲後停止


            self.parent.root.after(500, lambda: self.parent.stop_event.set())





    def remove_end_string(self):
        """從結束字串列表中移除當前選擇的項目"""
        try:
            # 獲取當前選擇的結束字串
            current_value = self.parent.components.combobox_end.get()
            if not current_value:
                return

            # 從 combobox 的值列表中移除
            values = list(self.parent.components.combobox_end['values'])
            if current_value in values:
                values.remove(current_value)
                self.parent.components.combobox_end['values'] = values

                # 更新 setup.json 中的正確路徑
                if 'DUT_Control' not in self.parent.setup:
                    self.parent.setup['DUT_Control'] = {}
                self.parent.setup['DUT_Control']['Available_End_Strings'] = values
                
                # 如果當前選擇的結束字串被刪除了，設定為第一個可用的
                if current_value == self.parent.setup.get('Command_End_String', 'root'):
                    if values:
                        self.parent.setup['DUT_Control']['Command_End_String'] = values[0]
                        self.parent.components.combobox_end.set(values[0])
                    else:
                        # 如果沒有可用的結束字串，設定為預設值
                        self.parent.setup['DUT_Control']['Command_End_String'] = 'root'
                        self.parent.components.combobox_end.set('root')

                # 保存到文件
                from config_core import save_setup
                save_setup(self.parent.setup)
                
                # 通知設定標籤頁更新
                self.notify_settings_tab_update()
                
                print(f"[INFO] 已移除結束字串: {current_value}")
                
        except Exception as e:
            print(f"[ERROR] 移除結束字串時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def add_end_string(self):
        """添加新的結束字串到列表中"""
        try:
            from tkinter import simpledialog
            
            # 彈出輸入對話框
            new_end_string = simpledialog.askstring("添加結束字串", "請輸入新的結束字串:")
            if not new_end_string or not new_end_string.strip():
                return
                
            new_end_string = new_end_string.strip()
            
            # 檢查是否已存在
            current_values = list(self.parent.components.combobox_end['values'])
            if new_end_string in current_values:
                from tkinter import messagebox
                messagebox.showwarning("警告", "該結束字串已存在")
                return
            
            # 添加到列表
            current_values.append(new_end_string)
            self.parent.components.combobox_end['values'] = current_values
            
            # 更新設定檔
            if 'DUT_Control' not in self.parent.setup:
                self.parent.setup['DUT_Control'] = {}
            self.parent.setup['DUT_Control']['Available_End_Strings'] = current_values
            
            # 保存到文件
            from config_core import save_setup
            save_setup(self.parent.setup)
            
            # 設定為當前選擇
            self.parent.components.combobox_end.set(new_end_string)
            
            # 通知設定標籤頁更新
            self.notify_settings_tab_update()
            
            print(f"[INFO] 已添加結束字串: {new_end_string}")
            
        except Exception as e:
            print(f"[ERROR] 添加結束字串時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def notify_settings_tab_update(self):
        """通知設定標籤頁更新 IP 地址和結束字串列表"""
        try:
            # 獲取主視窗
            root = self.parent.root
            if root and hasattr(root, 'tab_manager'):
                tab_manager = root.tab_manager
                if hasattr(tab_manager, 'settings_ui'):
                    # 調用設定標籤頁的刷新方法
                    tab_manager.settings_ui.refresh_from_dut_control()
                    print("[DEBUG] 已通知設定標籤頁更新")
                else:
                    print("[DEBUG] 設定標籤頁未找到")
            else:
                print("[DEBUG] 主視窗或標籤管理器未找到")
        except Exception as e:
            print(f"[ERROR] 通知設定標籤頁更新時發生錯誤: {e}")

    def apply_font_size(self):


        """套用字體大小設定"""


        try:


            size = int(self.parent.components.entry_font_size.get())


            if 8 <= size <= 20:


                self.parent.setup['DUT']['ContentFontSize'] = str(size)


                self.parent.save_setup()


                self.parent.components.text_output.configure(font=('Consolas', size))


                messagebox.showinfo("成功", f"字體大小已更新為 {size}")


            else:


                messagebox.showwarning("警告", "字體大小必須在 8-20 之間")


        except ValueError:


            messagebox.showwarning("警告", "請輸入有效的數字")





    def on_auto_exec_changed(self):


        """當自動執行勾選框狀態變更時，保存設置"""


        try:


            # 獲取當前勾選狀態


            auto_exec = self.parent.auto_exec_var.get()


            print(f"[DEBUG] 自動執行設置已變更為: {auto_exec}")





            # 更新設置


            self.parent.setup['Auto_Execute'] = auto_exec





            # 保存完整的設定結構


            from config_core import load_setup, save_setup


            full_setup = load_setup()


            full_setup['DUT_Control']['Auto_Execute'] = auto_exec


            save_setup(full_setup)





            # 添加自動執行狀態通知


            if auto_exec:


                self.parent.components.show_notification("已啟用自動執行功能", "blue", 3000)


            else:


                self.parent.components.show_notification("已禁用自動執行功能", "blue", 3000)





            print(f"[DEBUG] 自動執行設置已保存: {auto_exec}")


        except Exception as e:


            print(f"[ERROR] 保存自動執行設置時發生錯誤: {e}")


            import traceback


            traceback.print_exc()