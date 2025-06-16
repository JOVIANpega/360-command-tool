import subprocess
import platform
from tkinter import messagebox, scrolledtext
import json
from datetime import datetime
import os
import tkinter as tk
import tkinter.ttk as ttk
import threading

from config import COMMAND_FILE, GUIDE_FILE, save_setup, list_com_ports, load_setup
from serial_worker import SerialWorker

class UIHandlers:
    def __init__(self, parent):
        self.parent = parent
        self.countdown_job = None
        
    def parse_commands_by_section(self):
        """解析命令文件，按區段整理"""
        commands = {}
        section = "全部指令"  # 預設區段
        
        print("[DEBUG] 開始解析指令文件")
        
        try:
            with open(COMMAND_FILE, "r", encoding="utf-8") as file:
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
            # ping 結束時重置進度條
            self.parent.components.reset_progress()
            return

        def ping_worker():
            print("ping_worker started")
            try:
                default_ip = self.parent.setup.get('Default_IP', '192.168.11.143')
                ip = self.parent.components.entry_ip.get().strip() or default_ip
                self.parent.components.progress.config(style="blue.Horizontal.TProgressbar", value=0)
                self.update_status_light(False)
                param = '-n' if platform.system().lower() == 'windows' else '-c'
                command = ['ping', param, '4', '-w', '1000', ip]
                self.ping_stop = False
                self.parent.components.btn_ping.config(text='中止PING')
                self.parent.components.add_to_buffer(f"\n=== 開始 Ping {ip} ===\n", "success")
                self.parent.root.update_idletasks()
                startupinfo = None
                if platform.system().lower() == 'windows':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                self.ping_process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    startupinfo=startupinfo
                )
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
                        self.parent.root.after(0, lambda o=output: self.parent.components.add_to_buffer(o, "error" if ("請求超時" in o or "無法連線" in o or "失敗" in o) else None))
                        if "位元組" in output and "時間" in output or "請求超時" in output or "無法連線" in output or "失敗" in output:
                            received_packets += 1
                            progress = (received_packets / total_packets) * 100
                            if progress != last_progress:
                                self.parent.root.after(0, lambda p=progress: self.parent.components.progress.config(value=p))
                                last_progress = progress
                error = self.ping_process.stderr.read()
                if error:
                    self.parent.root.after(0, lambda: self.parent.components.add_to_buffer(error, "error"))
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
            finally:
                # ping 結束時重置進度條
                self.parent.root.after(0, lambda: self.parent.components.reset_progress())
                self.parent.root.after(0, lambda: self.parent.components.btn_ping.config(text='Ping'))
                self.ping_process = None

        self.ping_thread = threading.Thread(target=ping_worker, daemon=True)
        self.ping_thread.start()

    def refresh_com_ports(self):
        # 保存當前選擇
        current_selection = self.parent.components.combobox_com.get()
        # 更新 COM 口列表
        new_ports = list_com_ports()
        self.parent.components.combobox_com['values'] = new_ports
        
        # 如果當前選擇仍在新列表中，保持選擇；否則清空
        if current_selection and current_selection in new_ports:
            self.parent.components.combobox_com.set(current_selection)
            print(f"[DEBUG] refresh_com_ports: 保持選擇 {current_selection}")
        else:
            self.parent.components.combobox_com.set('')
            print(f"[DEBUG] refresh_com_ports: 清空選擇，當前選擇 '{current_selection}' 不在新列表 {new_ports} 中")

    def clear_output(self, event=None):
        """清空回應內容視窗，如果正在顯示使用說明，則恢復到正常模式"""
        self.parent.components.text_output.configure(state='normal')
        self.parent.components.text_output.delete('1.0', 'end')
        self.parent.components.text_output.configure(state='disabled')
        
        # 重置標記
        if hasattr(self.parent, 'showing_guide') and self.parent.showing_guide:
            self.parent.showing_guide = False

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
            messagebox.showinfo('備份成功', f'回應內容已備份至：\n{filename}')
        except Exception as e:
            messagebox.showerror('備份失敗', f'備份時發生錯誤：\n{str(e)}')

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
            
            # 保存設置
            self.parent.setup['UIFontSize'] = str(size)
            save_setup(self.parent.setup)

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
            
            # 保存設置
            self.parent.setup['ContentFontSize'] = str(size)
            save_setup(self.parent.setup)
            
            # 強制更新 UI
            self.parent.root.update_idletasks()
        except Exception as e:
            print(f"更改內容字體大小時發生錯誤: {e}")

    def toggle_guide(self):
        """在回應內容視窗中顯示使用說明，而不是開啟新視窗"""
        try:
            # 讀取使用說明文件
            with open(GUIDE_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 清空回應內容視窗
            self.parent.components.text_output.configure(state='normal')
            self.parent.components.text_output.delete('1.0', tk.END)
            
            # 在回應內容視窗中顯示使用說明
            self.parent.components.text_output.insert('1.0', "\n=== VALO360 指令通使用說明 ===\n\n", "guide_title")
            self.parent.components.text_output.insert(tk.END, content)
            
            # 添加返回按鈕的提示
            self.parent.components.text_output.insert(tk.END, "\n\n按 [清空回應] 按鈕可返回正常模式。\n", "guide_title")
            
            # 自動捲到頂部
            self.parent.components.text_output.see('1.0')
            
            # 設回唯讀狀態
            self.parent.components.text_output.configure(state='disabled')
            
            # 標記當前正在顯示使用說明
            self.parent.showing_guide = True
            
        except Exception as e:
            messagebox.showerror('錯誤', f'無法讀取使用說明文件：{e}')

    def on_execute(self):
        if self.parent.components.btn_exec['text'] == '中止':
            self.parent.stop_event.set()
            return
        # 清除舊倒數
        if self.countdown_job:
            self.parent.root.after_cancel(self.countdown_job)
            self.countdown_job = None
        com = self.parent.components.combobox_com.get()
        cmd_key = self.parent.components.combobox_cmd.get()
        end_str = self.parent.components.combobox_end.get()
        section = self.parent.components.section_var.get()
        
        print(f"[DEBUG] 執行指令: COM={com}, CMD={cmd_key}, Section={section}")
        
        try:
            timeout = float(self.parent.components.entry_timeout.get())
            if hasattr(self.parent.components, 'label_countdown'):
                self.parent.components.label_countdown.configure(text=f'倒數: {int(timeout)}')
            # 從 timeout-1 開始倒數，因為第一秒已經顯示了
            self.countdown_job = self.parent.root.after(1000, self.update_countdown, timeout - 1)
        except ValueError:
            messagebox.showwarning('提示', '請輸入正確的超時秒數')
            return
        if not com or not cmd_key or not end_str:
            messagebox.showwarning('提示', '請選擇COM口、指令並輸入結束字串')
            return
        
        # 獲取指令
        if section == '全部指令':
            # 從所有區段中查找指令
            cmd = ''
            for section_commands in self.parent.commands_by_section.values():
                if cmd_key in section_commands:
                    cmd = section_commands[cmd_key]
                    break
        else:
            cmd = self.parent.commands_by_section.get(section, {}).get(cmd_key, '')
        
        if not cmd:
            messagebox.showwarning('提示', f'找不到指令: {cmd_key}')
            return
            
        print(f"[DEBUG] 找到指令: {cmd}")
        
        cmd_list = cmd.split('|')
        self.parent.components.btn_exec.config(text='中止')  # 只改文字，不改 state
        self.parent.components.update_progress(0, "blue.Horizontal.TProgressbar")
        self.parent.stop_event.clear()
        
        # 在回應區域顯示開始執行的訊息
        self.parent.components.add_to_buffer(f"\n[發送] 開始執行指令: {cmd_key}\n", "send")
        self.parent.components.add_to_buffer(f"[發送] COM口: {com}\n", "send")
        self.parent.components.add_to_buffer(f"[發送] 指令內容: {cmd}\n", "send")
        
        # 定義消息框回調函數
        def show_message_callback(message, callback):
            # 在主線程中顯示消息框
            self.parent.root.after(0, lambda: self._show_message_and_callback(message, callback))
        
        # 啟動 SerialWorker
        self.parent.thread = SerialWorker(
            com, cmd_list, end_str, timeout,
            on_data=lambda text, tag: self.parent.components.add_to_buffer(text, tag),
            on_status=lambda connected: self.parent.root.after(0, lambda: self.update_status_light(connected)),
            on_progress=lambda p: self.parent.root.after(0, lambda: self.parent.components.update_progress(p)),
            on_finish=self.on_command_finish,
            stop_event=self.parent.stop_event
        )
        # 設置消息框回調函數
        self.parent.thread.show_message_callback = show_message_callback
        self.parent.thread.start()
        self.on_end_string_entered(None)
    
    def _show_message_and_callback(self, message, callback):
        """在主線程中顯示消息框，並在用戶確認後調用回調函數"""
        messagebox.showinfo('系統訊息', message)
        if callback:
            callback()

    def on_command_finish(self):
        self.parent.components.btn_exec.config(text='執行指令')  # 只改文字，不改 state
        self.parent.components.reset_progress()
        if self.countdown_job:
            self.parent.root.after_cancel(self.countdown_job)
            self.countdown_job = None
        if hasattr(self.parent.components, 'label_countdown'):
            self.parent.components.label_countdown.configure(text='')

    def update_status_light(self, connected):
        color = 'green' if connected else 'red'
        self.parent.components.status_canvas.itemconfig(self.parent.components.status_light, fill=color)

    def on_save_setup(self):
        # 保存 DUT 設定
        dut_setup = {
            'COM': self.parent.components.combobox_com.get(),
            'Timeout': self.parent.components.entry_timeout.get(),
            'EndString': self.parent.components.combobox_end.get(),
            'UIFontSize': self.parent.components.font_size_var.get(),
            'ContentFontSize': self.parent.components.content_font_size_var.get(),
            'Title': self.parent.title(),
            'EndStrings': json.dumps(self.parent.components.combobox_end['values'], ensure_ascii=False),
            'Default_IP': self.parent.components.entry_ip.get(),
            'WinWidth': str(self.parent.winfo_width()),
            'WinHeight': str(self.parent.winfo_height()),
            'LastSection': self.parent.components.section_var.get()
        }
        
        # 保存 FIXTURE 設定
        fixture_setup = {
            'COM': self.parent.components.fixture_com_var.get(),
            'FixtureFontSize': self.parent.components.fixture_font_size_var.get(),
            'MB': self.parent.components.mb_var.get(),
            'CMD': self.parent.components.fixture_cmd_var.get()
        }
        
        # 保存所有設定
        save_setup({
            'DUT': dut_setup,
            'FIXTURE': fixture_setup
        })
        messagebox.showinfo('成功', '設定已保存')

    def on_load_setup(self):
        setup = load_setup()
        
        # 載入 DUT 設定
        dut_setup = setup.get('DUT', {})
        self.parent.components.combobox_com.set(dut_setup.get('COM', ''))
        self.parent.components.entry_timeout.delete(0, tk.END)
        self.parent.components.entry_timeout.insert(0, dut_setup.get('Timeout', '30'))
        self.parent.components.combobox_end.set(dut_setup.get('EndString', 'root'))
        self.parent.components.font_size_var.set(dut_setup.get('UIFontSize', '12'))
        self.parent.components.content_font_size_var.set(dut_setup.get('ContentFontSize', '12'))
        self.parent.title(dut_setup.get('Title', 'VALO360 指令通'))
        try:
            end_strings = json.loads(dut_setup.get('EndStrings', '["root"]'))
            self.parent.components.combobox_end['values'] = end_strings
        except:
            self.parent.components.combobox_end['values'] = ['root']
        self.parent.components.entry_ip.delete(0, tk.END)
        self.parent.components.entry_ip.insert(0, dut_setup.get('Default_IP', '192.168.11.143'))
        self.parent.components.section_var.set(dut_setup.get('LastSection', '全部指令'))
        
        # 載入 FIXTURE 設定
        fixture_setup = setup.get('FIXTURE', {})
        self.parent.components.fixture_com_var.set(fixture_setup.get('COM', ''))
        self.parent.components.fixture_font_size_var.set(fixture_setup.get('FixtureFontSize', '12'))
        self.parent.components.mb_var.set(fixture_setup.get('MB', True))
        self.parent.components.fixture_cmd_var.set(fixture_setup.get('CMD', ''))
        
        # 更新字體大小
        self.parent.components.update_font_size()
        self.parent.components.update_content_font_size()
        self.parent.components.update_fixture_font_size()
        
        # 更新視窗大小
        try:
            width = int(dut_setup.get('WinWidth', '800'))
            height = int(dut_setup.get('WinHeight', '600'))
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
                
                # 更新 setup.json 中的兩個位置
                if 'DUT' not in self.parent.setup:
                    self.parent.setup['DUT'] = {}
                self.parent.setup['DUT']['EndStrings'] = values
                self.parent.setup['EndStrings'] = values
                
                # 保存到文件
                with open('setup.json', 'w', encoding='utf-8') as f:
                    json.dump(self.parent.setup, f, indent=4, ensure_ascii=False)
                
                # 更新 combobox 的顯示
                if values:
                    self.parent.components.combobox_end.set(values[0])
                else:
                    self.parent.components.combobox_end.set('')
                    
        except Exception as e:
            print(f"Error in remove_end_string: {e}")

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