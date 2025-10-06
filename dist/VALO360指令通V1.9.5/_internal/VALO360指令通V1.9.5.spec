# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('Command_TABLE', 'Command_TABLE'), ('FIXTURE', 'FIXTURE'), ('logs', 'logs'), ('backup', 'backup'), ('ui_parts', 'ui_parts'), ('core', 'core'), ('*.txt', '.'), ('*.json', '.'), ('*.ini', '.'), ('*.md', '.'), ('*.html', '.'), ('*.bat', '.'), ('*.spec', '.')],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.scrolledtext', 'tkinter.messagebox', 'serial', 'threading', 'json', 'logging', 'traceback'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VALO360指令通V1.9.5',
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
    icon=['assets\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VALO360指令通V1.9.5',
)
