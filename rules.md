1. 使用 Python 優先使用 Tkinter 開發 GUI（簡單穩定，適合打包），必要時可使用：ttk, customtkinter, Pillow, os, subprocess, re, threading 等。
2. UI 元素需包含標題欄、輸入欄、按鈕與輸出欄（根據需求增加），採用固定大小視窗（例如 600x400），視覺簡潔，使用清楚標籤名稱，避免預設名稱如 "Button1"，輸出結果須顯示於 Text 或 Label 中，不可只用終端輸出。
3. 程式需具備基本錯誤處理（try-except），函式獨立定義，避免全部寫在 UI callback 中，使用清楚註解與有意義的變數名稱，模組化撰寫，避免過長 main function。
4. 所有資源檔（圖示、圖片、外部檔案）放置於 assets/ 資料夾，使用下列指令打包為單一檔案：
   `pyinstaller --onefile --noconsole --icon=assets/icon.ico app.py`
   使用 `sys._MEIPASS` 支援打包後的相對路徑存取。
5. 顯示範例輸入與輸出畫面，協助使用者理解用法。
6. 可在本機以 `python app.py` 測試，也可用 PyInstaller 打包測試。
7. 當需求變複雜時可加入以下進階功能：多頁面 GUI 切換（使用 Frame）、設定檔讀寫（INI/JSON）、資料匯出（TXT/CSV）、多執行緒處理長時間任務（threading）、動態 UI 更新（例如進度條）。
8. 禁止使用 HTML、Flask、Electron 等網頁前端技術；禁止使用不支援打包的框架（如 PyQt6 無 license）；禁止寫死資源絕對路徑；GitHub 上傳需等我要求時才做，並需同時上傳本地與遠端版本。
9.超過300行代碼要切換新的PY
10. 所有函式應避免過長（建議單一函式不超過 50 行），並適當拆分重構，提升可讀性與維護性。
11. 程式檔案命名應清楚描述功能，禁止使用無意義名稱如 test.py、temp.py 等，並統一使用小寫 + 底線命名風格（例如：log_parser.py）。
12. 若 GUI 有多個頁面或功能模組，請使用 class 管理畫面元件，避免全域變數過多。
13. 若需記錄錯誤或執行紀錄，應使用內建 logging 模組，避免以 print() 作為除錯手段。
14. 不可在主程式中直接操作資料夾建立與路徑判斷，應封裝為工具函式（例如 get_resource_path()）處理路徑與檔案存取。
15. 所有輸入欄（Entry/Text）需預設 placeholder 或提示標籤，避免使用者操作時混淆。
16. 所有按鈕的 callback 函式需以 on_ 開頭命名（如 on_submit_click()），並集中定義在一起，提升一致性與可讀性。
17.回答一律繁體中文