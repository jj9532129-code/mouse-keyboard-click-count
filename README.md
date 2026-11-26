# 鼠标键盘实时监控（Windows 10）

## 功能
- 系统托盘常驻；关闭窗口会隐藏到托盘。
- 鼠标实时坐标、左/右/中键点击次数、滚轮次数。
- 键盘最近按键名称、按键总次数、常用按键次数。
- 不保存键入文本、不记录剪贴板、不联网。
- 右键托盘图标可打开窗口、重置统计或退出。

## 方式一：在 Windows 10 本机生成 EXE
1. 安装 Python 3（安装时勾选 `Add Python to PATH`）。
2. 解压本文件夹。
3. 双击 `build.bat`。
4. 成功后在 `dist` 文件夹中找到 `MouseKeyboardMonitor.exe`。

## 方式二：使用 GitHub Actions 云端生成 EXE
1. 将本文件夹中的全部文件上传到自己的 GitHub 仓库（包括隐藏的 `.github` 文件夹）。
2. 打开仓库的 **Actions** 页面，选择 **Build Windows EXE**。
3. 点击 **Run workflow**，等待构建完成。
4. 在运行记录底部的 **Artifacts** 下载 `MouseKeyboardMonitor-Windows-x64`，解压即可得到 EXE。

## 运行
双击 EXE。关闭窗口后程序仍在系统托盘运行；右键托盘图标选择“退出”才能完全关闭。

## 注意
此开发环境为 Linux，不能在这里直接产出并验证原生 Windows EXE。上述两种方式会在 Windows 构建环境中生成 EXE。
本程序使用全局键鼠事件监听，部分安全软件可能提示行为监控；请仅在自己的电脑上使用。程序只统计按键名称与次数，不保存输入文本。
