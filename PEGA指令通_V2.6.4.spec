# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('D:\\((Python TOOL\\指令工具-20250428T020034Z-001\\PEGA-command-tool\\setup.json', '.'), ('D:\\((Python TOOL\\指令工具-20250428T020034Z-001\\PEGA-command-tool\\sign_DOC.txt', '.'), ('D:\\((Python TOOL\\指令工具-20250428T020034Z-001\\PEGA-command-tool\\assets', 'assets'), ('D:\\((Python TOOL\\指令工具-20250428T020034Z-001\\PEGA-command-tool\\Command_TABLE', 'Command_TABLE'), ('D:\\((Python TOOL\\指令工具-20250428T020034Z-001\\PEGA-command-tool\\FIXTURE', 'FIXTURE'), ('D:\\((Python TOOL\\指令工具-20250428T020034Z-001\\PEGA-command-tool\\docs\\tooltips.ini', 'docs'), ('D:\\((Python TOOL\\指令工具-20250428T020034Z-001\\PEGA-command-tool\\docs\\tooltip_config.txt', 'docs'), ('D:\\((Python TOOL\\指令工具-20250428T020034Z-001\\PEGA-command-tool\\docs\\PEGA指令通使用指南.html', 'docs'), ('D:\\((Python TOOL\\指令工具-20250428T020034Z-001\\PEGA-command-tool\\docs\\VALO360_guide_files', 'docs/VALO360_guide_files')]
binaries = []
hiddenimports = ['cryptography', 'cryptography.hazmat.bindings._rust', 'cryptography.hazmat.backends.openssl.backend', 'paramiko', 'json', 'threading', 'queue', 'logging', 'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog', 'tkinter.scrolledtext']
tmp_ret = collect_all('cryptography')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('paramiko')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['D:\\((Python TOOL\\指令工具-20250428T020034Z-001\\PEGA-command-tool\\main.py'],
    pathex=['D:\\((Python TOOL\\指令工具-20250428T020034Z-001\\PEGA-command-tool'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['scipy', 'pandas', 'selenium', 'matplotlib', 'numpy', 'PIL', 'notebook', 'jedi', 'IPython'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PEGA指令通_V2.6.4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='D:\\((Python TOOL\\指令工具-20250428T020034Z-001\\PEGA-command-tool\\build_scripts\\version_info_zh.txt',
    icon=['D:\\((Python TOOL\\指令工具-20250428T020034Z-001\\PEGA-command-tool\\assets\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PEGA指令通_V2.6.4',
)
