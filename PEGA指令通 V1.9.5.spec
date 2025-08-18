# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('Command_TABLE', 'Command_TABLE'), ('FIXTURE', 'FIXTURE'), ('assets', 'assets'), ('ui_parts', 'ui_parts'), ('setup.json', '.'), ('tooltips.ini', '.'), ('command.txt', '.'), ('tooltip_config.txt', '.'), ('user_guide.txt', '.'), ('PEGA指令通使用指南.html', '.')],
    hiddenimports=[],
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
    name='PEGA指令通 V1.9.5',
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
    icon=['assets\\icon.ico'],
)
