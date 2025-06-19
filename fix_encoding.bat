@echo off
echo VALO360 指令通 - 編碼修復腳本
echo.

rem 創建 Python 腳本來修復編碼
echo import os, sys, codecs > fix_encoding.py
echo. >> fix_encoding.py
echo def fix_file(file_path): >> fix_encoding.py
echo     print(f"處理檔案: {file_path}") >> fix_encoding.py
echo     try: >> fix_encoding.py
echo         with open(file_path, 'rb') as f: >> fix_encoding.py
echo             content = f.read() >> fix_encoding.py
echo         # 嘗試不同的編碼 >> fix_encoding.py
echo         encodings = ['utf-8', 'big5', 'gbk', 'cp950', 'cp936'] >> fix_encoding.py
echo         decoded = None >> fix_encoding.py
echo         used_encoding = None >> fix_encoding.py
echo         for enc in encodings: >> fix_encoding.py
echo             try: >> fix_encoding.py
echo                 decoded = content.decode(enc) >> fix_encoding.py
echo                 used_encoding = enc >> fix_encoding.py
echo                 break >> fix_encoding.py
echo             except UnicodeDecodeError: >> fix_encoding.py
echo                 continue >> fix_encoding.py
echo         if decoded is None: >> fix_encoding.py
echo             print(f"  無法解碼檔案: {file_path}") >> fix_encoding.py
echo             return False >> fix_encoding.py
echo         # 使用 UTF-8 編碼寫入檔案 >> fix_encoding.py
echo         with open(file_path + '.bak', 'wb') as f: >> fix_encoding.py
echo             f.write(content) >> fix_encoding.py
echo         with open(file_path, 'w', encoding='utf-8') as f: >> fix_encoding.py
echo             f.write(decoded) >> fix_encoding.py
echo         print(f"  成功將檔案從 {used_encoding} 轉換為 UTF-8: {file_path}") >> fix_encoding.py
echo         return True >> fix_encoding.py
echo     except Exception as e: >> fix_encoding.py
echo         print(f"  處理檔案時發生錯誤: {file_path}, 錯誤: {e}") >> fix_encoding.py
echo         return False >> fix_encoding.py
echo. >> fix_encoding.py
echo def process_directory(directory): >> fix_encoding.py
echo     success_count = 0 >> fix_encoding.py
echo     fail_count = 0 >> fix_encoding.py
echo     for root, dirs, files in os.walk(directory): >> fix_encoding.py
echo         for file in files: >> fix_encoding.py
echo             if file.endswith('.py'): >> fix_encoding.py
echo                 file_path = os.path.join(root, file) >> fix_encoding.py
echo                 if fix_file(file_path): >> fix_encoding.py
echo                     success_count += 1 >> fix_encoding.py
echo                 else: >> fix_encoding.py
echo                     fail_count += 1 >> fix_encoding.py
echo     return success_count, fail_count >> fix_encoding.py
echo. >> fix_encoding.py
echo if __name__ == "__main__": >> fix_encoding.py
echo     print("開始修復 Python 檔案編碼...") >> fix_encoding.py
echo     directories = ['.', 'ui_parts'] >> fix_encoding.py
echo     total_success = 0 >> fix_encoding.py
echo     total_fail = 0 >> fix_encoding.py
echo     for directory in directories: >> fix_encoding.py
echo         print(f"處理目錄: {directory}") >> fix_encoding.py
echo         success, fail = process_directory(directory) >> fix_encoding.py
echo         total_success += success >> fix_encoding.py
echo         total_fail += fail >> fix_encoding.py
echo     print(f"完成! 成功轉換 {total_success} 個檔案，失敗 {total_fail} 個檔案") >> fix_encoding.py

rem 執行 Python 腳本
echo 執行編碼修復腳本...
python fix_encoding.py

echo.
echo 編碼修復完成，現在可以嘗試打包了
echo 使用以下命令打包:
echo pyinstaller --onefile --clean --noconfirm --icon=app.ico -w --version-file=version_info.txt --add-data "command.txt;." --add-data "user_guide.txt;." --add-data "setup.json;." --add-data "app.ico;." --name "VALO360指令通" main.py
echo.

pause 