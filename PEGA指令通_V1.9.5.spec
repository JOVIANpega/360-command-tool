# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog', 'serial', 'serial.tools.list_ports', 'logging', 'threading', 'json', 'os', 'sys', 're', 'datetime']
hiddenimports += collect_submodules('serial')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/icon.ico', 'assets'), ('tooltips.ini', '.'), ('setup.json', '.'), ('user_guide.txt', '.'), ('color_word.txt', '.'), ('command.txt', '.'), ('readROVO.txt', '.'), ('Command_TABLE', 'Command_TABLE'), ('core', 'core'), ('ui_parts', 'ui_parts')],
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.datas,
    [],
    name='PEGA指令通_V1.9.5',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icon.ico'],
)
