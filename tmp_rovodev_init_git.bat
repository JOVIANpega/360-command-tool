@echo off
echo 初始化 Git 倉庫並連接到 GitHub
echo =====================================

echo Step 1: 初始化 Git 倉庫
git init

echo.
echo Step 2: 添加遠端倉庫
git remote add origin https://github.com/JOVIANpega/360-command-tool.git

echo.
echo Step 3: 檢查遠端配置
git remote -v

echo.
echo Step 4: 添加所有文件
git add .

echo.
echo Step 5: 首次提交
git commit -m "Initial commit - VALO360 Command Tool V1.6.2.0"

echo.
echo Step 6: 設置主分支
git branch -M main

echo.
echo Step 7: 推送到 GitHub
git push -u origin main

echo.
echo Step 8: 創建並推送標籤
git tag v1.6.2.0
git push origin v1.6.2.0

echo.
echo =====================================
echo 完成！現在可以在 GitHub 上看到您的代碼了
echo 訪問：https://github.com/JOVIANpega/360-command-tool
echo =====================================
pause