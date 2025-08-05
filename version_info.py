# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 9, 2, 0),
    prodvers=(1, 9, 2, 0),
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
          StringStruct(u'FileVersion', u'1.9.2.0'),
          StringStruct(u'InternalName', u'VALO360_CommandTool'),
          StringStruct(u'LegalCopyright', u'Copyright © 2024-2025 VALO360'),
          StringStruct(u'OriginalFilename', u'指令通_v1.9.2.exe'),
          StringStruct(u'ProductName', u'VALO360 指令通'),
          StringStruct(u'ProductVersion', u'1.9.2.0'),
          StringStruct(u'Comments', u'ADB 優化3：COM口顯示增強 + 指令列表顯示')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1028, 1200])])
  ]
)

# 應用程式信息
APP_NAME = "VALO360 指令通"
APP_VERSION = "1.9.2"
APP_DESCRIPTION = "串口指令執行工具 - ADB 優化3：COM口顯示增強 + 指令列表顯示"
APP_AUTHOR = "VALO360 開發團隊"
APP_COPYRIGHT = "Copyright © 2024-2025 VALO360"

# 更新日誌
CHANGELOG_V1_9_2 = """
版本 1.9.2 更新內容：

🔍 COM 口顯示增強：
• 智能 COM 口識別：自動識別 AT PORT、DM PORT、NMEA PORT
• 選擇性描述顯示：只對特定類型的 COM 口顯示描述信息
• 其他 COM 口簡潔顯示：普通 COM 口只顯示名稱（如 COM3）
• 正確指令傳遞：確保後續指令只使用 COM 口名稱，不包含描述

📋 ADB 指令列表顯示：
• ADB 模式指令預覽：執行前顯示完整的指令列表
• 多重指令模式：清楚顯示將執行的指令數量和內容
• 統一顯示格式：ADB 和 Console 模式使用相同的指令列表顯示
• 改善用戶體驗：用戶可以在執行前確認所有指令

🛠️ ADB 模式優化：
• ADB 模式下 COM 口可見：COM 口顯示為灰色，表示僅供參考
• 智能狀態提示：自動提示 ADB 模式下 COM 口不會被使用
• 保持功能完整：所有 ADB 功能保持正常運作

🔧 技術改進：
• 修改 list_com_ports()：增強 COM 口類型識別邏輯
• 新增 extract_com_port_name()：從顯示名稱提取實際 COM 口名稱
• 更新 ui_handlers.py：統一 ADB 和 Console 模式的指令顯示
• 改進 COM 口狀態管理：ADB 模式下的智能狀態控制

✨ 使用者體驗提升：
• 更清楚的 COM 口資訊：一目了然的 COM 口類型
• 更好的指令預覽：執行前可確認所有指令
• 更智能的模式切換：ADB 和 Console 模式的無縫切換
• 更專業的界面顯示：保持簡潔但資訊豐富的顯示

📊 技術指標：
• 程式啟動時間：< 3 秒
• 記憶體使用：< 50MB
• 支援 COM 口：自動檢測並智能分類
• 支援 ADB 模式：完全隱藏 DOS 視窗 + 指令列表顯示
• 指令解析：94+ 個指令
• GUI 響應：即時更新
"""
