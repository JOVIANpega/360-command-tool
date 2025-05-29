import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
from datetime import datetime
import os
import subprocess
import platform
from config import load_setup, save_setup, list_com_ports, GUIDE_FILE, COMMAND_FILE

from serial_worker import SerialWorker

def parse_commands_by_section():
    commands = {}
    current_section = None
    with open(COMMAND_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('==') and line.endswith('=='):
                current_section = line.strip('=')
                commands[current_section] = {}
            elif '=' in line and current_section:
                k, v = line.split('=', 1)
                commands[current_section][k.strip()] = v.strip()
    return commands

class SerialUI:
    def __init__(self, root):
        self.root = root
        self.setup = load_setup()
        self.root.title(self.setup.get('Title', 'VALO360 指令通'))
        try:
            self.root.iconbitmap('app.ico')
        except:
            pass
        self.serial_port = None
        self.thread = None
        self.stop_event = threading.Event()
        self.guide_window = None

        self.text_buffer = []
        self.buffer_size = 1000
        self.update_interval = 100  # 毫秒
        self.buffer_timer = None

        # 設定全白色主題
        self.root.configure(bg='white')

        # 進度條樣式
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure("blue.Horizontal.TProgressbar", foreground='blue', background='blue')
        self.style.configure("gray.Horizontal.TProgressbar", foreground='#d9d9d9', background='#d9d9d9')
        self.style.configure("TFrame", background="white")
        self.style.configure("TLabel", background="white", foreground="black")
        self.style.configure("TLabelframe", background="white", foreground="black")
        self.style.configure("TLabelframe.Label", background="white", foreground="black")

        # 設定預設字體大小
        self.ui_font_size = int(self.setup.get('UIFontSize', '12'))
        self.content_font_size = int(self.setup.get('ContentFontSize', '12'))
        self.default_font = ('Microsoft JhengHei UI', self.ui_font_size)
        self.content_font = ('Consolas', self.content_font_size)

        main_frame = ttk.Frame(root, padding=10, style="TFrame")
        main_frame.pack(fill='both', expand=True)

        left_panel = ttk.LabelFrame(main_frame, text='控制面板', padding=10, style="TLabelframe")
        left_panel.grid(row=0, column=0, sticky='nsew', padx=10)

        com_frame = ttk.Frame(left_panel, style="TFrame")
        com_frame.pack(fill='x', pady=5)
        self.label_com = ttk.Label(com_frame, text='COM口:', style="TLabel", font=self.default_font)
        self.label_com.pack(side='left')
        self.combobox_com = ttk.Combobox(com_frame, values=list_com_ports(), state='readonly', width=15, font=self.content_font)
        self.combobox_com.pack(side='left', padx=5)
        self.combobox_com.set(self.setup.get('COM', ''))
        self.btn_refresh = tk.Button(com_frame, text='刷新', command=self.refresh_com_ports, 
                                   bg='white', fg='black', activebackground='white', activeforeground='black',
                                   font=self.default_font)
        self.btn_refresh.pack(side='left')

        self.status_canvas = tk.Canvas(com_frame, width=30, height=30, bg='white', highlightthickness=0)
        self.status_canvas.pack(side='left', padx=5)
        self.status_light = self.status_canvas.create_oval(5, 5, 25, 25, fill='red')

        # 指令分類 Radiobutton
        self.section_var = tk.StringVar(value='全部指令')
        section_frame = ttk.Frame(left_panel, style="TFrame")
        section_frame.pack(fill='x', pady=5)
        self.sections = ['全部指令', '單板指令', '整機指令', '出貨指令']
        self.section_radiobuttons = []
        for sec in self.sections:
            rb = tk.Radiobutton(
                section_frame, text=sec, variable=self.section_var, value=sec, command=self.update_cmd_list,
                bg='white', fg='black', selectcolor='white', activebackground='white', activeforeground='black',
                indicatoron=0, relief='flat', borderwidth=1, font=self.default_font
            )
            rb.pack(side='left', padx=2)
            rb.bind("<Enter>", lambda e, b=rb: b.config(bg="#ff9999"))
            rb.bind("<Leave>", lambda e, b=rb: self.update_radio_bg())
            self.section_radiobuttons.append(rb)

        cmd_frame = ttk.Frame(left_panel, style="TFrame")
        cmd_frame.pack(fill='x', pady=5)
        self.label_cmd = ttk.Label(cmd_frame, text='指令:', style="TLabel", font=self.default_font)
        self.label_cmd.pack(side='left')
        self.combobox_cmd = ttk.Combobox(cmd_frame, state='readonly', width=25, font=self.content_font)
        self.combobox_cmd.pack(side='left', padx=5)
        self.combobox_cmd.bind('<Return>', lambda e: self.on_execute())

        # Ping 檢查功能
        ping_frame = ttk.LabelFrame(left_panel, text='Ping 檢查', padding=10, style="TLabelframe")
        ping_frame.pack(fill='x', pady=10)

        ip_frame = ttk.Frame(ping_frame, style="TFrame")
        ip_frame.pack(fill='x', pady=2)
        self.label_ip = ttk.Label(ip_frame, text='IP地址:', style="TLabel", font=self.default_font)
        self.label_ip.pack(side='left')
        self.entry_ip = ttk.Entry(ip_frame, width=15, font=self.content_font)
        self.entry_ip.pack(side='left', padx=5)
        # 設置預設 IP
        default_ip = self.setup.get('Default_IP', '192.168.11.143')
        self.entry_ip.delete(0, tk.END)  # 清除現有內容
        self.entry_ip.insert(0, default_ip)  # 插入預設 IP
        self.btn_ping = tk.Button(ip_frame, text='Ping', command=self.check_ping, 
                                bg='white', fg='black', activebackground='white', activeforeground='black',
                                font=self.default_font)
        self.btn_ping.pack(side='left', padx=5)
        self.btn_ping.bind("<Enter>", lambda e: self.btn_ping.config(bg="#ff9999"))
        self.btn_ping.bind("<Leave>", lambda e: self.btn_ping.config(bg="white"))
        self.entry_ip.bind('<Return>', lambda e: self.check_ping())

        # 設定字體大小控制
        font_frame = ttk.LabelFrame(left_panel, text='字體大小設定', padding=5, style="TLabelframe")
        font_frame.pack(fill='x', pady=2)

        ui_font_frame = ttk.Frame(font_frame, style="TFrame")
        ui_font_frame.pack(fill='x', pady=2)
        self.label_ui_font = ttk.Label(ui_font_frame, text='介面字體大小:', style="TLabel", font=self.default_font)
        self.label_ui_font.pack(side='left')
        self.ui_font_scale = tk.Scale(ui_font_frame, from_=8, to=20, orient='horizontal', 
                                    command=self.change_ui_font_size, length=150, bg='white', fg='black', 
                                    highlightthickness=0, font=self.default_font)
        self.ui_font_scale.pack(side='left', padx=5)
        self.ui_font_scale.set(self.ui_font_size)

        content_font_frame = ttk.Frame(font_frame, style="TFrame")
        content_font_frame.pack(fill='x', pady=2)
        self.label_content_font = ttk.Label(content_font_frame, text='內容字體大小:', style="TLabel", font=self.default_font)
        self.label_content_font.pack(side='left')
        self.content_font_scale = tk.Scale(content_font_frame, from_=8, to=20, orient='horizontal', 
                                         command=self.change_content_font_size, length=150, bg='white', fg='black', 
                                         highlightthickness=0, font=self.default_font)
        self.content_font_scale.pack(side='left', padx=5)
        self.content_font_scale.set(self.content_font_size)

        # 按鈕區域
        btn_frame = ttk.Frame(left_panel, style="TFrame")
        btn_frame.pack(fill='x', pady=10)
        self.btn_clear = tk.Button(btn_frame, text='清空回應', command=self.clear_output, 
                                 bg='white', fg='black', activebackground='white', activeforeground='black',
                                 font=self.default_font)
        self.btn_clear.pack(side='left', padx=2)
        self.btn_backup = tk.Button(btn_frame, text='備份回應', command=self.backup_output, 
                                  bg='white', fg='black', activebackground='white', activeforeground='black',
                                  font=self.default_font)
        self.btn_backup.pack(side='left', padx=2)
        self.btn_guide = tk.Button(btn_frame, text='使用說明', command=self.toggle_guide, 
                                 bg='white', fg='black', activebackground='white', activeforeground='black',
                                 font=self.default_font)
        self.btn_guide.pack(side='left', padx=2)

        # 右側面板
        right_panel = ttk.LabelFrame(main_frame, text='回應內容', padding=10, style="TLabelframe")
        right_panel.grid(row=0, column=1, sticky='nsew', padx=10)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        self.text_output = scrolledtext.ScrolledText(right_panel, font=self.content_font,
                                                   bg='white', fg='black', insertbackground='black')
        self.text_output.pack(fill='both', expand=True)
        self.text_output.tag_configure("success", foreground="green")
        self.text_output.tag_configure("error", foreground="red")

        self.progress = ttk.Progressbar(right_panel, mode='determinate', style="gray.Horizontal.TProgressbar")
        self.progress.pack(fill='x', pady=5)
        self.progress.pack_forget()  # 預設隱藏

        self.btn_exec = tk.Button(main_frame, text='執行指令',
                                 command=self.on_execute, bg='white', fg='black', 
                                 activebackground='white', activeforeground='black',
                                 font=self.default_font)
        self.btn_exec.grid(row=1, column=0, columnspan=2, pady=10, sticky='ew')
        self.btn_exec.bind("<Enter>", lambda e: self.btn_exec.config(bg="#ff9999"))
        self.btn_exec.bind("<Leave>", lambda e: self.btn_exec.config(bg="white"))

        # 綁定快捷鍵
        self.root.bind('<Control-r>', lambda e: self.refresh_com_ports())
        self.root.bind('<Control-l>', lambda e: self.clear_output())
        self.root.bind('<Control-b>', lambda e: self.backup_output())
        self.root.bind('<Control-h>', lambda e: self.toggle_guide())
        self.root.bind_all('<Return>', lambda e: self.on_execute(), add='+')

        # 自動偵測 COM 埠
        self.last_com_ports = self.combobox_com['values']
        self.auto_refresh_com_ports()

        # 載入指令
        self.commands_by_section = parse_commands_by_section()
        self.update_cmd_list()

    def check_ping(self):
        ip = self.entry_ip.get().strip()
    if not ip:
        messagebox.showwarning('提示', '請輸入IP地址')
        return

    # 根據作業系統選擇不同的 ping 參數
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '4', ip]  # 發送4個封包

    try:
        # 在回應區顯示開始訊息
        self.add_to_buffer(f"\n=== 開始 Ping {ip} ===\n", "success")
        
        # 使用 Popen 來即時讀取輸出
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # 行緩衝
            universal_newlines=True
        )

        # 讀取並顯示輸出
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                # 根據輸出內容決定顯示顏色
                if "請求超時" in output or "無法連線" in output or "失敗" in output:
                    self.add_to_buffer(output, "error")
                else:
                    self.add_to_buffer(output)

        # 讀取錯誤輸出
        error = process.stderr.read()
        if error:
            self.add_to_buffer(error, "error")

        # 獲取返回碼並顯示結果
        return_code = process.poll()
        if return_code == 0:
            self.add_to_buffer("\nPing 成功！\n", "success")
        else:
            self.add_to_buffer("\nPing 失敗！\n", "error")
            
        except Exception as e:
            self.add_to_buffer(f"Ping 執行錯誤: {str(e)}\n", "error")

    def update_radio_bg(self):
        selected = self.section_var.get()
        for rb, sec in zip(self.section_radiobuttons, self.sections):
            if selected == sec:
                rb.config(bg="#ff4d4d", fg="white", activebackground="#ff4d4d", activeforeground="white")
            else:
                rb.config(bg="white", fg="black", activebackground="white", activeforeground="black")

    def update_cmd_list(self):
        self.update_radio_bg()
        section = self.section_var.get()
        # 重新讀取 command.txt
        self.commands_by_section = parse_commands_by_section()
        cmds = self.commands_by_section.get(section, {})
        self.combobox_cmd['values'] = list(cmds.keys())
        self.combobox_cmd.set('')

    def auto_refresh_com_ports(self):
        current_ports = list_com_ports()
        if tuple(current_ports) != tuple(self.last_com_ports):
            self.combobox_com['values'] = current_ports
            self.last_com_ports = current_ports
        self.root.after(2000, self.auto_refresh_com_ports)  # 每2秒檢查一次

    def update_end_strings(self):
        try:
            end_strings = json.loads(self.setup.get('EndStrings', '["root"]'))
        except Exception:
            end_strings = ['root']
        self.combobox_end['values'] = end_strings

    def on_end_string_entered(self, event):
        new_string = self.combobox_end.get().strip()
        if not new_string:
            return
        try:
            end_strings = json.loads(self.setup.get('EndStrings', '["root"]'))
        except Exception:
            end_strings = ['root']
        if new_string not in end_strings:
            end_strings.append(new_string)
            self.setup['EndStrings'] = json.dumps(end_strings, ensure_ascii=False)
            save_setup(self.setup)
            self.update_end_strings()
        self.combobox_end.set(new_string)

    def update_ui_fonts(self):
        try:
            font_size = self.ui_font_scale.get()
            default_font = ('Microsoft JhengHei UI', font_size)
            self.label_com.configure(font=default_font)
            self.label_cmd.configure(font=default_font)
            self.label_end.configure(font=default_font)
            self.label_timeout.configure(font=default_font)
            self.label_ui_font.configure(font=default_font)
            self.label_content_font.configure(font=default_font)
            self.label_ip.configure(font=default_font)  # 新增
            self.btn_refresh.configure(font=default_font)
            self.btn_clear.configure(font=default_font)
            self.btn_backup.configure(font=default_font)
            self.btn_guide.configure(font=default_font)
            self.btn_exec.configure(font=default_font)
            self.btn_ping.configure(font=default_font)  # 新增
            for rb in self.section_radiobuttons:
                rb.configure(font=default_font)
        except Exception as e:
            print(f'更新介面字體時發生錯誤: {e}')

    def update_content_fonts(self):
        try:
            font_size = self.content_font_scale.get()
            content_font = ('Consolas', font_size)
            self.combobox_com.configure(font=content_font)
            self.combobox_cmd.configure(font=content_font)
            self.combobox_end.configure(font=content_font)
            self.entry_timeout.configure(font=content_font)
            self.entry_ip.configure(font=content_font)  # 新增
            self.text_output.configure(font=content_font)
            if self.guide_window and tk.Toplevel.winfo_exists(self.guide_window):
                for widget in self.guide_window.winfo_children():
                    if isinstance(widget, scrolledtext.ScrolledText):
                        widget.configure(font=content_font)
        except Exception as e:
            print(f'更新內容字體時發生錯誤: {e}')

    def change_ui_font_size(self, val):
        self.update_ui_fonts()
        self.setup['UIFontSize'] = str(val)
        save_setup(self.setup)

    def change_content_font_size(self, val):
        self.update_content_fonts()
        self.setup['ContentFontSize'] = str(val)
        save_setup(self.setup)

    def update_status_light(self, connected):
        color = 'green' if connected else 'red'
        self.status_canvas.itemconfig(self.status_light, fill=color)

    def refresh_com_ports(self):
        self.combobox_com['values'] = list_com_ports()
        self.combobox_com.set('')

    def clear_output(self, event=None):
        self.text_output.configure(state='normal')
        self.text_output.delete('1.0', tk.END)
        self.text_output.configure(state='normal')

    def backup_output(self):
        try:
            backup_dir = 'backup'
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(backup_dir, f'backup_{timestamp}.txt')
            content = self.text_output.get('1.0', tk.END)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo('備份成功', f'回應內容已備份至：\n{filename}')
        except Exception as e:
            messagebox.showerror('備份失敗', f'備份時發生錯誤：\n{str(e)}')

    def add_to_buffer(self, text, tag=None):
        self.text_buffer.append((text, tag))
        if len(self.text_buffer) > self.buffer_size:
            self.text_buffer = self.text_buffer[-self.buffer_size:]
        if self.buffer_timer:
            self.root.after_cancel(self.buffer_timer)
        self.buffer_timer = self.root.after(self.update_interval, self.flush_buffer)

    def flush_buffer(self):
        if not self.text_buffer:
            return
        self.text_output.configure(state='normal')
        for text, tag in self.text_buffer:
            if tag:
                self.text_output.insert(tk.END, text, tag)
            else:
                self.text_output.insert(tk.END, text)
        self.text_output.see(tk.END)  # 自動捲到最底
        self.text_output.configure(state='normal')
        self.text_buffer = []

    def on_execute(self):
        if self.btn_exec['text'] == '中止':
            self.stop_event.set()
            return
        com = self.combobox_com.get()
        cmd_key = self.combobox_cmd.get()
        end_str = self.combobox_end.get()
        section = self.section_var.get()
        try:
            timeout = float(self.entry_timeout.get())
        except ValueError:
            messagebox.showwarning('提示', '請輸入正確的超時秒數')
            return
        if not com or not cmd_key or not end_str:
            messagebox.showwarning('提示', '請選擇COM口、指令並輸入結束字串')
            return
        cmd = self.commands_by_section.get(section, {}).get(cmd_key, '')
        cmd_list = cmd.split('|')
        self.btn_exec.config(text='中止')  # 只改文字，不改 state
        self.progress.config(style="blue.Horizontal.TProgressbar")
        self.progress.pack(fill='x', pady=5)
        self.stop_event.clear()
        # 啟動 SerialWorker
        self.thread = SerialWorker(
            com, cmd_list, end_str, timeout,
            on_data=lambda text, tag: self.add_to_buffer(text, tag),
            on_status=lambda connected: self.root.after(0, lambda: self.update_status_light(connected)),
            on_progress=lambda p: self.root.after(0, lambda: self.progress.config(value=p)),
            on_finish=self.on_command_finish,
            stop_event=self.stop_event
        )
        self.thread.start()
        self.on_end_string_entered(None)

    def on_command_finish(self):
        self.btn_exec.config(text='執行指令')  # 只改文字，不改 state
        self.progress.config(style="gray.Horizontal.TProgressbar")
        self.progress.pack_forget()

    def toggle_guide(self):
        if self.guide_window and tk.Toplevel.winfo_exists(self.guide_window):
            self.guide_window.destroy()
            self.guide_window = None
        else:
            self.guide_window = tk.Toplevel(self.root)
            self.guide_window.title('使用說明')
            self.guide_window.geometry('600x400')
            try:
                with open(GUIDE_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                content = f'無法讀取 user_guide.txt: {e}'
            current_font_size = self.content_font_scale.get()
            font = ('Consolas', current_font_size)
            text = scrolledtext.ScrolledText(self.guide_window, font=font)
            text.pack(fill='both', expand=True)
            text.insert('1.0', content)
            text.config(state='disabled')

    def on_close(self):
        try:
            self.setup['COM'] = self.combobox_com.get()
            self.setup['Timeout'] = self.entry_timeout.get()
            self.setup['EndString'] = self.combobox_end.get()
            save_setup(self.setup)
            if self.stop_event:
                self.stop_event.set()
            self.root.destroy()
        except Exception as e:
            messagebox.showerror('錯誤', f'關閉程式時發生錯誤: {e}')
            self.root.destroy()