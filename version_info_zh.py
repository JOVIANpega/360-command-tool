# -*- coding: utf-8 -*-

"""

生成 PyInstaller 版本資訊檔案

"""



import os
import sys
import datetime

# 設置版本號
VERSION = "V1.4.3.3"

# 生成版本資訊檔案
with open("version_info_zh.txt", "w", encoding="utf-8") as f:
    f.write("VSVersionInfo(\n")
    f.write("  ffi=FixedFileInfo(\n")
    f.write("    filevers=(1, 4, 3, 3),\n")
    f.write("    prodvers=(1, 4, 3, 3),\n")
    f.write("    mask=0x3f,\n")
    f.write("    flags=0x0,\n")
    f.write("    OS=0x40004,\n")
    f.write("    fileType=0x1,\n")
    f.write("    subtype=0x0,\n")
    f.write("    date=(0, 0)\n")
    f.write("  ),\n")
    f.write("  kids=[\n")
    f.write("    StringFileInfo(\n")
    f.write("      [\n")
    f.write("        StringTable(\n")
    f.write("          u'040904B0',\n")
    f.write("          [StringStruct(u'CompanyName', u'VALO360'),\n")
    f.write("           StringStruct(u'FileDescription', u'VALO360指令通'),\n")
    f.write("           StringStruct(u'FileVersion', u'" + VERSION + "'),\n")
    f.write("           StringStruct(u'InternalName', u'VALO360指令通'),\n")
    f.write("           StringStruct(u'LegalCopyright', u'Copyright (C) 2025 VALO360'),\n")
    f.write("           StringStruct(u'OriginalFilename', u'VALO360指令通.exe'),\n")
    f.write("           StringStruct(u'ProductName', u'VALO360指令通'),\n")
    f.write("           StringStruct(u'ProductVersion', u'" + VERSION + "')]\n")
    f.write("        )\n")
    f.write("      ]),\n")
    f.write("    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])\n")
    f.write("  ]\n")
    f.write(")\n")

print(f"已生成版本資訊檔案 version_info_zh.txt，版本號：{VERSION}") 