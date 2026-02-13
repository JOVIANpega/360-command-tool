# CHANGELOG V2.5.6 (Stable Release)

## Release Date
2026-02-12

## Summary
This is a comprehensive stable release that resolves critical packaging issues, ensuring the application runs correctly as a standalone executable. It features a completely rebuilt build system using Python script for reliability and precise resource handling.

## 🚀 Major Improvements

### 1. Robust Build System Overhaul
- **New Build Script**: Replaced fragile batch scripts with a robust Python-based build system (`build_scripts/build_final.py`).
- **Path Auto-Correction**: The build script now automatically detects the project root, eliminating "file not found" errors during packaging regardless of where the script is executed.
- **Dependency Management**: Explicitly handles critical dependencies like `cryptography` and `paramiko` to prevent runtime crashes.

### 2. Critical Bug Fixes
- **SSH Crash Fix**: Resolved a startup crash caused by missing `cryptography` Rust bindings in the packaged EXE.
- **Resource Path Fix**: Rewrite of `core/resource_manager.py` to intelligently locate resources (like `command.txt`, `Fixture_Command.txt`) in both development and packaged environments (Onedir/Onefile).
- **Fixture Command Redirection**: Fixed an issue where `Fixture_Command.txt` was being searched in the wrong directory (`Command_TABLE`) by forcing redirection to the correct `FIXTURE` folder.

### 3. Performance Optimization
- **Onedir Default**: The packaging process now defaults to `Onedir` mode for significantly faster application startup times.
- **Clean Build**: Automated cleanup of old build artifacts (`build/`, `dist/`) before each packaging run.

## 📦 Packaging Details

- **Output Directory**: `dist/` (in project root)
- **Executable Name**: `PEGA指令通_V2.5.6.exe`
- **Included Resources**:
    - `Command_TABLE/` (Full directory)
    - `FIXTURE/` (Full directory)
    - `docs/` (User manual and tooltips)
    - `assets/` (Icons and images)
    - `setup.json`, `sign_DOC.txt`, `color_word.txt`

## 🛠️ How to Build
Simply run the launcher script:
```
build_scripts\build_PEGA_final.bat
```
This will automatically invoke the Python build system and generate a stable release in the `dist` folder.
