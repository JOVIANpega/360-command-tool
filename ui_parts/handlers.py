import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from config import COMMAND_FILE, list_com_ports, GUIDE_FILE
import subprocess
import os
from datetime import datetime

class Handlers:
    def __init__(self, parent):
        self.parent = parent
        self.countdown = 0
        self.timeout = 0
        self.guide_window = None

    def toggle_guide(self):
        """切換使用說明視窗"""
        try:
            if self.guide_window is None or not self.guide_window.winfo_exists():
                # 創建新視窗
                self.guide_window = tk.Toplevel(self.parent.root)
                self.guide_window.title("使用說明")
                self.guide_window.geometry("600x400")
                
                # 創建文字區域
                text = scrolledtext.ScrolledText(self.guide_window, wrap=tk.WORD, font=('Microsoft JhengHei UI', 12))
                text.pack(expand=True, fill='both', padx=10, pady=10)
                
                # 讀取說明文件
                try:
                    with open(GUIDE_FILE, 'r', encoding='utf-8') as f:
                        content = f.read()
                        text.insert('1.0', content)
                except Exception as e:
                    text.insert('1.0', f"讀取說明文件時發生錯誤: {e}")
                
                text.configure(state='disabled')  # 設為唯讀
                
                # 設置關閉事件
                def on_closing():
                    self.guide_window.destroy()
                    self.guide_window = None
                self.guide_window.protocol("WM_DELETE_WINDOW", on_closing)
                
                # 置中顯示
                self.guide_window.update_idletasks()
                width = self.guide_window.winfo_width()
                height = self.guide_window.winfo_height()
                x = (self.guide_window.winfo_screenwidth() // 2) - (width // 2)
                y = (self.guide_window.winfo_screenheight() // 2) - (height // 2)
                self.guide_window.geometry(f'{width}x{height}+{x}+{y}')
            else:
                # 如果視窗已存在，就關閉它
                self.guide_window.destroy()
                self.guide_window = None
        except Exception as e:
            print(f"切換使用說明視窗時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"切換使用說明視窗時發生錯誤: {e}")

    def change_content_font_size(self, value):
        """改變內容字體大小"""
        try:
            size = int(float(value))
            self.parent.components.text_output.configure(font=('Microsoft JhengHei UI', size))
        except Exception as e:
            print(f"改變內容字體大小時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"改變內容字體大小時發生錯誤: {e}")

    def clear_output(self):
        """清空輸出內容"""
        try:
            self.parent.components.text_output.delete(1.0, tk.END)
        except Exception as e:
            print(f"清空輸出內容時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"清空輸出內容時發生錯誤: {e}")

    def backup_output(self):
        """備份輸出內容"""
        try:
            # 創建 logs 目錄（如果不存在）
            if not os.path.exists('logs'):
                os.makedirs('logs')
            
            # 生成檔案名稱（使用當前時間）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'logs/output_{timestamp}.txt'
            
            # 獲取輸出內容
            content = self.parent.components.text_output.get(1.0, tk.END)
            
            # 寫入檔案
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            messagebox.showinfo("成功", f"輸出內容已備份至 {filename}")
        except Exception as e:
            print(f"備份輸出內容時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"備份輸出內容時發生錯誤: {e}")

    def check_ping(self):
        """檢查 IP 是否可以 ping 通"""
        try:
            ip = self.parent.components.entry_ip.get()
            if not ip:
                messagebox.showerror("錯誤", "請輸入 IP 地址")
                return
            
            # 執行 ping 命令
            result = subprocess.run(['ping', '-n', '1', ip], 
                                 capture_output=True, 
                                 text=True, 
                                 encoding='big5')
            
            # 檢查結果
            if result.returncode == 0:
                self.parent.components.add_to_buffer(f'\n[成功] {ip} 可以 ping 通\n', "success")
            else:
                self.parent.components.add_to_buffer(f'\n[失敗] {ip} 無法 ping 通\n', "error")
        except Exception as e:
            print(f"檢查 ping 時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"檢查 ping 時發生錯誤: {e}")

    def change_ui_font_size(self, value):
        """改變 UI 字體大小"""
        try:
            size = int(float(value))
            style = ttk.Style()
            # 更新所有相關元件的字體大小
            style.configure('TButton', font=('Microsoft JhengHei UI', size))
            style.configure('TLabel', font=('Microsoft JhengHei UI', size))
            style.configure('TCombobox', font=('Microsoft JhengHei UI', size))
            style.configure('TEntry', font=('Microsoft JhengHei UI', size))
            style.configure('TNotebook.Tab', font=('Microsoft JhengHei UI', size, 'bold'))
            # 更新進度條標籤
            if hasattr(self.parent.components, 'label_countdown'):
                self.parent.components.label_countdown.configure(font=('Microsoft JhengHei UI', size))
        except Exception as e:
            print(f"改變 UI 字體大小時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"改變 UI 字體大小時發生錯誤: {e}")

    def remove_end_string(self):
        """移除結束字串"""
        try:
            current = self.parent.components.combobox_end.get()
            values = list(self.parent.components.combobox_end['values'])
            if current in values:
                values.remove(current)
                self.parent.components.combobox_end['values'] = values
                if values:
                    self.parent.components.combobox_end.set(values[0])
                else:
                    self.parent.components.combobox_end.set('')
        except Exception as e:
            print(f"移除結束字串時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"移除結束字串時發生錯誤: {e}")

    def refresh_com_ports(self):
        """刷新串口列表"""
        try:
            ports = list_com_ports()
            self.parent.components.combobox_com['values'] = ports
            if ports and self.parent.components.combobox_com.get() not in ports:
                self.parent.components.combobox_com.set(ports[0])
        except Exception as e:
            print(f"刷新串口列表時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"刷新串口列表時發生錯誤: {e}")

    def parse_commands_by_section(self):
        """解析 command.txt 中的指令，按區段分類"""
        commands_by_section = {}
        current_section = "全部指令"
        commands_by_section[current_section] = {}
        
        try:
            with open(COMMAND_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1]
                        if current_section not in commands_by_section:
                            commands_by_section[current_section] = {}
                    else:
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            cmd_name = parts[0].strip()
                            cmd_content = parts[1].strip()
                            commands_by_section[current_section][cmd_name] = cmd_content
        except Exception as e:
            print(f"解析指令檔案時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"解析指令檔案時發生錯誤: {e}")
        
        return commands_by_section

    def on_execute(self):
        """執行指令"""
        try:
            # 檢查 command.txt 是否合法
            if not self.check_command_file_validity():
                messagebox.showerror("錯誤", "command.txt 需要包含合法的編輯代碼 (JOVIAN)")
                return

            # 獲取當前選擇的指令
            cmd = self.parent.ui.combobox_cmd.get()
            if not cmd:
                messagebox.showerror("錯誤", "請選擇指令")
                return

            # 獲取指令內容
            cmd_content = self.parent.commands_by_section.get(self.parent.ui.section_var.get(), {}).get(cmd, '')
            if not cmd_content:
                messagebox.showerror("錯誤", "無效的指令")
                return

            # 獲取超時時間
            try:
                self.timeout = int(self.parent.ui.entry_timeout.get())
            except ValueError:
                messagebox.showerror("錯誤", "超時時間必須為數字")
                return

            # 開始倒數計時
            self.parent.ui.show_progress(True)
            self.parent.ui.update_progress(0, "blue.Horizontal.TProgressbar")
            self.start_countdown()

            # 發送指令
            self.parent.serial_worker.send_command(cmd_content, self.timeout)
            
        except Exception as e:
            print(f"執行指令時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"執行指令時發生錯誤: {e}")

    def check_command_file_validity(self):
        """檢查 command.txt 是否包含合法的編輯代碼"""
        try:
            with open(COMMAND_FILE, 'r', encoding='utf-8') as f:
                content = f.read().upper()
                return 'JOVIAN' in content
        except Exception as e:
            print(f"檢查 command.txt 時發生錯誤: {e}")
            return False

    def start_countdown(self):
        """開始倒數計時"""
        self.countdown = self.timeout
        self.update_countdown()

    def update_countdown(self):
        """更新倒數計時"""
        if self.countdown > 0:
            self.parent.ui.label_countdown.config(text=str(self.countdown))
            self.countdown -= 1
            # 更新進度條
            progress = ((self.timeout - self.countdown) / self.timeout) * 100
            self.parent.ui.update_progress(progress)
            self.parent.root.after(1000, self.update_countdown)
        else:
            self.parent.ui.label_countdown.config(text="")
            self.parent.ui.reset_progress() 