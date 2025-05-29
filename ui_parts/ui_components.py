import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import sys
import json

# 將當前目錄加入 Python 路徑
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from config import list_com_ports, save_setup, GUIDE_FILE, COMMAND_FILE

class UIComponents:
    def __init__(self, parent):
        self.parent = parent
        self.init_ui()
        # 讀取 setup.txt 的寬高
        width = int(self.parent.setup.get('Window_Width', 800))
        height = int(self.parent.setup.get('Window_Height', 600))
        # 視窗最大化
        try:
            self.parent.root.state('zoomed')  # Windows
        except Exception:
            self.parent.root.attributes('-zoomed', True)  # Linux
        self.last_size = (width, height)
        self.parent.root.bind('<Configure>', self.on_window_resize)
        # 綁定 Enter 鍵執行指令
        self.parent.root.bind('<Return>', lambda e: self.parent.handlers.on_execute())
        
    def center_window(self, width, height):
        self.parent.root.update_idletasks()
        screen_width = self.parent.root.winfo_screenwidth()
        screen_height = self.parent.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.parent.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def init_ui(self):
        # 建立主框架
        self.main_frame = ttk.PanedWindow(self.parent.parent, orient='horizontal', style="Main.TFrame")
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        # 配置主框架的 grid
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=2)
        
        # --- 左側控制面板可下拉 ---
        # 1. 建立一個外層 Frame
        left_panel_container = ttk.Frame(self.main_frame)
        # 2. 建立 Canvas 和 Scrollbar
        canvas = tk.Canvas(left_panel_container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_panel_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        left_panel_container.grid_rowconfigure(0, weight=1)
        left_panel_container.grid_columnconfigure(0, weight=1)
        # 3. 在 Canvas 裡建立一個 Frame，作為 left_panel
        self.left_panel = ttk.LabelFrame(canvas, text='控制面板', padding=10, style="Main.TLabelframe")
        left_panel_window = canvas.create_window((0, 0), window=self.left_panel, anchor='nw')
        # 4. 綁定自動調整 scrollregion
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.left_panel.bind("<Configure>", on_frame_configure)
        # 5. 滾輪支援
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 建立右側面板
        self.right_panel = ttk.LabelFrame(self.main_frame, text='回應內容', padding=10, style="Main.TLabelframe")
        
        # 將左右面板加入 PanedWindow
        self.main_frame.add(left_panel_container, weight=1)
        self.main_frame.add(self.right_panel, weight=2)
        
        # 綁定 PanedWindow 分割位置變更事件
        self.main_frame.bind('<ButtonRelease-1>', self.on_pane_position_changed)
        
        # 初始化各個元件
        self.init_com_components()
        self.init_cmd_components()
        self.init_ping_components()
        self.init_settings_components()
        self.init_output_components()
        self.init_progress_components()
        
        # 強化 left_panel 內所有 Entry/Combobox 的 <Return> 綁定
        for widget in [self.combobox_cmd, self.entry_timeout, self.combobox_end, self.entry_ip, self.combobox_com]:
            widget.bind('<Return>', lambda e: self.parent.handlers.on_execute())
            
        # 將執行按鈕移回 left_panel 最下方，並用 grid 固定
        self.init_exec_button_left_panel()
        # 統一所有 left_panel 內 tk.Button hover 為藍底白字
        for widget in self.left_panel.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, tk.Button):
                    child.bind("<Enter>", lambda e, b=child: b.config(bg="#2196f3", fg="white"))
                    child.bind("<Leave>", lambda e, b=child: b.config(bg="white", fg="black"))
        
        # 恢復 PanedWindow 分割位置（延遲執行，確保視窗已完全載入）
        self.parent.root.after(200, self.restore_pane_position)

    def init_com_components(self):
        com_frame = ttk.Frame(self.left_panel, style="TFrame")
        com_frame.grid(row=0, column=0, sticky='ew', pady=5)
        com_frame.columnconfigure(0, weight=1)
        self.label_com = ttk.Label(com_frame, text='COM口:', style="TLabel")
        self.label_com.grid(row=0, column=0, sticky='w')
        
        # 獲取可用的 COM 口列表
        com_values = list_com_ports()
        
        # 創建 COM 口下拉選單
        self.combobox_com = ttk.Combobox(com_frame, values=com_values, state='readonly', width=15)
        self.combobox_com.grid(row=0, column=1, padx=5, sticky='ew')
        
        # 注意：不在這裡設定預設值，由 load_initial_settings 統一處理
        print(f"[DEBUG] init_com_components: 已創建 COM 口選單，可用 COM 口: {com_values}")
        
        self.btn_refresh = tk.Button(com_frame, text='刷新', command=self.parent.handlers.refresh_com_ports,
                                   bg='#e0e0e0', fg='black', activebackground='#2196f3', activeforeground='black')
        self.btn_refresh.grid(row=0, column=2, padx=5)
        self.status_canvas = tk.Canvas(com_frame, width=60, height=60, bg='white', highlightthickness=0)
        self.status_canvas.grid(row=0, column=3, padx=5)
        self.status_light = self.status_canvas.create_oval(10, 10, 50, 50, fill='black')
        self.led_blinking = False

    def init_cmd_components(self):
        section_frame = ttk.Frame(self.left_panel, style="TFrame")
        section_frame.grid(row=1, column=0, sticky='ew', pady=5)
        section_frame.columnconfigure(0, weight=1)
        self.section_var = tk.StringVar(value='全部指令')
        self.sections = ['全部指令', '單板指令', '整機指令', '出貨指令']
        self.section_radiobuttons = []
        for i, sec in enumerate(self.sections):
            rb = tk.Radiobutton(
                section_frame, text=sec, variable=self.section_var, value=sec, 
                command=self.update_cmd_list,
                bg='#d9d9d9', fg='black', selectcolor='#d9d9d9', 
                activebackground='#2196f3', activeforeground='white',
                indicatoron=0, relief='flat', borderwidth=1, width=8, height=2,
                font=('Microsoft JhengHei UI', int(self.parent.setup.get('UI_Font_Size', '12')))
            )
            rb.grid(row=0, column=i, padx=2, sticky='ew')
            rb.bind("<Enter>", lambda e, b=rb: b.config(bg="#2196f3", fg='white'))
            rb.bind("<Leave>", lambda e, b=rb: self.update_radio_bg())
            self.section_radiobuttons.append(rb)
        self.update_radio_bg()

        # 添加說明文字
        self.section_description = ttk.Label(
            section_frame, 
            text=self.get_section_description('全部指令'),
            style="TLabel",
            wraplength=300
        )
        self.section_description.grid(row=1, column=0, columnspan=4, pady=5, sticky='w')
        
        cmd_frame = ttk.Frame(self.left_panel, style="TFrame")
        cmd_frame.grid(row=2, column=0, sticky='ew', pady=5)
        cmd_frame.columnconfigure(1, weight=1)
        self.label_cmd = ttk.Label(cmd_frame, text='指令:', style="TLabel")
        self.label_cmd.grid(row=0, column=0, sticky='w')
        self.combobox_cmd = ttk.Combobox(cmd_frame, state='readonly', width=25)
        self.combobox_cmd.grid(row=0, column=1, padx=5, sticky='ew')

    def get_section_description(self, section):
        descriptions = {
            '全部指令': '顯示所有可用的指令',
            '單板指令': '用於單板測試的指令集',
            '整機指令': '用於整機測試的指令集',
            '出貨指令': '用於出貨測試的指令集'
        }
        return descriptions.get(section, '')

    def init_ping_components(self):
        print('[DEBUG] handlers in init_ping_components:', self.parent.handlers)
        ping_frame = ttk.LabelFrame(self.left_panel, text='Ping 檢查', padding=10, style="TLabelframe")
        ping_frame.grid(row=3, column=0, sticky='ew', pady=10)
        ip_frame = ttk.Frame(ping_frame, style="TFrame")
        ip_frame.grid(row=0, column=0, sticky='ew', pady=2)
        ip_frame.columnconfigure(1, weight=1)
        self.label_ip = ttk.Label(ip_frame, text='IP地址:', style="TLabel")
        self.label_ip.grid(row=0, column=0, sticky='w')
        self.entry_ip = ttk.Entry(ip_frame, width=15)
        self.entry_ip.grid(row=0, column=1, padx=5, sticky='ew')
        default_ip = self.parent.setup.get('Default_IP_Address', '192.168.11.143')
        self.entry_ip.delete(0, tk.END)
        self.entry_ip.insert(0, default_ip)
        self.btn_ping = tk.Button(ip_frame, text='Ping', command=lambda: self.parent.handlers.check_ping(), bg='white', fg='black')
        self.btn_ping.grid(row=0, column=2, padx=5)
        self.btn_ping.bind("<Enter>", lambda e: self.btn_ping.config(bg="#ff9999"))
        self.btn_ping.bind("<Leave>", lambda e: self.btn_ping.config(bg="white"))

    def init_settings_components(self):
        settings_frame = ttk.LabelFrame(self.left_panel, text='設定', padding=10, style="TLabelframe")
        settings_frame.grid(row=4, column=0, sticky='ew', pady=10)
        end_frame = ttk.Frame(settings_frame, style="TFrame")
        end_frame.grid(row=0, column=0, sticky='ew', pady=2)
        self.label_end = ttk.Label(end_frame, text='結束字串:', style="TLabel")
        self.label_end.grid(row=0, column=0, sticky='w')
        self.combobox_end = ttk.Combobox(end_frame, width=15)
        self.combobox_end.grid(row=0, column=1, padx=5, sticky='ew')
        self.update_end_strings()
        self.combobox_end.set(self.parent.setup.get('Command_End_String', 'root'))
        # 加入刪除按鈕
        self.btn_remove_end = tk.Button(end_frame, text='-', command=self.parent.handlers.remove_end_string, width=2, bg='#ffcccc', fg='black')
        self.btn_remove_end.grid(row=0, column=2, padx=2)
        timeout_frame = ttk.Frame(settings_frame, style="TFrame")
        timeout_frame.grid(row=1, column=0, sticky='ew', pady=2)
        self.label_timeout = ttk.Label(timeout_frame, text='超時(秒):', style="TLabel")
        self.label_timeout.grid(row=0, column=0, sticky='w')
        self.entry_timeout = ttk.Entry(timeout_frame, width=8)
        self.entry_timeout.grid(row=0, column=1, padx=5, sticky='ew')
        self.entry_timeout.insert(0, self.parent.setup.get('Command_Timeout_Seconds', '30'))
        font_frame = ttk.LabelFrame(settings_frame, text='字體大小設定', padding=5, style="TLabelframe")
        font_frame.grid(row=2, column=0, sticky='ew', pady=2)
        ui_font_frame = ttk.Frame(font_frame, style="TFrame")
        ui_font_frame.grid(row=0, column=0, sticky='ew', pady=2)
        self.label_ui_font = ttk.Label(ui_font_frame, text='介面字體大小:', style="TLabel")
        self.label_ui_font.grid(row=0, column=0, sticky='w')
        self.btn_ui_font_minus = tk.Button(ui_font_frame, text='－', width=2, command=lambda: self.ui_font_scale.set(self.ui_font_scale.get()-1))
        self.btn_ui_font_minus.grid(row=0, column=1, padx=2)
        self.ui_font_scale = tk.Scale(ui_font_frame, from_=8, to=20, orient='horizontal', 
                                    command=self.parent.handlers.change_ui_font_size, length=120, bg='white', fg='black', 
                                    highlightthickness=0)
        self.ui_font_scale.grid(row=0, column=2, padx=2)
        self.ui_font_scale.set(int(self.parent.setup.get('UI_Font_Size', '12')))
        self.btn_ui_font_plus = tk.Button(ui_font_frame, text='＋', width=2, command=lambda: self.ui_font_scale.set(self.ui_font_scale.get()+1))
        self.btn_ui_font_plus.grid(row=0, column=3, padx=2)
        self.label_ui_font_value = ttk.Label(ui_font_frame, text=str(self.ui_font_scale.get()), style="TLabel")
        self.label_ui_font_value.grid(row=0, column=4, padx=4)
        content_font_frame = ttk.Frame(font_frame, style="TFrame")
        content_font_frame.grid(row=1, column=0, sticky='ew', pady=2)
        self.label_content_font = ttk.Label(content_font_frame, text='內容字體大小:', style="TLabel")
        self.label_content_font.grid(row=0, column=0, sticky='w')
        self.content_font_scale = tk.Scale(content_font_frame, from_=8, to=20, orient='horizontal', 
                                         command=self.parent.handlers.change_content_font_size, length=150, bg='white', fg='black', 
                                         highlightthickness=0)
        self.content_font_scale.grid(row=0, column=1, padx=5)
        self.content_font_scale.set(int(self.parent.setup.get('Content_Font_Size', '12')))
        btn_frame = ttk.Frame(self.left_panel, style="TFrame")
        btn_frame.grid(row=5, column=0, sticky='ew', pady=10)
        self.btn_clear = ttk.Button(btn_frame, text='清空回應', command=self.parent.handlers.clear_output, style='Blue.TButton')
        self.btn_clear.grid(row=0, column=0, padx=2)
        self.btn_backup = ttk.Button(btn_frame, text='備份Log', command=self.parent.handlers.backup_output, style='Blue.TButton')
        self.btn_backup.grid(row=0, column=1, padx=2)
        self.btn_guide = ttk.Button(btn_frame, text='使用說明', command=self.parent.handlers.toggle_guide, style='Blue.TButton')
        self.btn_guide.grid(row=0, column=2, padx=2)
        # 將 ui_font_scale 的 command 綁定為 handlers.change_ui_font_size，避免 lambda 導致無法正確更新
        self.ui_font_scale.config(command=self.parent.handlers.change_ui_font_size)
        # label_ui_font_value 由 change_ui_font_size 內部主動更新
        
        # 添加倒數計時標籤 - 移到更明顯的位置
        countdown_frame = ttk.Frame(settings_frame, style="TFrame")
        countdown_frame.grid(row=3, column=0, sticky='ew', pady=5)
        countdown_frame.columnconfigure(0, weight=1)
        
        # 倒數計時標籤 - 使用更大的字體和明顯的顏色
        self.label_countdown = tk.Label(
            countdown_frame, 
            text='', 
            font=('Microsoft JhengHei UI', 16, 'bold'),
            fg='red',  # 紅色文字
            bg='white',  # 白色背景
            anchor='center'
        )
        self.label_countdown.grid(row=0, column=0, sticky='ew', padx=5, pady=2)

    def init_output_components(self):
        try:
            # 建立輸出區域
            self.text_output = scrolledtext.ScrolledText(
                self.right_panel,
                wrap=tk.WORD,
                width=50,
                height=20,
                font=('Microsoft JhengHei UI', int(self.parent.setup.get('Content_Font_Size', '12')))
            )
            self.text_output.grid(row=0, column=0, sticky='nsew')
            self.right_panel.grid_rowconfigure(0, weight=1)
            self.right_panel.grid_columnconfigure(0, weight=1)
            
            # 設定 tag
            self.text_output.tag_configure("send", foreground="blue")
            self.text_output.tag_configure("end", foreground="green")  # 收到結束字串為綠色
            self.text_output.tag_configure("timeout", foreground="red")  # 超時為紅色
            self.text_output.tag_configure("purple", foreground="#800080")  # 紫色
            
            # 設定唯讀
            self.text_output.config(state='disabled')
        except Exception as e:
            print(f"Error in init_output_components: {e}")
            raise

    def init_exec_button_left_panel(self):
        # 執行指令大圓角按鈕（預設灰色，hover 綠色），用 grid 固定在 left_panel 最下方
        exec_frame = ttk.Frame(self.left_panel, style="TFrame")
        exec_frame.grid(row=999, column=0, sticky='ew', pady=8)
        exec_frame.columnconfigure(0, weight=1)
        self.btn_exec = tk.Button(exec_frame, text='執行指令',
            command=self.parent.handlers.on_execute,
                                 bg='#cccccc', fg='black',
                                 activebackground='#4caf50', activeforeground='white',
                                 font=('Microsoft JhengHei UI', 20, 'bold'),
                                 relief='flat', borderwidth=0, highlightthickness=0)
        self.btn_exec.grid(row=0, column=0, sticky='ew', padx=4, pady=6)
        self.btn_exec.bind("<Enter>", lambda e: self.btn_exec.config(bg="#4caf50", fg='white'))
        self.btn_exec.bind("<Leave>", lambda e: self.btn_exec.config(bg="#cccccc", fg='black'))
        # 讓 left_panel 最下方 row 有 weight，確保按鈕永遠可見
        self.left_panel.grid_rowconfigure(999, weight=1)

    def init_progress_components(self):
        """初始化進度條組件"""
        self.progress = ttk.Progressbar(
            self.right_panel,
            mode='determinate',
            style="gray.Horizontal.TProgressbar",
            length=200
        )
        self.progress.grid(row=1, column=0, sticky='ew', pady=5)
        self.progress['value'] = 0
        # 確保進度條始終顯示
        self.progress.grid_remove()  # 初始隱藏
        self.right_panel.rowconfigure(1, weight=0)  # 進度條行不擴展

    def show_progress(self, show=True):
        """控制進度條顯示/隱藏"""
        print(f"[DEBUG] show_progress: show={show}")
        if show:
            self.progress.grid()
        else:
            self.progress.grid_remove()

    def update_progress(self, value, style="blue.Horizontal.TProgressbar"):
        """更新進度條值和樣式"""
        print(f"[DEBUG] update_progress: value={value}, style={style}")
        self.progress.config(style=style, value=value)
        self.progress.grid()  # 確保進度條顯示

    def reset_progress(self):
        """重置進度條"""
        print("[DEBUG] reset_progress: set progress to 0 and hide")
        self.progress.config(style="gray.Horizontal.TProgressbar", value=0)
        self.show_progress(False)

    def update_radio_bg(self):
        selected = self.section_var.get()
        for rb, sec in zip(self.section_radiobuttons, self.sections):
            if rb['state'] == 'disabled':
                rb.config(bg="#e0e0e0", fg="#b0b0b0", activebackground="#e0e0e0", activeforeground="#b0b0b0")
            elif selected == sec:
                rb.config(bg="#2196f3", fg="white", activebackground="#2196f3", activeforeground="white")
            else:
                rb.config(bg="#d9d9d9", fg="black", activebackground="#d9d9d9", activeforeground="black")

    def update_cmd_list(self):
        self.update_radio_bg()
        section = self.section_var.get()
        # 更新說明文字
        self.section_description.config(text=self.get_section_description(section))
        # 重新讀取 command.txt
        self.parent.commands_by_section = self.parent.handlers.parse_commands_by_section()
        cmds = self.parent.commands_by_section.get(section, {})
        self.combobox_cmd['values'] = list(cmds.keys())
        # 自動選中第一個指令
        if cmds:
            first_cmd = list(cmds.keys())[0]
            self.combobox_cmd.set(first_cmd)
        else:
            self.combobox_cmd.set('')

    def update_end_strings(self):
        try:
            end_strings = json.loads(self.parent.setup.get('Available_End_Strings', '["root"]'))
        except Exception:
            end_strings = ['root']
        self.combobox_end['values'] = end_strings

    def add_to_buffer(self, text, tag=None):
        # 設為可編輯狀態
        self.text_output.configure(state='normal')
        
        # 若是 [送出] 開頭自動用 send tag
        if text.startswith('[發送]'):
            self.text_output.insert(tk.END, text, "send")
        # 若是 [結束] 開頭自動用 end tag
        elif text.startswith('[結束]'):
            self.text_output.insert(tk.END, text, "end")
        # 若是包含 inserted 的行，使用 purple tag
        elif "inserted" in text:
            self.text_output.insert(tk.END, text, "purple")
        # 其他情況使用指定的 tag
        elif tag:
            self.text_output.insert(tk.END, text, tag)
        else:
            self.text_output.insert(tk.END, text)
        
        # 自動捲到最底
        self.text_output.see(tk.END)
        # 設回唯讀狀態
        self.text_output.configure(state='disabled')

    def flush_buffer(self):
        if not self.parent.text_buffer:
            return
        self.text_output.configure(state='normal')
        for text, tag in self.parent.text_buffer:
            if tag:
                self.text_output.insert(tk.END, text, tag)
            else:
                self.text_output.insert(tk.END, text)
        self.text_output.see(tk.END)  # 自動捲到最底
        self.text_output.configure(state='disabled')  # 設回唯讀狀態
        self.parent.text_buffer = []

    def update_ui_fonts(self, size=None):
        try:
            if size is None:
                size = int(self.ui_font_scale.get())
            font = ('Microsoft JhengHei UI', size)
            # 更新所有標籤和按鈕
            widgets = [
                self.label_com, self.label_cmd, self.label_end, self.label_timeout,
                self.label_ui_font, self.label_content_font, self.btn_refresh,
                self.btn_clear, self.btn_backup, self.btn_guide, self.label_ip, self.btn_ping
            ]
            for w in widgets:
                if w.winfo_exists():
                    w.configure(font=font)
            # 更新 section_radiobuttons 字體
            for rb in getattr(self, 'section_radiobuttons', []):
                if rb.winfo_exists():
                    rb.configure(font=font)
            # 更新輸入框和下拉選單
            for widget in [self.combobox_com, self.combobox_cmd, self.combobox_end, 
                         self.entry_timeout, self.entry_ip]:
                if widget.winfo_exists():
                    widget.configure(font=('Consolas', size))
            # 更新 ttk 樣式
            style = ttk.Style()
            style.configure("TLabelframe.Label", font=font)
            style.configure("TLabelframe", font=font)
            style.configure("TLabel", font=font)
            # 強制更新 UI
            self.parent.root.update_idletasks()
        except Exception as e:
            print(f"更新介面字體時發生錯誤: {e}")

    def update_content_fonts(self, size=None):
        try:
            if size is None:
                size = int(self.content_font_scale.get())
            content_font = ('Consolas', size)
            # 更新文字輸出區域
            if self.text_output.winfo_exists():
                self.text_output.configure(font=content_font)
            # 更新所有下拉選單與輸入框
            for widget in [self.combobox_com, self.combobox_cmd, self.combobox_end, self.entry_timeout, self.entry_ip]:
                if widget.winfo_exists():
                    widget.configure(font=content_font)
            # 根據字體大小自動調整 combobox_cmd 寬度
            min_width = 25
            width = max(min_width, int(size * 2.2))
            self.combobox_cmd.config(width=width)
            # 強制 combobox 下拉選單選項字體同步
            try:
                self.parent.root.option_add('*TCombobox*Listbox.font', content_font)
            except Exception as e:
                print(f'Combobox Listbox 字體設置失敗: {e}')
            # 更新使用說明視窗
            if self.parent.guide_window and self.parent.guide_window.winfo_exists():
                for widget in self.parent.guide_window.winfo_children():
                    if isinstance(widget, scrolledtext.ScrolledText) and widget.winfo_exists():
                        widget.configure(font=content_font)
            self.parent.root.update_idletasks()
        except Exception as e:
            print(f"更新內容字體時發生錯誤: {e}")

    def on_window_resize(self, event):
        # 只在主視窗且尺寸真的有變時記錄
        if event.widget == self.parent.root:
            w, h = event.width, event.height
            if (w, h) != self.last_size and w > 200 and h > 200:
                self.last_size = (w, h)
                # 更新當前設定
                self.parent.setup['Window_Width'] = str(w)
                self.parent.setup['Window_Height'] = str(h)
                # 保存完整的設定結構
                from config import load_setup, save_setup
                full_setup = load_setup()
                full_setup['DUT_Control'].update({
                    'Window_Width': str(w),
                    'Window_Height': str(h)
                })
                save_setup(full_setup)
                print(f"[DEBUG] 視窗大小已保存: {w}x{h}")
        # 不再自動縮放字體

    def start_led_blink(self):
        self.led_blinking = True
        self._blink_led()

    def _blink_led(self):
        if not self.led_blinking:
            return
        current_color = self.status_canvas.itemcget(self.status_light, 'fill')
        next_color = 'green' if current_color == 'black' else 'black'
        self.status_canvas.itemconfig(self.status_light, fill=next_color)
        self.status_canvas.after(300, self._blink_led)

    def stop_led_blink(self):
        self.led_blinking = False
        self.status_canvas.itemconfig(self.status_light, fill='black')

    def on_pane_drag_start(self, event):
        self.main_frame.start_x = event.x
        self.main_frame.start_y = event.y

    def on_pane_drag_end(self, event):
        dx = event.x - self.main_frame.start_x
        dy = event.y - self.main_frame.start_y
        self.main_frame.move(dx, dy)

    def on_pane_position_changed(self, event):
        """當 PanedWindow 分割位置改變時保存位置"""
        try:
            # 獲取當前分割位置
            sash_position = self.main_frame.sashpos(0)  # 第一個分割線的位置
            print(f"[DEBUG] PanedWindow 分割位置變更: {sash_position}")
            
            # 保存到設定中
            self.parent.setup['Pane_Sash_Position'] = str(sash_position)
            
            # 保存完整的設定結構
            from config import load_setup, save_setup
            full_setup = load_setup()
            full_setup['DUT_Control']['Pane_Sash_Position'] = str(sash_position)
            save_setup(full_setup)
            
        except Exception as e:
            print(f"[DEBUG] 保存分割位置時發生錯誤: {e}")

    def restore_pane_position(self):
        """恢復 PanedWindow 分割位置"""
        try:
            # 從設定中讀取分割位置
            sash_position = self.parent.setup.get('Pane_Sash_Position', '')
            if sash_position:
                position = int(sash_position)
                # 確保位置在合理範圍內
                window_width = self.parent.root.winfo_width()
                if 100 <= position <= window_width - 100:
                    self.main_frame.sashpos(0, position)
                    print(f"[DEBUG] 已恢復 PanedWindow 分割位置: {position}")
                else:
                    print(f"[DEBUG] 分割位置 {position} 超出範圍，使用預設位置")
            else:
                print(f"[DEBUG] 沒有保存的分割位置，使用預設位置")
        except Exception as e:
            print(f"[DEBUG] 恢復分割位置時發生錯誤: {e}")