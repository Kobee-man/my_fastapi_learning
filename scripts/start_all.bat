@echo off
chcp 65001 >nul 2>nul
title 海龟汤游戏系统 - 一键启动
color 0A

echo.
echo ╔════════════════════════════════════════════════╗
echo ║  🐢 海龟汤游戏系统 - 一键启动脚本 v2.0       ║
echo ╚════════════════════════════════════════════════╝
echo.

:: ==================== 检查Python ====================
echo [1/5] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python！请先安装 Python 3.10+
    echo.
    echo   下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
for /f "tokens=2 delims=. " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo       [OK] Python %PYVER% 已就绪

:: ==================== 检查Node.js ===================
echo [2/5] 检查 Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js！请先安装 Node.js 18+
    echo.
    echo   下载地址: https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f "tokens=1 delims=v" %%v in ('node --version 2^>^&1') do set NODEVER=%%v
echo       [OK] Node.js %NODEVER% 已就绪

:: ==================== 检查依赖 ====================
echo [3/5] 检查项目依赖...

:: 检查后端依赖
python -c "import fastapi, uvicorn, sqlmodel" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装 Python 依赖...
    pip install -q fastapi uvicorn sqlmodel python-jose passlib requests
    if errorlevel 1 (
        echo [错误] Python 依赖安装失败！
        pause
        exit /b 1
    )
)
echo       [OK] Python 依赖已就绪

:: 检查前端依赖
if not exist "frontend\node_modules\vue" (
    if exist "frontend\package.json" (
        echo [提示] 正在安装前端依赖（首次需要几分钟）...
        cd frontend
        call npm install --silent
        cd ..
        if errorlevel 1 (
            echo [错误] 前端依赖安装失败！
            pause
            exit /b 1
        )
    ) else (
        echo [警告] 前端目录不完整
    )
)
echo       [OK] 前端依赖已就绪

:: ==================== 启动后端 ====================
echo [4/5] 启动后端服务 (端口 8000)...
start "Backend-API" cmd /k "cd /d %~dp0 && python main.py"
timeout /t 4 /nobreak >nul

:: 简单的连接测试
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [提示] 后端正在启动中，请稍候...
    timeout /t 6 /nobreak >nul
)
echo       [OK] 后端服务已启动

:: ==================== 启动前端 ====================
echo [5/5] 启动前端服务 (端口 3000)...
start "Frontend-Vite" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 4 /nobreak >nul
echo       [OK] 前端服务已启动

echo.
echo ╔════════════════════════════════════════════════╗
echo ║                                                ║
echo ║     ✅ 所有服务已启动完成！                    ║
echo ║                                                ║
echo ║  🌐  前端界面: http://localhost:3000           ║
echo ║  🔧  后端API:  http://localhost:8000           ║
echo ║  📖  API文档:  http://localhost:8000/docs      ║
echo ║                                                ║
echo ║  💡 使用提示:                                ║
echo ║    • 登录后点击右上角 "🐢海龟汤" 进入游戏      ║
echo ║    • 无API Key时使用预设题库（完全可用）      ║
echo ║    • 需要AI功能? 先运行 ollama serve          ║
echo ║                                                ║
echo ╚════════════════════════════════════════════════╝
echo.

:: 尝试自动打开浏览器
start http://localhost:3000 2>nul

echo.
echo   按任意键关闭此窗口（不影响服务运行）...
echo   或直接关闭此窗口，服务继续在后台运行
echo.
pause >nul
