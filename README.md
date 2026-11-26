[README.md](https://github.com/user-attachments/files/35454804/README.md)
修复版：修复全键盘界面启动失败。原因为 Tkinter 网格的 column 只能使用整数，但键盘布局含 1.5 等半键宽坐标；现已转换为整数网格并扩展列数。将全部文件（包括 .github 隐藏目录）上传到 GitHub 仓库，进入 Actions 重新构建 EXE。
