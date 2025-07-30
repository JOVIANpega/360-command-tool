# VALO360 指令通 V1.6.2.0 Git 推送指南

## 手动执行以下命令：

### 1. 打开命令提示符或 Git Bash

### 2. 依次执行以下命令：

```bash
# 检查当前状态
git status

# 添加所有更改的文件
git add .

# 提交更改
git commit -m "Release V1.6.2.0 stable version - Fix issues and add separator customization"

# 创建版本标签
git tag v1.6.2.0

# 推送主分支到远端
git push origin main

# 推送标签到远端
git push origin v1.6.2.0
```

### 3. 验证推送成功
访问 GitHub 仓库确认：
- 代码已推送到 main 分支
- 标签 v1.6.2.0 已创建

### 4. 创建 GitHub Release
1. 访问：https://github.com/JOVIANpega/360-command-tool/releases/new
2. 选择标签：v1.6.2.0
3. 发布标题：VALO360 指令通 V1.6.2.0 稳定版
4. 发布说明：复制 CHANGELOG_v1.6.2.0.md 的内容
5. 上传编译好的 exe 文件

## 已更新的文件：
- ✅ CHANGELOG_v1.6.2.0.md
- ✅ setup.json
- ✅ version_info_zh.py
- ✅ README.md
- ✅ version_info.txt

## 版本特色：
- 修复问题，提升程式穩定性
- 新增可修改間隔符號功能
- 優化系統性能與使用體驗
- 其他細節優化與錯誤修正