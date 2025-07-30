# -*- coding: utf-8 -*-
"""
清理不需要的文件腳本
將多餘的.py、.md、.spec文件移動到backup目錄
"""
import os
import shutil
from datetime import datetime

def create_backup_folder():
    """創建備份文件夾"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_folder = f"backup/cleanup_{timestamp}"
    os.makedirs(backup_folder, exist_ok=True)
    return backup_folder

def move_to_backup(file_path, backup_folder):
    """移動文件到備份文件夾"""
    try:
        filename = os.path.basename(file_path)
        backup_path = os.path.join(backup_folder, filename)
        shutil.move(file_path, backup_path)
        print(f"✓ 移動: {file_path} -> {backup_path}")
        return True
    except Exception as e:
        print(f"✗ 移動失敗: {file_path} - {e}")
        return False

def main():
    """主清理函數"""
    print("開始清理不需要的文件...")
    
    # 創建備份文件夾
    backup_folder = create_backup_folder()
    print(f"備份文件夾: {backup_folder}")
    
    # 需要保留的核心文件
    keep_files = {
        # 核心Python文件
        'main.py',
        'config_core.py', 
        'config_utils.py',
        'serial_worker.py',
        'version_info_zh.py',
        
        # 核心模組
        'core/__init__.py',
        'core/error_handler.py',
        'core/config_manager.py', 
        'core/resource_manager.py',
        'core/async_manager.py',
        'core/performance_monitor.py',
        
        # UI模組
        'ui_parts/__init__.py',
        'ui_parts/ui_main.py',
        'ui_parts/ui_components.py',
        'ui_parts/ui_handlers.py',
        'ui_parts/ui_settings_tab.py',
        'ui_parts/notification_manager.py',
        'ui_parts/shared_config.py',
        'ui_parts/tooltip.py',
        'ui_parts/ui_components_base.py',
        'ui_parts/ui_components_input.py',
        'ui_parts/ui_components_output.py',
        'ui_parts/ui_components_settings.py',
        'ui_parts/ui_handlers_core.py',
        
        # 治具模組
        'FIXTURE/fixture13.py',
        
        # 配置和資源文件
        'setup.json',
        'requirements.txt',
        'user_guide.txt',
        'README.md',
        'command.txt',
        'color_word.txt',
        
        # 重要的新文檔
        'OPTIMIZATION_SUMMARY.md',
        'OPTIMIZATION_COMPLETE.md'
    }
    
    # 需要移動的文件（多餘的文件）
    files_to_move = [
        # 多餘的構建文件
        'build_direct.py',
        'build_exe.py', 
        'build_simple.py',
        'exec_build.py',
        'fix_build.py',
        'install_and_build.py',
        'minimal_build.py',
        'run_build.py',
        'check_syntax.py',
        'test_imports.py',
        'tmp_rovodev_build.py',
        
        # 多餘的配置文件
        'config.py.bak',
        
        # 舊版本的文檔
        'BUILD_INSTRUCTIONS.md',
        'CHANGELOG_v1.5.0.4.md',
        'CHANGELOG_v1.5.0.5.md', 
        'CHANGELOG_v1.5.0.9.md',
        'CHANGELOG_v1.6.0.0.md',
        'CHANGELOG_v1.6.2.0.md',
        'COMMAND_SEPARATOR_IMPLEMENTATION_SUMMARY.md',
        'FINAL_BUILD_STATUS.md',
        'GIT_PUSH_INSTRUCTIONS.md',
        'GLOBAL_NOTIFICATION_IMPLEMENTATION.md',
        'GUI_OPTIMIZATION_SUMMARY.md',
        'LATEST_IMPROVEMENTS_SUMMARY.md',
        'NOTIFICATION_MANAGER_IMPROVEMENTS.md',
        'SETTINGS_OPTIMIZATION_SUMMARY.md',
        'SETTINGS_PREVIEW_REMOVAL.md',
        'SETTINGS_TAB_OPTIMIZATION.md',
        'SETTINGS_TAB_SIMPLIFICATION.md',
        'SETUP_GIT_REPOSITORY.md',
        'tmp_rovodev_git_troubleshooting.md',
        
        # 測試文件
        'test_optimization.py',
        
        # 其他文件
        'EXECUTE_THESE_COMMANDS.txt',
        'TALK_TOROVO.txt',
        'VALO360 指令通 - 完整功能分析.txt',
        'version_info.txt',
        'version_info_zh.txt',
        'rules.md',
        
        # 構建腳本
        'build.cmd',
        'build_exe.bat',
        'build_fix.bat',
        'run_build.bat',
        'simple_build.cmd',
        'tmp_rovodev_build.bat',
        
        # spec文件
        'VALO360指令通.spec',
        
        # 其他構建相關
        'build code.txt'
    ]
    
    moved_count = 0
    
    # 移動文件
    for file_path in files_to_move:
        if os.path.exists(file_path):
            if move_to_backup(file_path, backup_folder):
                moved_count += 1
    
    # 移動整個HTML文件夾
    html_folder = 'VALO360 指令通使用指南_files'
    if os.path.exists(html_folder):
        try:
            backup_html_path = os.path.join(backup_folder, 'VALO360_guide_files')
            shutil.move(html_folder, backup_html_path)
            print(f"✓ 移動文件夾: {html_folder} -> {backup_html_path}")
            moved_count += 1
        except Exception as e:
            print(f"✗ 移動文件夾失敗: {html_folder} - {e}")
    
    # 移動HTML文件
    html_file = 'VALO360 指令通使用指南.html'
    if os.path.exists(html_file):
        if move_to_backup(html_file, backup_folder):
            moved_count += 1
    
    print(f"\n清理完成！")
    print(f"總共移動了 {moved_count} 個文件/文件夾到 {backup_folder}")
    
    # 顯示保留的重要文件
    print(f"\n保留的核心文件:")
    for file_path in sorted(keep_files):
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (不存在)")

if __name__ == "__main__":
    main()
