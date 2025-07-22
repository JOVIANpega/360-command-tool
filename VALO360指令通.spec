# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('Command_TABLE', 'Command_TABLE'), ('FIXTURE', 'FIXTURE'), ('user_guide.txt', '.'), ('setup.json', '.'), ('assets', 'assets'), ('ui_parts', 'ui_parts'), ('command.txt', '.'), ('color_word.txt', '.'), ('config_core.py', '.'), ('config_utils.py', '.'), ('serial_worker.py', '.')],
    hiddenimports=['tkinter', 'tkinter.ttk', 'serial', 'serial.tools.list_ports', 'json', 'threading', 'datetime', 'config_core', 'config_utils', 'serial_worker', 'ui_parts.ui_main', 'ui_parts.shared_config', 'ui_parts.notification_manager'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VALO360指令通',
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
    version='version_info_zh.txt',
    icon=['assets\\app.ico'],
)
