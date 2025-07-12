# -*- coding: utf-8 -*-

"""

生成 PyInstaller 版本資訊檔案

"""



import os



def generate_version_info():

    """生成版本信息文件"""

    version = "V1.4.2"

    version_tuple = (1, 4, 2, 0)  # 主版本, 次版本, 修訂版本, 構建版本

    

    # 創建版本信息文件內容

    content = f"""VSVersionInfo(

  ffi=FixedFileInfo(

    filevers={version_tuple},

    prodvers={version_tuple},

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

           StringStruct(u'FileDescription', u'VALO360指令通'),

           StringStruct(u'FileVersion', u'{version}'),

           StringStruct(u'InternalName', u'VALO360指令通'),

           StringStruct(u'LegalCopyright', u'Copyright (C) 2025 VALO360'),

           StringStruct(u'OriginalFilename', u'VALO360指令通.exe'),

           StringStruct(u'ProductName', u'VALO360指令通'),

           StringStruct(u'ProductVersion', u'{version}')]

        )

      ]),

    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])

  ]

)

"""

    

    # 寫入版本信息文件

    with open("version_info_zh.txt", "w", encoding="utf-8") as f:

        f.write(content)

    

    print("版本資訊已保存到 version_info_zh.txt")



if __name__ == "__main__":

    generate_version_info() 