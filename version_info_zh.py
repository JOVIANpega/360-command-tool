# -*- coding: utf-8 -*-

"""

生成 PyInstaller 版本資訊檔案

"""



import os
import sys
import datetime

version_info = {
    'version': '2.1.5',
    'file_version': (2, 1, 5, 0),
    'product_version': (2, 1, 5, 0),
    'company_name': 'PEGA指令通',
    'file_description': 'PEGA指令通 - 序列埠通訊工具',
    'internal_name': 'PEGA指令通',
    'legal_copyright': '© 2024 PEGA指令通',
    'original_filename': 'main.exe',
    'product_name': 'PEGA指令通',
    'comments': '用於PEGA設備的序列埠通訊控制工具'
}

# 版本更新記錄
version_history = """
v1.6.0.3 (2025-01-28)
----------------------
• 全域通知系統優化：
  - 新增「呼吸顯示」效果，自動處理長文字顯示
  - 長訊息自動分行，每行顯示2.5秒後輪流切換
  - 通知字體大小控制按鈕 [+][-] 直接整合到通知區域
  - 字體大小設定自動儲存至 setup.json
• ToolTip 與全域通知整合強化：
  - 修復 ToolTip 顯示在全域通知欄的功能
  - 確保所有頁面的 ToolTip 都能正確顯示在通知欄
  - 滑鼠離開元件時自動清除通知
• 程式架構改進：
  - 優化全域通知管理器的傳遞機制
  - 確保設定頁面的 ToolTip 也能使用全域通知
  - 提升通知系統的穩定性和使用者體驗

v1.6.0.2 (2025-01-27)
----------------------
• AI ToolTip 系統完整實現：
  - 新增 AI 自動生成 ToolTip 內容功能
  - 建立 tooltip_config.txt 配置檔案，支援友善中文說明
  - 所有按鈕、COMBOBOX 等 UI 元件皆有對應 ToolTip
  - ToolTip 內容同時顯示在元件旁和全域通知區域
  - 支援從配置檔案讀取說明，無需修改程式碼
• 全域通知系統優化：
  - 新增 clear_notification() 方法
  - ToolTip 與全域通知區域聯動顯示
  - 滑鼠離開元件時自動清除通知
• 程式架構改進：
  - 重構 ToolTip 管理器，支援配置檔案讀取
  - 優化元件識別與說明文字匹配邏輯
  - 提升程式穩定性和使用者體驗

v1.6.0.1 (2025-01-27)
----------------------
• 基礎 ToolTip 系統建立：
  - 實現基本 ToolTip 顯示功能
  - 支援按鈕、下拉選單等元件
  - 可啟用/停用 ToolTip 功能

v1.6.0.0 (2025-07-18)
----------------------
• 設定儲存功能修復與穩定性提升：
  - 解決因 config 與 config_core 模組衝突導致的儲存失敗問題。
  - 修正重複銷毀視窗造成的 TclError。
  - 移除重複與無效的程式碼，提升穩定性。
• 使用者介面優化：
  - 簡化設定頁面，移除多餘的設定項目。

v1.5.0.9 (2025-07-17)
----------------------
• 設定檔案系統優化與GUI結構重新設計：
  - 修復設定檔案載入錯誤，解決重複設定項目問題
  - 建立統一設定管理系統，實現跨模組變數同步聯動
  - 治具設定完全移動至「TAB 測試治具」，儲存按鈕重新設計
  - 強化錯誤處理與穩定性，代碼品質全面提升

v1.5.0.8 (2025-07-16)
----------------------
• 系統設定頁面優化：
  - 指令檔案路徑欄位寬度調整為150字元，支援更長的檔案路徑顯示
  - 儲存按鈕尺寸加大（width=15）並移至頁面上方，提升可見性與操作便利性
  - 改善設定頁面整體佈局與使用者體驗

v1.5.0.7 (2025-07-16)
===================
✅ 制具控制頁面UI優化與功能整合
• 測試類別單選邏輯優化 - 勾選時自動取消其他選項
• 整合測試類別選擇與指令控制到同一區塊
• 調整欄位寬度與按鈕間距，提升使用體驗  
• 修正清除按鈕功能，正確清除執行結果區域
• 從檔案讀取說明文字並顯示在固定區域
• 統一字體大小控制，與設定頁聯動

🔧 技術修復
• 修復ttk元件font參數錯誤問題
• 優化布局配置，使介面更緊湊對齊
• 保持外部檔案讀取邏輯，避免硬編碼
• 完善錯誤處理與日誌記錄

v1.5.0.6 (2025-07-16)
===================
✅ 重新整理制具控制頁面 Layout
• 完成串列設定整合與檔案讀取功能
• 新增串列埠參數完整配置(波特率、資料位、停止位、奇偶校驗、超時)
• 設定頁面新增制具控制串列參數設定區域
• 制具控制頁面顯示當前串列連接參數資訊
• 優化制具指令檔案讀取與分類顯示功能

v1.5.0.5 (2025-07-15)
===================
✅ ToolTip提示系統完整整合
• 為所有GUI按鈕新增詳細的ToolTip說明
• 設定頁面新增ToolTip開關選項
• ToolTip設定與setup.json同步儲存
• 執行指令按鈕尺寸優化，提升點擊體驗
• 確保按鈕位置配置保持穩定

v1.5.0.4 (2025-07-15)  
===================
✅ 介面優化與使用體驗改善
• 調整執行指令按鈕尺寸，更加醒目易點擊
• 優化按鈕間距與對齊配置
• 改善整體視覺設計與操作流暢度

v1.5.0.3 (2025-07-15)
===================
✅ 系統穩定性與功能優化
• 修復多項系統異常與記憶體洩漏問題
• 優化設定檔備份機制與錯誤處理
• 改善串列埠連接穩定性
• 提升整體執行效能與回應速度

v1.5.0.2 (2025-07-14) 
===================
✅ 核心功能完善與穩定化
• 完成主要功能模組化重構
• 修復設定檔案讀寫相關問題  
• 優化UI元件載入與初始化流程
• 改善錯誤日誌記錄機制

v1.5.0.1 (2025-07-12)
===================
✅ 初始版本發布
• 建立基本序列埠通訊功能
• 實現指令檔案讀取與執行
• 完成基礎GUI介面設計
• 新增設定檔案管理功能
"""

# 定義版本號
VERSION = version_info['version']

APP_VERSION = "V2.1.5"
APP_VERSION_DETAIL = "\n【V2.1.5 主要更新】\n- 治具控制TAB字体联动功能\n- COM口连接稳定性改进\n- 指令格式统一优化\n"

# 生成版本資訊檔案
with open("version_info_zh.txt", "w", encoding="utf-8") as f:
    f.write("VSVersionInfo(\n")
    f.write("  ffi=FixedFileInfo(\n")
    f.write("    filevers=(2, 1, 5, 0),\n")
    f.write("    prodvers=(2, 1, 5, 0),\n")
    f.write("    mask=0x3f,\n")
    f.write("    flags=0x0,\n")
    f.write("    OS=0x40004,\n")
    f.write("    fileType=0x1,\n")
    f.write("    subtype=0x0,\n")
    f.write("    date=(0, 0)\n")
    f.write("  ),\n")
    f.write("  kids=[\n")
    f.write("    StringFileInfo(\n")
    f.write("      [\n")
    f.write("        StringTable(\n")
    f.write("          u'040904B0',\n")
    f.write("          [StringStruct(u'CompanyName', u'PEGA'),\n")
    f.write("           StringStruct(u'FileDescription', u'PEGA指令通'),\n")
    f.write("           StringStruct(u'FileVersion', u'" + VERSION + "'),\n")
    f.write("           StringStruct(u'InternalName', u'PEGA指令通'),\n")
    f.write("           StringStruct(u'LegalCopyright', u'Copyright (C) 2025 PEGA'),\n")
    f.write("           StringStruct(u'OriginalFilename', u'PEGA指令通.exe'),\n")
    f.write("           StringStruct(u'ProductName', u'PEGA指令通'),\n")
    f.write("           StringStruct(u'ProductVersion', u'" + VERSION + "')]\n")
    f.write("        )\n")
    f.write("      ]),\n")
    f.write("    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])\n")
    f.write("  ]\n")
    f.write(")\n")

print(f"已生成版本資訊檔案 version_info_zh.txt，版本號：{VERSION}") 