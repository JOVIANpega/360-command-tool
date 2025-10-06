# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 獲取當前目錄
current_dir = os.path.dirname(os.path.abspath(SPEC))

# 分析選項
a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=[],
    datas=[
        # 包含所有必要的檔案和資料夾
        ('assets', 'assets'),  # 圖示和資源檔案
        ('Command_TABLE', 'Command_TABLE'),  # 指令表格
        ('FIXTURE', 'FIXTURE'),  # 治具相關檔案
        ('logs', 'logs'),  # 日誌目錄
        ('backup', 'backup'),  # 備份目錄
        ('ui_parts', 'ui_parts'),  # UI元件模組
        ('core', 'core'),  # 核心模組
        ('*.txt', '.'),  # 所有txt檔案
        ('*.json', '.'),  # 所有json檔案
        ('*.ini', '.'),  # 所有ini檔案
        ('*.md', '.'),  # 所有markdown檔案
        ('*.spec', '.'),  # 所有spec檔案
        ('*.bat', '.'),  # 所有bat檔案
        ('*.py', '.'),  # 所有Python檔案
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.messagebox',
        'tkinter.simpledialog',
        'serial',
        'threading',
        'json',
        'os',
        'sys',
        're',
        'time',
        'datetime',
        'logging',
        'traceback',
        'subprocess',
        'configparser',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 移除重複的檔案
def remove_duplicates(analysis):
    seen = set()
    unique_datas = []
    for data in analysis.datas:
        if data[0] not in seen:
            seen.add(data[0])
            unique_datas.append(data)
    analysis.datas = unique_datas

remove_duplicates(a)

# 打包選項
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 執行檔設定
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VALO360指令通V1.9.5',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 無控制台視窗
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',  # 使用圖示
    version_file='version_info_zh.py',  # 版本資訊檔案
    uac_admin=False,
    uac_uiaccess=False,
)

# 版本資訊
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 9, 5, 0),
        prodvers=(1, 9, 5, 0),
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
                    [StringStruct(u'CompanyName', u'VALO360'),
                     StringStruct(u'FileDescription', u'VALO360指令通 - 序列埠通訊工具'),
                     StringStruct(u'FileVersion', u'1.9.5.0'),
                     StringStruct(u'InternalName', u'VALO360指令通'),
                     StringStruct(u'LegalCopyright', u'Copyright © 2025 VALO360. All rights reserved.'),
                     StringStruct(u'OriginalFilename', u'VALO360指令通V1.9.5.exe'),
                     StringStruct(u'ProductName', u'VALO360指令通'),
                     StringStruct(u'ProductVersion', u'1.9.5.0'),
                     StringStruct(u'Comments', u'優化設定標籤與排版優化版本')]
                )
            ]),
        VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
    ]
)
