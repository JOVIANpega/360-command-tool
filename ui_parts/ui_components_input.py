# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import json

# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from config_core import list_com_ports, COMMAND_FILE

class UIComponentsInput:
    def init_com_components(self):
        com_frame = ttk.Frame(self.left_panel, style="TFrame")
        com_frame.grid(row=0, column=0, sticky='ew', pady=3)
        com_frame.columnconfigure(0, weight=0)
        com_frame.columnconfigure(1, weight=1)
        com_frame.columnconfigure(2, weight=0)
        com_frame.columnconfigure(3, weight=0)

        self.label_com = ttk.Label(com_frame, text='COM口:', style="TLabel")
        self.label_com.grid(row=0, column=0, sticky='w')

        com_values = list_com_ports()
        self.combobox_com = ttk.Combobox(com_frame, values=com_values, state='readonly', width=15)
        self.combobox_com.grid(row=0, column=1, padx=5, sticky='ew')

        refresh_command = None
        if hasattr(self.parent, 'handlers') and hasattr(self.parent.handlers, 'refresh_com_ports'):
            refresh_command = self.parent.handlers.refresh_com_ports
        else:
            refresh_command = lambda: None

        self.btn_refresh = tk.Button(com_frame, text='刷新', command=refresh_command,
                                   bg='#e0e0e0', fg='black', activebackground='#2196f3', activeforeground='black')
        self.btn_refresh.grid(row=0, column=2, padx=3)

        self.status_canvas = tk.Canvas(com_frame, width=40, height=40, bg='white', highlightthickness=0)
        self.status_canvas.grid(row=0, column=3, padx=3)
        self.status_light = self.status_canvas.create_oval(5, 5, 35, 35, fill='black')
        self.led_blinking = False

    def init_cmd_components(self):
        section_frame = ttk.Frame(self.left_panel, style="TFrame")
        section_frame.grid(row=1, column=0, sticky='ew', pady=5)
        section_frame.columnconfigure(0, weight=1)
        self.section_var = tk.StringVar()

        self.sections = []
        try:
            with open(COMMAND_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('==') and line.endswith('=='):
                        section_name = line.strip('=')
                        if section_name and section_name not in self.sections:
                            self.sections.append(section_name)
        except Exception as e:
            print(f"[ERROR] 讀取分類時發生錯誤: {e}")

        if not self.sections:
            self.sections = ['全部指令']

        if self.sections:
            self.section_var.set(self.sections[0])

        max_buttons_per_row = 4
        self.section_radiobuttons = []

        for i, sec in enumerate(self.sections):
            row = i // max_buttons_per_row
            col = i % max_buttons_per_row
            rb = tk.Radiobutton(
                section_frame, text=sec, variable=self.section_var, value=sec, 
                command=self.update_cmd_list,
                bg='#d9d9d9', fg='black', selectcolor='#d9d9d9', 
                activebackground='#2196f3', activeforeground='white',
                indicatoron=0, relief='flat', borderwidth=1, width=8, height=1,
                font=('Microsoft JhengHei UI', int(self.parent.setup.get('UI_Font_Size', '12')))
            )
            rb.grid(row=row, column=col, padx=1, pady=1, sticky='ew')
            rb.bind("<Enter>", lambda e, b=rb: b.config(bg="#2196f3", fg='white'))
            rb.bind("<Leave>", lambda e, b=rb: self.update_radio_bg())
            self.section_radiobuttons.append(rb)
            section_frame.columnconfigure(col, weight=1)

        cmd_frame = ttk.Frame(self.left_panel, style="TFrame")
        cmd_frame.grid(row=2, column=0, sticky='ew', pady=3)
        cmd_frame.columnconfigure(0, weight=0)
        cmd_frame.columnconfigure(1, weight=1)

        self.label_cmd = ttk.Label(cmd_frame, text='指令:', style="TLabel")
        self.label_cmd.grid(row=0, column=0, sticky='w')

        self.combobox_cmd = ttk.Combobox(cmd_frame, width=30, height=15, postcommand=self.update_cmd_list)
        self.combobox_cmd.grid(row=0, column=1, padx=5, sticky='ew')
        self.combobox_cmd.bind("<<ComboboxSelected>>", lambda e: self.on_cmd_selected())

        self.btn_cmd_reload = tk.Button(cmd_frame, text='🔄', command=self.update_cmd_list,
                                      bg='#d9d9d9', fg='black', activebackground='#2196f3', activeforeground='white',
                                      width=2, height=1, font=('Arial', 10, 'bold'))
        self.btn_cmd_reload.grid(row=0, column=2, padx=3)
        self.btn_cmd_reload.bind("<Enter>", lambda e: self.btn_cmd_reload.config(bg='#2196f3', fg='white'))
        self.btn_cmd_reload.bind("<Leave>", lambda e: self.btn_cmd_reload.config(bg='#d9d9d9', fg='black'))
        
        if self.parent.tooltip_manager:
            self.parent.tooltip_manager.add_tooltip_with_text(self.btn_cmd_reload, "重新載入指令外部檔案內容")

        self.section_description = ttk.Label(cmd_frame, text='', style="TLabel", wraplength=300)
        self.section_description.grid(row=1, column=0, columnspan=2, sticky='w', pady=3)

        timeout_frame = ttk.Frame(self.left_panel, style="TFrame")
        timeout_frame.grid(row=3, column=0, sticky='ew', pady=3)
        timeout_frame.columnconfigure(0, weight=0)
        timeout_frame.columnconfigure(1, weight=1)
        timeout_frame.columnconfigure(2, weight=0)
        timeout_frame.columnconfigure(3, weight=1)

        self.label_timeout = ttk.Label(timeout_frame, text='超時(秒):', style="TLabel")
        self.label_timeout.grid(row=0, column=0, sticky='w')

        self.entry_timeout = ttk.Entry(
            timeout_frame, 
            width=5, 
            textvariable=self.shared_config.get_var('dut_timeout')
        )
        self.entry_timeout.grid(row=0, column=1, padx=5, sticky='w')

        self.label_end = ttk.Label(timeout_frame, text='結束字串:', style="TLabel")
        self.label_end.grid(row=0, column=2, sticky='w')

        self.combobox_end = ttk.Combobox(timeout_frame, width=10)
        self.combobox_end.grid(row=0, column=3, padx=5, sticky='ew')
        self.combobox_end.bind("<Return>", self.parent.handlers.on_end_string_entered)
        self.combobox_end.bind("<<ComboboxSelected>>", self.on_end_string_changed)
        self.combobox_end.bind("<KeyRelease>", self.on_end_string_changed)

    def on_end_string_changed(self, event=None):
        try:
            current_end_string = self.combobox_end.get().strip()
            if current_end_string:
                from config_core import load_settings, save_settings
                settings = load_settings()
                if "DUT" not in settings:
                    settings["DUT"] = {}
                settings["DUT"]["end_prompt"] = current_end_string
                save_settings(settings)
        except Exception as e:
            print(f"[ERROR] 保存結束字串時發生錯誤: {e}")

    def load_ip_from_settings(self):
        try:
            from config_core import load_settings
            settings = load_settings()
            if "DUT" not in settings:
                settings["DUT"] = {}
            ip_address = settings["DUT"].get("ip_address", "192.168.11.143")
            self.entry_ip.delete(0, tk.END)
            self.entry_ip.insert(0, ip_address)
        except Exception as e:
            print(f"[ERROR] 載入IP地址設定時發生錯誤: {e}")
            self.entry_ip.delete(0, tk.END)
            self.entry_ip.insert(0, "192.168.11.143")

    def load_end_string_from_settings(self):
        try:
            from config_core import load_settings
            settings = load_settings()
            if "DUT" not in settings:
                settings["DUT"] = {}
            end_prompt = settings["DUT"].get("end_prompt", "root")
            self.combobox_end.set(end_prompt)
        except Exception as e:
            print(f"[ERROR] 載入結束字串設定時發生錯誤: {e}")
            self.combobox_end.set("root")

    def get_section_description(self, section):
        descriptions = {
            '全部指令': '包含所有可用的指令',
            '單板指令2': '用於單板測試的指令集',
            '整機指令3': '用於整機測試的指令集',
            '喇叭': '用於喇叭測試的指令集'
        }
        return descriptions.get(section, f'{section} 相關指令')

    def init_ping_components(self):
        ping_frame = ttk.Frame(self.left_panel, style="TFrame")
        ping_frame.grid(row=4, column=0, sticky='ew', pady=3)
        ping_frame.columnconfigure(0, weight=0)
        ping_frame.columnconfigure(1, weight=1)
        ping_frame.columnconfigure(2, weight=0)
        ping_frame.columnconfigure(3, weight=0)
        
        self.label_ip = ttk.Label(ping_frame, text='IP位址:', style="TLabel")
        self.label_ip.grid(row=0, column=0, sticky='w')
        
        self.ip_container = ttk.Frame(ping_frame, style="TFrame")
        self.ip_container.grid(row=0, column=1, sticky='ew', padx=5)
        
        self.ip_entries = []
        self.ip_delete_buttons = []
        
        self.load_ip_segments()
        if not self.ip_entries:
            self.add_ip_segment_without_save()
        
        self._loading_completed = True
        
        self.btn_add_ip = tk.Button(ping_frame, text='+', command=self.add_ip_segment, 
                                   width=2, bg='#d9d9d9', fg='black')
        self.btn_add_ip.grid(row=0, column=2, padx=2)
        self.btn_add_ip.bind("<Enter>", lambda e: self.btn_add_ip.config(bg='#2196f3', fg='white'))
        self.btn_add_ip.bind("<Leave>", lambda e: self.btn_add_ip.config(bg='#d9d9d9', fg='black'))
        
        self.btn_ping = tk.Button(ping_frame, text='Ping', command=self.on_ping, 
                                 width=6, bg='#d9d9d9', fg='black')
        self.btn_ping.grid(row=0, column=3, padx=2)
        self.btn_ping.bind("<Enter>", lambda e: self.btn_ping.config(bg='#2196f3', fg='white'))
        self.btn_ping.bind("<Leave>", lambda e: self.btn_ping.config(bg='#d9d9d9', fg='black'))

    def load_ip_segments(self):
        try:
            from config_core import load_setup
            setup = load_setup()
            ip_history = setup.get('DUT_Control', {}).get('IP_History', [])
            for ip in ip_history:
                if ip.strip():
                    self.add_ip_segment_without_save(ip)
        except Exception as e:
            print(f"[DEBUG] 載入 IP 區段時發生錯誤: {e}")

    def add_ip_segment_without_save(self, ip_address=""):
        if len(self.ip_entries) >= 20:
            return
        row_num = len(self.ip_entries)
        ip_entry = ttk.Entry(self.ip_container, width=15)
        ip_entry.grid(row=row_num, column=0, sticky='ew', pady=1)
        if ip_address:
            ip_entry.insert(0, ip_address)
        from functools import partial
        delete_btn = tk.Button(self.ip_container, text='-', command=partial(self.remove_ip_segment, row_num), 
                              width=2, bg='#ffcccc', fg='black')
        delete_btn.grid(row=row_num, column=1, padx=2)
        self.ip_entries.append(ip_entry)
        self.ip_delete_buttons.append(delete_btn)
        self.update_delete_buttons()

    def add_ip_segment(self, ip_address=""):
        if len(self.ip_entries) >= 20:
            messagebox.showwarning("警告", "最多只能新增 20 個 IP 區段")
            return
        row_num = len(self.ip_entries)
        ip_entry = ttk.Entry(self.ip_container, width=15)
        ip_entry.grid(row=row_num, column=0, sticky='ew', pady=1)
        if ip_address:
            ip_entry.insert(0, ip_address)
        from functools import partial
        delete_btn = tk.Button(self.ip_container, text='-', command=partial(self.remove_ip_segment, row_num), 
                              width=2, bg='#ffcccc', fg='black')
        delete_btn.grid(row=row_num, column=1, padx=2)
        self.ip_entries.append(ip_entry)
        self.ip_delete_buttons.append(delete_btn)
        self.update_delete_buttons()
        if hasattr(self, '_loading_completed'):
            self.save_ip_segments()

    def remove_ip_segment(self, row_index):
        if len(self.ip_entries) <= 1:
            messagebox.showwarning("警告", "至少需要保留一個 IP 區段")
            return
        self.ip_entries[row_index].destroy()
        self.ip_delete_buttons[row_index].destroy()
        del self.ip_entries[row_index]
        del self.ip_delete_buttons[row_index]
        self.rearrange_ip_segments()
        self.update_delete_buttons()

    def rearrange_ip_segments(self):
        for i, (entry, btn) in enumerate(zip(self.ip_entries, self.ip_delete_buttons)):
            entry.grid(row=i, column=0, sticky='ew', pady=1)
            btn.grid(row=i, column=1, padx=2)

    def update_delete_buttons(self):
        for i, btn in enumerate(self.ip_delete_buttons):
            from functools import partial
            btn.config(command=partial(self.remove_ip_segment, i))

    def get_all_ip_addresses(self):
        ip_list = []
        for entry in self.ip_entries:
            ip = entry.get().strip()
            if ip:
                ip_list.append(ip)
        return ip_list

    def save_ip_segments(self):
        try:
            from config_core import load_setup, save_setup
            setup = load_setup()
            ip_list = self.get_all_ip_addresses()
            setup['DUT_Control']['IP_History'] = ip_list
            save_setup(setup, manual_save=True)
        except Exception as e:
            print(f"[ERROR] 保存 IP 區段時發生錯誤: {e}")

    def on_ping(self):
        ip_list = self.get_all_ip_addresses()
        if not ip_list:
            messagebox.showwarning("警告", "請至少輸入一個 IP 地址")
            return
        current_ip = ip_list[0]
        try:
            import subprocess
            import platform
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "1", current_ip]
            else:
                cmd = ["ping", "-c", "1", current_ip]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                messagebox.showinfo("Ping 結果", f"IP {current_ip} 可以連通")
            else:
                messagebox.showwarning("Ping 結果", f"IP {current_ip} 無法連通")
        except Exception as e:
            messagebox.showerror("錯誤", f"Ping 操作失敗: {e}")

    def update_radio_bg(self):
        selected = self.section_var.get()
        for rb, sec in zip(self.section_radiobuttons, self.sections):
            if rb['state'] == 'disabled':
                rb.config(bg="#e0e0e0", fg="#b0b0b0", activebackground="#e0e0e0", activeforeground="#b0b0b0")
            elif selected == sec:
                rb.config(bg="#2196f3", fg="white", activebackground="#2196f3", activeforeground="white")
            else:
                rb.config(bg="#d9d9d9", fg="black", activebackground="#2196f3", activeforeground="white")

    def update_cmd_list(self):
        self.update_radio_bg()
        section = self.section_var.get()
        self.section_description.config(text=self.get_section_description(section))

        # [優化]：每次點選分類或按刷新，都重新解析一次指令表，確保編輯後的內容立即生效
        try:
            new_cmds = self.parent.handlers.command_processor.parse_commands_by_section()
            if new_cmds:
                self.parent.commands_by_section = new_cmds
        except Exception as e:
            print(f"[DEBUG] 重新載入指令表失敗: {e}")

        cmds = self.parent.commands_by_section.get(section, {})
        if not cmds and section != '全部指令':
            cmds = self.parent.commands_by_section.get('全部指令', {})
        curr_val = self.combobox_cmd.get()
        new_names = list(cmds.keys())
        self.combobox_cmd['values'] = new_names
        if curr_val in new_names:
            self.combobox_cmd.set(curr_val)
        elif new_names:
            self.combobox_cmd.set(new_names[0])
        else:
            self.combobox_cmd.set('')

    def update_end_strings(self):
        try:
            end_strings = json.loads(self.parent.setup.get('Available_End_Strings', '["root"]'))
        except Exception:
            end_strings = ['root']
        self.combobox_end['values'] = end_strings

    def on_cmd_selected(self):
        """當指令被選中時，更新資訊"""
        try:
            selected_cmd = self.combobox_cmd.get()
            section = self.section_var.get()
            if not selected_cmd:
                return

            cmd_content = self.parent.commands_by_section.get(section, {}).get(selected_cmd, '')
            if not cmd_content and section != '全部指令':
                cmd_content = self.parent.commands_by_section.get('全部指令', {}).get(selected_cmd, '')

            if cmd_content:
                # 1. 顯示選擇通知
                if hasattr(self, 'show_notification'):
                    from config_utils import get_notification_text
                    self.show_notification(get_notification_text("cmd_selected", selected_cmd), "blue", 3000)

                # 2. [重點] 直接設定完整原始碼到下拉選單上
                if hasattr(self.parent, 'tooltip_manager') and self.parent.tooltip_manager:
                    full_detail = cmd_content.replace('==>', '\n➔ ')
                    self.parent.tooltip_manager.add_tooltip_with_text(self.combobox_cmd, f"【完整指令原始碼】\n{full_detail}", side='right')
            else:
                if hasattr(self.parent, 'tooltip_manager') and self.parent.tooltip_manager:
                    self.parent.tooltip_manager.add_tooltip(self.combobox_cmd, 'combobox_cmd')
        except Exception as e:
            print(f"[ERROR] on_cmd_selected 發生嚴重錯誤: {e}")
            import traceback
            traceback.print_exc()