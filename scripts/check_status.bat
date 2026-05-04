@echo off
chcp 65001 >nul 2>nul
title 海龟汤游戏系统 - 状态检查
color 0B

echo.
echo ╔════════════════════════════════════════════════╗
echo ║  🐢 海龟汤游戏系统 - 服务状态检查 v2.0       ║
echo ╚════════════════════════════════════════════════╝
echo.

:: ==================== 检查后端 ====================
echo [1/4] 检查后端服务 (端口 8000)...
curl -s -o nul -w "%%{http_code}" http://localhost:8000/health >backend_status.txt 2>&1
set /p BACKEND_CODE=<backend_status.txt
del backend_status.txt 2>nul

if "%BACKEND_CODE%"=="200" (
    echo       [OK] 后端服务运行正常 (HTTP %BACKEND_CODE%)
    
    :: 获取详细信息
    for /f "tokens=*" %%i in ('curl -s http://localhost:8000/api/status ^| findstr "status"') do (
        echo            %%i
    )
) else (
    if "%BACKEND_CODE%"=="" (
        echo       [FAIL] 后端服务未启动或无法连接
    ) else (
        echo       [WARN] 后端服务异常 (HTTP %BACKEND_CODE%)
    )
)

:: ==================== 检查前端 ====================
echo.
echo [2/4] 检查前端服务 (端口 3000)...
curl -s -o nul -w "%%{http_code}" http://localhost:3000 >frontend_status.txt 2>&1
set /p FRONTEND_CODE=<frontend_status.txt
del frontend_status.txt 2>nul

if "%FRONTEND_CODE%"=="200" (
    echo       [OK] 前端服务运行正常 (HTTP %FRONTEND_CODE%)
) else (
    if "%FRONTEND_CODE%"=="" (
        echo       [FAIL] 前端服务未启动或无法连接
    ) else (
        echo       [WARN] 前端服务异常 (HTTP %FRONTEND_CODE%)
    )
)

:: ==================== 检查Ollama（可选）====================
echo.
echo [3/4] 检查 AI 服务 (Ollama, 可选)...
curl -s -o nul -w "%%{http_code}" http://localhost:11434/api/tags >ollama_status.txt 2>&1
set /p OLLAMA_CODE=<ollama_status.txt
del ollama_status.txt 2>nul

if "%OLLAMA_CODE%"=="200" (
    echo       [OK] Ollama AI 服务运行中
    
    :: 显示已安装模型
    echo 已安装模型:
    curl -s http://localhost:11434/api/tags | findstr "name" | more +1
) else (
    echo       [INFO] Ollama 未运行（AI功能不可用，基础功能正常）
)

:: ==================== 检查端口占用 ====================
echo.
echo [4/4] 检查端口占用情况...
netstat -an | findstr ":3000 :8000 :11434" | findstr "LISTENING" >port_check.txt 2>&1

if exist port_check.txt (
    for /f "tokens=4 delims=: " %%a in ('type port_check.txt ^| findstr ":3000"') do (
        if not "%%a"=="" echo       端口 3000 (前端): 占用中 PID=%%a
    )
    for /f "tokens=4 delims=: " %%a in ('type port_check.txt ^| findstr ":8000"') do (
        if not "%%a"=="" echo       端口 8000 (后端): 占用中 PID=%%a
    )
    for /f "tokens=4 delims=: " %%a in ('type port_check.txt ^| findstr ":11434"') do (
        if not "%%a"=="" echo       端口 11434 (AI): 占用中 PID=%%a
    )
    del port_check.txt
) else (
    echo       无服务正在监听
)

:: ==================== 总结 ====================
echo.
echo ╔════════════════════════════════════════════════╗
echo ║              📊 运行状态总结                  ║
╠════════════════════════════════════════════════╣

if "%BACKEND_CODE%"=="200" (
    if "%FRONTEND_CODE%"=="200" (
        echo ║                                                ║
        echo ║     ✅ 系统完全就绪！                          ║
        echo ║                                                ║
        echo ║  请访问: http://localhost:3000                ║
        echo ║                                                ║
    ) else (
        echo ║                                                ║
        echo ║     ⚠️ 后端正常，前端未启动                    ║
        echo ║                                                ║
        echo ║  请执行: cd frontend && npm run dev           ║
        echo ║                                                ║
    )
) else (
    echo ║                                                ║
    echo ║     ❌ 系统未完全启动                          ║
    echo ║                                                ║
    echo ║  请执行: start_all.bat                         ║
    echo ║                                                ║
)

echo ╚════════════════════════════════════════════════╝
echo.

pause
