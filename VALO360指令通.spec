# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_utf8_fixed.py'],
    pathex=[],
    binaries=[],
    datas=[('command.txt', '.'), ('user_guide.txt', '.'), ('setup.json', '.'), ('app.ico', '.'), ('VALO360 指令通使用指南.html', '.'), ('VALO360 指令通使用指南_files', 'VALO360 指令通使用指南_files'), ('Command_TABLE', 'Command_TABLE'), ('FIXTURE', 'FIXTURE')],
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
    icon=['app.ico'],
)
