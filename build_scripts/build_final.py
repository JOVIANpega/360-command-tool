import os
import sys
import shutil
import PyInstaller.__main__
import json
import re

def increment_version(version_str):
    """
    將版本號進版 (V2.6.4 -> V2.6.5)
    傳回 (新版本字串, (major, minor, patch, build))
    """
    # 支援 V2.6.4 或 2.6.4 格式
    match = re.search(r'(\d+)\.(\d+)\.(\d+)', version_str)
    if match:
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        new_patch = patch + 1
        new_version = f"V{major}.{minor}.{new_patch}"
        return new_version, (major, minor, new_patch, 0)
    return version_str, (1, 0, 0, 0)

def update_version_info_file(file_path, version_tuple):
    """
    同步更新 version_info_zh.txt 中的版本資訊
    version_tuple: (major, minor, patch, build)
    """
    if not os.path.exists(file_path):
        print(f"[WARN] Version info file not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    v_str = f"{version_tuple[0]}.{version_tuple[1]}.{version_tuple[2]}"
    v_tuple_str = f"({version_tuple[0]}, {version_tuple[1]}, {version_tuple[2]}, {version_tuple[3]})"

    # 替換 filevers=(2, 6, 4, 0)
    content = re.sub(r'filevers=\(\d+,\s*\d+,\s*\d+,\s*\d+\)', f'filevers={v_tuple_str}', content)
    # 替換 prodvers=(2, 6, 4, 0)
    content = re.sub(r'prodvers=\(\d+,\s*\d+,\s*\d+,\s*\d+\)', f'prodvers={v_tuple_str}', content)
    # 替換 FileVersion 字串
    content = re.sub(r"u'FileVersion',\s*u'[\d\.]+'", f"u'FileVersion', u'{v_str}'", content)
    # 替換 ProductVersion 字串
    content = re.sub(r"u'ProductVersion',\s*u'[\d\.]+'", f"u'ProductVersion', u'{v_str}'", content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[Info] Updated {file_path} to version {v_str}")

def main():
    # ==========================================
    # 1. 環境設定與路徑鎖定
    # ==========================================
    
    # 獲取 build_final.py 所在的目錄 (build_scripts)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 推導專案根目錄 (往上一層)
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    
    # 強制切換工作目錄到專案根目錄
    os.chdir(project_root)
    print(f"[INFO] Project Root: {project_root}")
    print(f"[INFO] Working Directory: {os.getcwd()}")

    # ==========================================
    # 2. 用戶模式選擇 
    # ==========================================
    print("\n========================================")
    print("   PEGA Command Tool - Python Build System")
    print("   Mode: Advance Version & Package EXE")
    print("========================================")
    
    onefile = False
    mode_str = "Onedir"

    # ==========================================
    # 3. 讀取並自動進版 (Increment Version)
    # ==========================================
    setup_path = os.path.join(project_root, 'setup.json')
    app_version = "V2.6.4" 
    version_tuple = (2, 6, 4, 0)
    
    try:
        if os.path.exists(setup_path):
            with open(setup_path, 'r', encoding='utf-8') as f:
                setup_data = json.load(f)
                old_version = setup_data.get('version', 'V2.6.4')
            
            # 執行進版
            app_version, version_tuple = increment_version(old_version)
            print(f"[Info] Version incremented: {old_version} -> {app_version}")
            
            # 寫回到 setup.json
            setup_data['version'] = app_version
            with open(setup_path, 'w', encoding='utf-8') as f:
                json.dump(setup_data, f, indent=2, ensure_ascii=False)
            print(f"[Info] Updated setup.json to version {app_version}")
            
            # 同步更新 version_info_zh.txt
            vinfo_path = os.path.join(project_root, 'version_info_zh.txt')
            update_version_info_file(vinfo_path, version_tuple)
        else:
            print(f"[WARN] setup.json not found at {setup_path}")
    except Exception as e:
        print(f"[ERROR] 自動進版失敗: {e}")

    app_name = f"PEGA指令通_{app_version}"
    print(f"[Info] Building: {app_name}")

    # ==========================================
    # 4. 清理舊建置
    # ==========================================
    dist_dir = os.path.join(project_root, 'dist')
    build_dir = os.path.join(project_root, 'build')
    
    print("[Step 1/4] Clean up old build artifacts...")
    if os.path.exists(build_dir):
        try: shutil.rmtree(build_dir)
        except: pass
        
    target_exe = os.path.join(dist_dir, f"{app_name}.exe")
    target_folder = os.path.join(dist_dir, app_name)
    
    if os.path.exists(target_exe):
        try: os.remove(target_exe)
        except: pass
    if os.path.exists(target_folder):
        try: shutil.rmtree(target_folder)
        except: pass

    # ==========================================
    # 5. 建構 PyInstaller 參數
    # ==========================================
    print("[Step 2/4] Preparing PyInstaller arguments...")
    
    icon_path = os.path.join(project_root, 'assets', 'icon.ico')
    icon_arg = ['--icon', icon_path] if os.path.exists(icon_path) else []

    args = [
        os.path.join(project_root, 'main.py'),
        '--name', app_name,
        '--noconfirm',
        '--clean',
        '--noconsole',
        '--distpath', dist_dir,
        '--workpath', build_dir,
        '--version-file', os.path.join(project_root, 'version_info_zh.txt'),
        '--paths', project_root,
    ]
    
    args.extend(icon_arg)
    args.append('--onefile' if onefile else '--onedir')

    sep = os.pathsep
    
    add_data = [
        ('setup.json', '.'),
        ('sign_DOC.txt', '.'),
        ('assets', 'assets'),
        ('Command_TABLE', 'Command_TABLE'),
        ('FIXTURE', 'FIXTURE'),
        ('docs/tooltips.ini', 'docs'),
        ('docs/tooltip_config.txt', 'docs'),
        ('docs/PEGA指令通使用指南.html', 'docs'),
        ('docs/VALO360_guide_files', 'docs/VALO360_guide_files'),
    ]

    for src, dst in add_data:
        src_abs = os.path.join(project_root, src).replace('/', os.sep)
        if os.path.exists(src_abs):
            args.extend(['--add-data', f'{src_abs}{sep}{dst}'])
        else:
            print(f"[WARN] Resource not found, skipping: {src_abs}")

    hidden_imports = [
        'cryptography', 'cryptography.hazmat.bindings._rust', 
        'cryptography.hazmat.backends.openssl.backend', 'paramiko',
        'json', 'threading', 'queue', 'logging',
        'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 
        'tkinter.filedialog', 'tkinter.scrolledtext'
    ]
    for imp in hidden_imports:
        args.extend(['--hidden-import', imp])
        
    args.extend(['--collect-all', 'cryptography'])
    args.extend(['--collect-all', 'paramiko'])

    excludes = ['scipy', 'pandas', 'selenium', 'matplotlib', 'numpy', 'PIL', 'notebook', 'jedi', 'IPython']
    for exc in excludes:
        args.extend(['--exclude-module', exc])

    # ==========================================
    # 6. 執行打包
    # ==========================================
    print(f"[Step 3/4] Running PyInstaller ({mode_str})...")
    PyInstaller.__main__.run(args)

    # ==========================================
    # 7. 後續處理 (外部檔案複製)
    # ==========================================
    print("[Step 4/4] Post-processing file copy...")
    
    user_config_dir = dist_dir if onefile else os.path.join(dist_dir, app_name)
    
    if not os.path.exists(user_config_dir):
        os.makedirs(user_config_dir, exist_ok=True)
        
    items_to_copy = [
        ('setup.json', '.', 'file'),
        ('sign_DOC.txt', '.', 'file'),
        ('Command_TABLE', '.', 'dir'),          # 整個 Command_TABLE 目錄
        ('FIXTURE', '.', 'dir'),                # 整個 FIXTURE 目錄
        ('IMAGES', '.', 'dir'),                 # 圖片資料夾
        ('docs/PEGA指令通使用指南.html', 'docs', 'file'),
    ]

    for src_rel, dst_parent, item_type in items_to_copy:
        src_path = os.path.join(project_root, src_rel)
        target_base = user_config_dir if dst_parent == '.' else os.path.join(user_config_dir, dst_parent)
            
        if not os.path.exists(target_base):
            os.makedirs(target_base, exist_ok=True)

        dst_path = os.path.join(target_base, os.path.basename(src_path))

        if os.path.exists(src_path):
            if item_type == 'dir':
                if os.path.exists(dst_path):
                    try: shutil.rmtree(dst_path)
                    except: pass
                print(f"Copying Directory {src_rel} -> {dst_path}")
                shutil.copytree(src_path, dst_path)
            else:
                print(f"Copying File {src_rel} -> {dst_path}")
                shutil.copy2(src_path, dst_path)
        else:
            print(f"[WARN] Source {item_type} not found: {src_path}")

    print("\n========================================")
    print(f"[SUCCESS] Build Complete!")
    print(f"Version: {app_version}")
    print(f"Output Location: {user_config_dir}")
    print("========================================")

if __name__ == "__main__":
    main()
