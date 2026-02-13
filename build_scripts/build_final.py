import os
import sys
import shutil
import PyInstaller.__main__

def main():
    # ==========================================
    # 1. 環境設定與路徑鎖定
    # ==========================================
    
    # 獲取 build_final.py 所在的目錄 (build_scripts)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 推導專案根目錄 (往上一層)
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    
    # 強制切換工作目錄到專案根目錄
    # 這是最關鍵的一步！讓 PyInstaller 能正確找到 core, ui_parts 等模組
    os.chdir(project_root)
    print(f"[INFO] Project Root: {project_root}")
    print(f"[INFO] Working Directory: {os.getcwd()}")

    # ==========================================
    # 2. 用戶模式選擇 (預設使用 Onedir 以獲得更快的啟動速度)
    # ==========================================
    print("\n========================================")
    print("   PEGA Command Tool - Python Build System")
    print("   Mode: Onedir (Fast Startup) - Default")
    print("========================================")
    
    # 強制使用 Onedir 模式 (速度快)
    onefile = False
    mode_str = "Onedir"
    print(f"[Mode] Selected: {mode_str}")

    # ==========================================
    # 3. 清理舊建置
    # ==========================================
    dist_dir = os.path.join(project_root, 'dist')
    build_dir = os.path.join(project_root, 'build')
    
    print("[Step 1/4] Clean up old build artifacts...")
    if os.path.exists(build_dir):
        try: shutil.rmtree(build_dir)
        except: pass
        
    # 不完全刪除 dist，只刪除我們目標的那個
    app_name = "PEGA指令通_V2.6.1"
    target_exe = os.path.join(dist_dir, f"{app_name}.exe")
    target_folder = os.path.join(dist_dir, app_name)
    
    if os.path.exists(target_exe):
        try: os.remove(target_exe)
        except: pass
    if os.path.exists(target_folder):
        try: shutil.rmtree(target_folder)
        except: pass

    # ==========================================
    # 4. 建構 PyInstaller 參數
    # ==========================================
    print("[Step 2/4] Preparing PyInstaller arguments...")
    
    # 圖示絕對路徑
    icon_path = os.path.join(project_root, 'assets', 'icon.ico')
    if not os.path.exists(icon_path):
        print(f"[WARN] Icon not found at {icon_path}, using default icon.")
        icon_arg = []
    else:
        icon_arg = ['--icon', icon_path]

    # 基礎參數
    args = [
        os.path.join(project_root, 'main.py'),  # 入口腳本也用絕對路徑
        '--name', app_name,
        '--noconfirm',
        '--clean',
        '--noconsole',
        '--distpath', dist_dir,
        '--workpath', build_dir,
        '--version-file', os.path.join(project_root, 'build_scripts', 'version_info_zh.txt'),
        '--paths', project_root,
    ]
    
    # 加入圖示參數
    args.extend(icon_arg)

    # 模式參數
    if onefile:
        args.append('--onefile')
    else:
        args.append('--onedir')

    # 資源映射 (Source:Dest)
    sep = os.pathsep
    
    add_data = [
        ('setup.json', '.'),
        ('sign_DOC.txt', '.'),
        # color_word.txt now managed inside Command_TABLE
        # version_info handled via --version-file only
        ('assets', 'assets'),
        ('Command_TABLE', 'Command_TABLE'),
        ('FIXTURE', 'FIXTURE'),
        ('docs/tooltips.ini', 'docs'),
        ('docs/tooltip_config.txt', 'docs'),
        ('docs/PEGA指令通使用指南.html', 'docs'),
        ('docs/VALO360_guide_files', 'docs/VALO360_guide_files'),
    ]

    for src, dst in add_data:
        # src 路徑必須是絕對路徑
        src_abs = os.path.join(project_root, src)
        src_abs = src_abs.replace('/', os.sep) # 確保分隔符號正確
        if os.path.exists(src_abs):
            args.extend(['--add-data', f'{src_abs}{sep}{dst}'])
        else:
            print(f"[WARN] Resource not found, skipping: {src_abs}")

    # 隱藏導入 (解決 SSH / Cryptography 崩潰)
    hidden_imports = [
        # SSH 核心
        'cryptography',
        'cryptography.hazmat.bindings._rust',  
        'cryptography.hazmat.backends.openssl.backend',
        'paramiko',
        
        # 常用標準庫 (PyInstaller 有時會漏)
        'json', 'threading', 'queue', 'logging',
        
        # GUI 相關
        'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 
        'tkinter.filedialog', 'tkinter.scrolledtext'
    ]
    for imp in hidden_imports:
        args.extend(['--hidden-import', imp])
        
    # 強制收集 SSH 資源
    args.extend(['--collect-all', 'cryptography'])
    args.extend(['--collect-all', 'paramiko'])

    # 排除不需要的庫 (瘦身)
    excludes = ['scipy', 'pandas', 'selenium', 'matplotlib', 'numpy', 'PIL', 'notebook', 'jedi', 'IPython']
    for exc in excludes:
        args.extend(['--exclude-module', exc])

    # ==========================================
    # 5. 執行打包
    # ==========================================
    print(f"[Step 3/4] Running PyInstaller ({mode_str})...")
    PyInstaller.__main__.run(args)

    # ==========================================
    # 6. 後續處理 (外部檔案複製)
    # ==========================================
    print("[Step 4/4] Post-processing file copy...")
    
    # 這些檔案需要複製到 user 可見的地方，方便他們修改配置
    # 我們的 resource_manager 會優先讀取這裡的檔案
    
    if onefile:
        # Onefile: 複製到 EXE 旁 (dist 根目錄)
        user_config_dir = dist_dir
    else:
        # Onedir: 複製到 EXE 同目錄 (dist/AppName)
        user_config_dir = os.path.join(dist_dir, app_name)
    
    if not os.path.exists(user_config_dir):
        os.makedirs(user_config_dir, exist_ok=True)
        
    # 定義需要複製的檔案與目錄
    # 使用 (來源路徑, 目標父目錄, 類型)
    # 類型: 'file' 或 'dir'
    items_to_copy = [
        ('setup.json', '.', 'file'),
        ('sign_DOC.txt', '.', 'file'),
        ('Command_TABLE', '.', 'dir'),          # 整個 Command_TABLE 目錄
        ('FIXTURE', '.', 'dir'),                # 整個 FIXTURE 目錄
        ('IMAGES', '.', 'dir'),                 # 圖片資料夾 (手冊皆引用此處)
        ('docs/PEGA指令通使用指南.html', 'docs', 'file'),
    ]

    for src_rel, dst_parent, item_type in items_to_copy:
        src_path = os.path.join(project_root, src_rel)
        
        # 計算目標目錄
        if dst_parent == '.':
            target_base = user_config_dir
        else:
            target_base = os.path.join(user_config_dir, dst_parent)
            
        if not os.path.exists(target_base):
            os.makedirs(target_base, exist_ok=True)

        # 計算目標路徑
        base_name = os.path.basename(src_path)
        dst_path = os.path.join(target_base, base_name)

        if os.path.exists(src_path):
            if item_type == 'dir':
                # 如果目標目錄已存在，先刪除以確保乾淨複製
                if os.path.exists(dst_path):
                    try:
                        shutil.rmtree(dst_path)
                    except Exception as e:
                        print(f"[WARN] Failed to remove existing dir {dst_path}: {e}")
                
                print(f"Copying Directory {src_rel} -> {dst_path}")
                shutil.copytree(src_path, dst_path)
            else:
                print(f"Copying File {src_rel} -> {dst_path}")
                shutil.copy2(src_path, dst_path)
        else:
            print(f"[WARN] Source {item_type} not found: {src_path}")

    print("\n========================================")
    print(f"[SUCCESS] Build Complete!")
    print(f"Output Location: {user_config_dir}")
    print("========================================")

if __name__ == "__main__":
    main()
