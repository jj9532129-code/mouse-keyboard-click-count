@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo [1/3] 检查 Python...
py -3 --version
if errorlevel 1 (
  echo 未检测到 Python 3。请先安装 Python 3，并勾选 Add Python to PATH。
  pause
  exit /b 1
)
echo [2/3] 安装依赖...
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt
if errorlevel 1 (
  echo 依赖安装失败。
  pause
  exit /b 1
)
echo [3/3] 打包 Windows EXE...
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name MouseKeyboardMonitor app.py
if errorlevel 1 (
  echo 打包失败。
  pause
  exit /b 1
)
echo.
echo 打包完成：dist\MouseKeyboardMonitor.exe
pause
