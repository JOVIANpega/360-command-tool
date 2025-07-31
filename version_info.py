# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 7, 6, 0),
    prodvers=(1, 7, 6, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName', u'VALO360 開發團隊'),
          StringStruct(u'FileDescription', u'VALO360 指令通 - 串口指令執行工具'),
          StringStruct(u'FileVersion', u'1.7.6.0'),
          StringStruct(u'InternalName', u'VALO360_CommandTool'),
          StringStruct(u'LegalCopyright', u'Copyright © 2024-2025 VALO360'),
          StringStruct(u'OriginalFilename', u'指令通_v1.7.6.exe'),
          StringStruct(u'ProductName', u'VALO360 指令通'),
          StringStruct(u'ProductVersion', u'1.7.6.0'),
          StringStruct(u'Comments', u'漸進式重構版本 - 改善代碼結構，提升維護性')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1028, 1200])])
  ]
)

# 應用程式信息
APP_NAME = "VALO360 指令通"
APP_VERSION = "1.7.6"
APP_DESCRIPTION = "串口指令執行工具 - 漸進式重構版本"
APP_AUTHOR = "VALO360 開發團隊"
APP_COPYRIGHT = "Copyright © 2024-2025 VALO360"

# 更新日誌
CHANGELOG_V1_7_6 = """
版本 1.7.6 更新內容：

🔧 代碼重構改進：
• 漸進式重構 ui_handlers.py，將大函數拆分為更小的輔助函數
• 漸進式重構 ui_main.py，改善代碼結構和可維護性
• 添加了 13 個重構輔助函數，提升代碼可讀性
• 保持所有原有功能完全不變，確保穩定性

✨ 重構輔助函數：
• _get_command_file_path() - 獲取指令檔路徑
• _parse_command_line() - 解析單行指令
• _print_commands_summary() - 輸出指令摘要
• _validate_execution_parameters() - 驗證執行參數
• _prepare_command_execution() - 準備指令執行
• _create_and_start_worker() - 創建並啟動工作線程
• _read_section_titles_from_file() - 從指令檔案中讀取區段標題
• _get_section_titles() - 獲取區段標題列表
• _create_section_radiobutton() - 創建區段單選按鈕
• _update_basic_settings() - 更新基本設定
• _update_end_string_settings() - 更新結束字串設定
• _update_font_settings() - 更新字體設定
• _update_device_and_command_settings() - 更新設備和指令設定

🎯 改進效果：
• 大函數從 200+ 行拆分為多個 20-50 行的小函數
• 提升代碼可讀性和維護性
• 降低代碼複雜度，便於後續開發
• 保持 100% 向後兼容性

📊 技術指標：
• 程式啟動時間：< 3 秒
• 記憶體使用：< 50MB
• 支援 COM 口：自動檢測
• 指令解析：94+ 個指令
• GUI 響應：即時更新
"""
