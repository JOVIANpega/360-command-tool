# -*- coding: utf-8 -*-
"""
生成 PyInstaller 版本資訊檔案
"""

VERSION = "V1.38"
VERSION_TUPLE = (1, 3, 8, 0)

def generate_version_info():
    """生成版本資訊檔案內容"""
    version_info = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={VERSION_TUPLE},
    prodvers={VERSION_TUPLE},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName', u'VALO360'),
           StringStruct(u'FileDescription', u'VALO360 指令通'),
           StringStruct(u'FileVersion', u'{VERSION}'),
           StringStruct(u'InternalName', u'VALO360指令通'),
           StringStruct(u'LegalCopyright', u'Copyright (C) 2025 VALO360'),
           StringStruct(u'OriginalFilename', u'VALO360指令通.exe'),
           StringStruct(u'ProductName', u'VALO360 指令通'),
           StringStruct(u'ProductVersion', u'{VERSION}')]
        )
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    return version_info

def save_version_info(filename="version_info_zh.txt"):
    """保存版本資訊到檔案"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(generate_version_info())
    print(f"版本資訊已保存到 {filename}")

if __name__ == "__main__":
    save_version_info() 