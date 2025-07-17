# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('Command_TABLE', 'Command_TABLE'), ('Command_TABLE/*.txt', 'Command_TABLE'), ('FIXTURE', 'FIXTURE'), ('FIXTURE/*.txt', 'FIXTURE'), ('user_guide.txt', '.'), ('setup.json', '.'), ('assets', 'assets'), ('ui_parts', 'ui_parts')],
    hiddenimports=[],
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
