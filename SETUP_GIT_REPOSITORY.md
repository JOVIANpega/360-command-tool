# 設置 Git 倉庫指南

## 問題：目錄不是 Git 倉庫

您的工作目錄還沒有初始化為 Git 倉庫，所以無法推送到 GitHub。

## 解決方案：

### 方法一：使用腳本（推薦）
執行我創建的腳本：
```bash
tmp_rovodev_init_git.bat
```

### 方法二：手動執行命令
在命令提示符中依次執行：

```bash
# 1. 初始化 Git 倉庫
git init

# 2. 添加遠端倉庫
git remote add origin https://github.com/JOVIANpega/360-command-tool.git

# 3. 添加所有文件
git add .

# 4. 首次提交
git commit -m "Initial commit - VALO360 Command Tool V1.6.2.0"

# 5. 設置主分支名稱
git branch -M main

# 6. 推送到 GitHub
git push -u origin main

# 7. 創建並推送版本標籤
git tag v1.6.2.0
git push origin v1.6.2.0
```

## 執行後您將看到：
- ✅ GitHub 上出現完整的代碼
- ✅ V1.6.2.0 標籤
- ✅ 所有更新的版本文件

## 注意事項：
- 如果 GitHub 倉庫已存在內容，可能需要先 `git pull origin main`
- 如果遇到權限問題，確保您有該倉庫的寫入權限
- 首次推送可能需要輸入 GitHub 用戶名和密碼/token