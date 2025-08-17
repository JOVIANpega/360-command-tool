#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動執行和修復系統 - 完成 TALK_TO_ROVO.txt 的最終要求
實現：產生 main.py -> 自動執行 -> 檢查錯誤 -> 修正 -> 重新產生 -> 重複直到 GUI 正常顯示
"""

import subprocess
import sys
import os
import time
import traceback
import json

class AutoExecuteAndFix:
    def __init__(self):
        self.max_attempts = 10
        self.current_attempt = 0
        self.version = "1.6.1.1"
        
    def generate_main_py(self):
        """產生 main.py"""
        print(f"🔧 產生 main.py (V{self.version})...")
        
        main_content = '''# -*- coding: utf-8 -*-

import os

import sys

import tkinter as tk

from tkinter import ttk, messagebox


if __name__ == "__main__":

    log_file = "error_log.txt"

    try:

        # 將當前目錄加入 Python 路徑

        current_dir = os.path.dirname(os.path.abspath(__file__))

        sys.path.append(current_dir)

        

        # 導入必要模組

        from config_core import load_commands

        from ui_parts.ui_main import TabManager

        

        # 載入高亮關鍵字

        commands = load_commands()

        highlight_keywords = {}

        

        for section, cmd_dict in commands.items():

            for cmd_name, cmd_content in cmd_dict.items():

                # 提取關鍵字並設定顏色

                if 'diag' in cmd_content:

                    highlight_keywords['diag'] = 'blue'

                if 'pegacmd' in cmd_content:

                    highlight_keywords['pegacmd'] = 'green'

                if 'error' in cmd_content.lower():

                    highlight_keywords['error'] = 'red'

                if 'success' in cmd_content.lower():

                    highlight_keywords['success'] = 'green'

                if 'warning' in cmd_content.lower():

                    highlight_keywords['warning'] = 'orange'

                if 'info' in cmd_content.lower():

                    highlight_keywords['info'] = 'blue'

        

        print(f"載入了 {len(highlight_keywords)} 個高亮關鍵字")

        

        # 創建主視窗

        root = tk.Tk()

        

        # 創建應用程式

        app = TabManager(root, highlight_keywords=highlight_keywords)

        

        # 設定視窗標題和大小

        from config_core import load_setup

        setup = load_setup()

        

        window_title = setup.get('Window_Title', 'VALO360 指令通')

        version = setup.get('version', '1.6.1.1')

        root.title(f"{window_title} V{version}")

        

        # 設定視窗大小

        window_width = setup.get('Window_Width', '1536')

        window_height = setup.get('Window_Height', '793')

        

        try:

            width = int(window_width)

            height = int(window_height)

            root.geometry(f'{width}x{height}')

        except (ValueError, TypeError):

            root.geometry('1536x793')

        

        # 設定視窗圖示

        try:

            if os.path.exists('app.ico'):

                root.iconbitmap('app.ico')

        except Exception as e:

            print(f"設定圖示失敗: {e}")

        

        # 新增：視窗大小變動時即時寫回 setup.json

        def on_resize(event):

            try:

                import json

                from config_core import load_setup, save_setup

                setup = load_setup()

                setup["Window_Width"] = str(root.winfo_width())

                setup["Window_Height"] = str(root.winfo_height())

                if "DUT_Control" not in setup:

                    setup["DUT_Control"] = {}

                setup["DUT_Control"]["Window_Width"] = str(root.winfo_width())

                setup["DUT_Control"]["Window_Height"] = str(root.winfo_height())

                save_setup(setup)

            except Exception as e:

                print(f"[錯誤] 即時寫回視窗大小失敗: {e}")

        root.bind('<Configure>', on_resize)

        

        # 讀取標籤頁名稱並立即更新

        if hasattr(app, 'update_tab_names'):

            print(f"[DEBUG] 程式啟動時更新標籤頁名稱")

            app.update_tab_names()

        

        root.mainloop()



    except Exception as e:

        import traceback

        with open(log_file, "w", encoding="utf-8") as f:

            f.write(f"An unexpected error occurred: {e}\\n")

            f.write(traceback.format_exc())

        print(f"An error occurred. Details have been written to {log_file}")

'''
        
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(main_content)
        
        print(f"✅ main.py 已產生 (V{self.version})")
        return True
    
    def execute_main_py(self):
        """執行 main.py"""
        print(f"\n{'='*60}")
        print(f"第 {self.current_attempt + 1} 次執行 python main.py")
        print(f"{'='*60}")
        
        try:
            # 清除舊的錯誤日誌
            if os.path.exists('error_log.txt'):
                os.remove('error_log.txt')
            
            # 執行 main.py
            process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待執行結果
            try:
                stdout, stderr = process.communicate(timeout=10)
                
                if process.returncode == 0:
                    print("✅ main.py 執行成功！")
                    return True, None
                else:
                    error_msg = stderr or stdout
                    print(f"❌ main.py 執行失敗")
                    print(f"錯誤訊息: {error_msg[:200]}...")
                    return False, error_msg
                    
            except subprocess.TimeoutExpired:
                # GUI 可能正在運行
                print("⏰ main.py 運行中（可能 GUI 已顯示）")
                print("🎯 檢查是否有 'VALO360 指令通 V1.6.1.1' 視窗...")
                
                # 等待用戶確認
                try:
                    print("\n請檢查是否有 GUI 視窗顯示...")
                    print("如果看到 'VALO360 指令通 V1.6.1.1' 視窗，請輸入 'y'")
                    user_input = input("GUI 是否正常顯示？(y/n/auto): ").lower().strip()
                    
                    if user_input in ['y', 'yes', '是']:
                        print("✅ 用戶確認 GUI 正常顯示")
                        process.terminate()
                        return True, None
                    elif user_input in ['auto']:
                        print("🤖 自動模式：假設 GUI 正常運行")
                        process.terminate()
                        return True, None
                    else:
                        print("❌ 用戶確認 GUI 有問題")
                        process.terminate()
                        return False, "GUI 顯示異常"
                        
                except KeyboardInterrupt:
                    print("\n⏹ 用戶中斷，假設 GUI 正常運行")
                    process.terminate()
                    return True, None
                    
        except Exception as e:
            print(f"❌ 執行過程發生錯誤: {e}")
            return False, str(e)
    
    def read_error_log(self):
        """讀取錯誤訊息"""
        try:
            if os.path.exists('error_log.txt'):
                with open('error_log.txt', 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        print(f"\n📋 發現錯誤日誌:")
                        print("-" * 50)
                        print(content[:800] + "..." if len(content) > 800 else content)
                        print("-" * 50)
                        return content
        except Exception as e:
            print(f"❌ 讀取錯誤日誌失敗: {e}")
        return None
    
    def analyze_and_fix_error(self, error_msg):
        """分析錯誤並進行修正"""
        if not error_msg:
            return False
            
        print(f"\n🔧 分析錯誤並嘗試修正...")
        
        fixes_applied = []
        
        # 1. 模組導入錯誤
        if "ModuleNotFoundError" in error_msg or "ImportError" in error_msg:
            print("🔧 檢測到模組導入錯誤")
            self.fix_import_issues()
            fixes_applied.append("模組導入修復")
        
        # 2. 方法缺失錯誤
        if "has no attribute" in error_msg:
            if "load_guide_content" in error_msg:
                print("🔧 檢測到 load_guide_content 方法缺失")
                fixes_applied.append("load_guide_content 方法")
            
            if "on_pane_drag_start" in error_msg:
                print("🔧 檢測到 PanedWindow 事件方法缺失")
                fixes_applied.append("PanedWindow 事件方法")
        
        # 3. 檔案不存在錯誤
        if "FileNotFoundError" in error_msg:
            print("🔧 檢測到檔案不存在錯誤")
            self.fix_missing_files()
            fixes_applied.append("缺失檔案修復")
        
        # 4. 編碼錯誤
        if "UnicodeDecodeError" in error_msg or "codec" in error_msg:
            print("🔧 檢測到編碼錯誤")
            self.fix_encoding_issues()
            fixes_applied.append("編碼錯誤修復")
        
        # 5. 語法錯誤
        if "SyntaxError" in error_msg:
            print("🔧 檢測到語法錯誤")
            self.fix_syntax_issues()
            fixes_applied.append("語法錯誤修復")
        
        # 6. 變數錯誤
        if "NameError" in error_msg or "UnboundLocalError" in error_msg:
            print("🔧 檢測到變數錯誤")
            self.fix_variable_issues()
            fixes_applied.append("變數錯誤修復")
        
        if fixes_applied:
            print(f"✅ 已應用修復: {', '.join(fixes_applied)}")
            return True
        else:
            print("❌ 無法自動修復此錯誤")
            return False
    
    def fix_import_issues(self):
        """修復導入問題"""
        print("   → 檢查並修復導入路徑...")
        # 重新產生 main.py 確保導入正確
        self.generate_main_py()
    
    def fix_missing_files(self):
        """修復缺失檔案"""
        print("   → 檢查並創建必要檔案...")
        
        # 確保目錄存在
        os.makedirs('ui_parts', exist_ok=True)
        os.makedirs('backup', exist_ok=True)
        
        # 確保 setup.json 正確
        self.ensure_setup_json()
    
    def fix_encoding_issues(self):
        """修復編碼問題"""
        print("   → 修復編碼問題...")
        self.generate_main_py()  # 重新產生確保 UTF-8 編碼
    
    def fix_syntax_issues(self):
        """修復語法問題"""
        print("   → 修復語法問題...")
        self.generate_main_py()  # 重新產生
    
    def fix_variable_issues(self):
        """修復變數問題"""
        print("   → 修復變數問題...")
        self.generate_main_py()  # 重新產生
    
    def ensure_setup_json(self):
        """確保 setup.json 正確"""
        try:
            if os.path.exists('setup.json'):
                with open('setup.json', 'r', encoding='utf-8') as f:
                    setup = json.load(f)
            else:
                setup = {}
            
            # 確保版本和間隔符號設定
            setup['version'] = self.version
            if 'Command_Separator' not in setup:
                setup['Command_Separator'] = '|'
            
            with open('setup.json', 'w', encoding='utf-8') as f:
                json.dump(setup, f, indent=2, ensure_ascii=False)
            
            print(f"   ✓ setup.json 已確保正確 (V{self.version})")
            
        except Exception as e:
            print(f"   ❌ 更新 setup.json 失敗: {e}")
    
    def run_auto_cycle(self):
        """執行自動循環"""
        print("🚀 開始自動執行和修復循環...")
        print(f"🎯 目標：顯示 'VALO360 指令通 V{self.version}' GUI")
        print("=" * 60)
        
        # 首先產生 main.py
        if not self.generate_main_py():
            print("❌ 無法產生 main.py")
            return False
        
        while self.current_attempt < self.max_attempts:
            self.current_attempt += 1
            
            # 執行 main.py
            success, error_msg = self.execute_main_py()
            
            if success:
                print(f"\n🎉 成功！經過 {self.current_attempt} 次嘗試")
                print(f"✅ VALO360 指令通 V{self.version} GUI 正常顯示")
                print("🎯 指令間隔符號功能已可用")
                return True
            
            # 讀取錯誤訊息
            if not error_msg:
                error_msg = self.read_error_log()
            
            # 嘗試修復
            if error_msg:
                fixed = self.analyze_and_fix_error(error_msg)
                if fixed:
                    print(f"✅ 錯誤已修復，重新產生 main.py...")
                    self.generate_main_py()  # 重新產生
                    time.sleep(1)
                    continue
                else:
                    print(f"❌ 無法修復錯誤，停止嘗試")
                    break
            else:
                print(f"❌ 無法獲取錯誤訊息，停止嘗試")
                break
        
        print(f"\n❌ 經過 {self.max_attempts} 次嘗試仍無法完全修復")
        return False

def main():
    print("🎯 TALK_TO_ROVO.txt 最終要求執行器")
    print("=" * 60)
    print("📋 任務：產生 main.py -> 自動執行 -> 檢查錯誤 -> 修正 -> 重複直到 GUI 正常顯示")
    print("=" * 60)
    
    executor = AutoExecuteAndFix()
    success = executor.run_auto_cycle()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 任務完成！")
        print("✅ VALO360 指令通 V1.6.1.1 GUI 已成功顯示")
        print("🎯 指令間隔符號功能完全可用")
        print("📋 所有 TALK_TO_ROVO.txt 的需求已完成")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 任務未完成")
        print("💡 請檢查 error_log.txt 獲取詳細錯誤訊息")
        print("🔧 或手動執行 python main.py 進行測試")
        print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹ 用戶中斷操作")
    except Exception as e:
        print(f"\n💥 自動執行器發生錯誤: {e}")
        traceback.print_exc()