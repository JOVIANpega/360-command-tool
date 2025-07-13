# -*- coding: utf-8 -*-
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import traceback
import json

# 設置路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def write_log(msg):
    try:
        with open("test_run_log.txt", "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

write_log("test_main.py 啟動")

# 簡化版的TabManager
class SimpleTabManager:
    def __init__(self, root):
        self.root = root
        
        # 創建一個簡單的notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)
        
        # 創建幾個分頁
        self.dut_frame = ttk.Frame(self.notebook)
        self.settings_frame = ttk.Frame(self.notebook)
        
        # 添加分頁到notebook
        self.notebook.add(self.dut_frame, text='DUT 控制')
        self.notebook.add(self.settings_frame, text='設定')
        
        # 在DUT分頁中添加一些控件
        self.init_dut_tab()
        
        # 在設定分頁中添加一些控件
        self.init_settings_tab()
    
    def init_dut_tab(self):
        # 創建一個簡單的界面
        frame = ttk.Frame(self.dut_frame, padding=20)
        frame.pack(fill='both', expand=True)
        
        # COM口選擇
        com_frame = ttk.Frame(frame)
        com_frame.pack(fill='x', pady=10)
        
        ttk.Label(com_frame, text='COM口:').pack(side='left')
        self.com_combo = ttk.Combobox(com_frame, values=['COM1', 'COM2', 'COM3'], state='readonly')
        self.com_combo.pack(side='left', padx=5)
        self.com_combo.set('COM1')
        
        # 指令分類按鈕
        section_frame = ttk.LabelFrame(frame, text='指令分類')
        section_frame.pack(fill='x', pady=10)
        
        self.section_var = tk.StringVar(value='測試指令')
        sections = ['測試指令', '單板指令', '整機指令']
        
        for i, section in enumerate(sections):
            rb = tk.Radiobutton(section_frame, text=section, variable=self.section_var, value=section)
            rb.grid(row=0, column=i, padx=5, pady=5)
        
        # 指令下拉選單
        cmd_frame = ttk.Frame(frame)
        cmd_frame.pack(fill='x', pady=10)
        
        ttk.Label(cmd_frame, text='指令:').pack(side='left')
        self.cmd_combo = ttk.Combobox(cmd_frame, values=['指令1', '指令2', '指令3'], state='readonly')
        self.cmd_combo.pack(side='left', padx=5, fill='x', expand=True)
        self.cmd_combo.set('指令1')
        
        # 執行按鈕
        self.exec_btn = ttk.Button(frame, text='執行指令', command=self.on_execute)
        self.exec_btn.pack(pady=10)
        
        # 輸出區域
        output_frame = ttk.LabelFrame(frame, text='輸出')
        output_frame.pack(fill='both', expand=True, pady=10)
        
        self.output_text = tk.Text(output_frame, wrap='word', height=10)
        self.output_text.pack(fill='both', expand=True)
        
    def init_settings_tab(self):
        # 創建一個簡單的設定界面
        frame = ttk.Frame(self.settings_frame, padding=20)
        frame.pack(fill='both', expand=True)
        
        # 指令檔路徑
        path_frame = ttk.Frame(frame)
        path_frame.pack(fill='x', pady=10)
        
        ttk.Label(path_frame, text='指令檔路徑:').pack(side='left')
        self.path_entry = ttk.Entry(path_frame)
        self.path_entry.pack(side='left', padx=5, fill='x', expand=True)
        self.path_entry.insert(0, 'Command_TABLE/command.txt')
        
        self.browse_btn = ttk.Button(path_frame, text='...', width=3, command=self.browse_file)
        self.browse_btn.pack(side='left')
        
        # 保存設定按鈕
        self.save_btn = ttk.Button(frame, text='保存設定', command=self.save_settings)
        self.save_btn.pack(pady=10)
    
    def on_execute(self):
        cmd = self.cmd_combo.get()
        self.output_text.insert('end', f'執行指令: {cmd}\n')
    
    def browse_file(self):
        messagebox.showinfo('選擇檔案', '這裡應該彈出檔案選擇對話框')
        self.path_entry.delete(0, 'end')
        self.path_entry.insert(0, 'Command_TABLE/Fixture_Command.txt')
    
    def save_settings(self):
        path = self.path_entry.get()
        messagebox.showinfo('保存設定', f'設定已保存！指令檔路徑: {path}')

if __name__ == "__main__":
    log_file = "test_error.txt"
    try:
        # 創建主窗口
        root = tk.Tk()
        app = SimpleTabManager(root)
        
        # 設置窗口標題和大小
        root.title('VALO360 指令通 (測試版)')
        root.geometry('800x600')
        
        # 啟動應用程式
        root.mainloop()

    except Exception as e:
        import traceback
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"An unexpected error occurred: {e}\n")
            f.write(traceback.format_exc())
        print(f"An error occurred. Details have been written to {log_file}") 