# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('tooltips.ini', '.'),
        ('assets/', 'assets/'),
        ('Command_TABLE/', 'Command_TABLE/'),
        ('FIXTURE/', 'FIXTURE/'),
        ('setup.json', '.'),
        ('command.txt', '.'),
        ('color_word.txt', '.'),
        ('tooltip_config.txt', '.'),
        ('user_guide.txt', '.'),
    ],
    hiddenimports=['configparser', 'subprocess', 'tkinter', 'tkinter.ttk', 'threading', 'json', 'os', 'sys'],
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
    name='JOVIAN指令工具',
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
    icon='assets/app.ico',
)
