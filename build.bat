@echo off
chcp 65001 >nul
echo ============================================
echo   DeskStudy 打包脚本
echo ============================================
echo.

:: 进入项目目录
cd /d "%~dp0"

:: 检查 PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装 PyInstaller...
    pip install pyinstaller -q
)

:: 检查依赖
echo [信息] 检查依赖...
pip install -r requirements.txt -q

:: 清理旧的打包文件
echo [信息] 清理旧的打包文件...
if exist "dist" rd /s /q "dist" 2>nul
if exist "build" rd /s /q "build" 2>nul

:: 开始打包
echo [信息] 开始打包...
pyinstaller DeskStudy.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo.
echo ============================================
echo   打包完成！
echo   输出目录: %~dp0dist\DeskStudy
echo ============================================
echo.

:: 打开输出目录
explorer "%~dp0dist\DeskStudy"

pause
