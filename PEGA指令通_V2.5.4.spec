# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['MAIN.PY'],
    pathex=[],
    binaries=[],
    datas=[('tooltips.ini', '.'), ('setup.json', '.'), ('command.txt', '.'), ('color_word.txt', '.'), ('tooltip_config.txt', '.'), ('user_guide.txt', '.'), ('readROVO.txt', '.'), ('sign_DOC.txt', '.'), ('Command_TABLE', 'Command_TABLE'), ('FIXTURE', 'FIXTURE'), ('core', 'core'), ('ui_parts', 'ui_parts'), ('transport', 'transport'), ('assets', 'assets'), ('docs\\PEGA指令通使用指南.html', '.'), ('docs\\VALO360_guide_files', 'VALO360_guide_files')],
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
    name='PEGA指令通_V2.5.4',
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
