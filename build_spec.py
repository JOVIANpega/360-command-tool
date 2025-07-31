# -*- coding: utf-8 -*-
"""
PyInstaller 打包規格文件
"""

import os
import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE
from PyInstaller.building.datastruct import Tree

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 導入版本信息
from version_info import APP_NAME, APP_VERSION

# 主程式文件
main_script = 'main.py'

# 數據文件和資源
datas = [
    ('assets', 'assets'),
    ('Command_TABLE', 'Command_TABLE'),
    ('setup.json', '.'),
    ('version_info.py', '.'),
]

# 隱藏導入
hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'serial',
    'threading',
    'json',
    'os',
    'sys',
    'time',
    'datetime',
    'logging',
    'subprocess',
    're',
    'configparser',
    'pathlib',
]

# 排除的模組
excludes = [
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'PIL',
    'cv2',
    'tensorflow',
    'torch',
    'sklearn',
]

# 分析
a = Analysis(
    [main_script],
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# EXE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=f'指令通_v{APP_VERSION}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不顯示控制台
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
    version='version_info.py',
)

print(f"✅ PyInstaller 規格文件已創建")
print(f"📦 應用程式名稱：{APP_NAME}")
print(f"🔢 版本號：{APP_VERSION}")
print(f"📁 輸出檔案：指令通_v{APP_VERSION}.exe")
