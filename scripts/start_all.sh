#!/bin/bash

# 海龟汤游戏系统 - 一键启动脚本 (Linux/macOS)
# Version: 2.0
# Usage: bash start_all.sh

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "╔════════════════════════════════════════════════╗"
echo "║  🐢 海龟汤游戏系统 - 一键启动脚本 v2.0       ║"
echo "╚════════════════════════════════════════════════╝"
echo -e "${NC}"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ==================== 检查Python ====================
echo -e "\n${YELLOW}[1/5]${NC} 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}[错误]${NC} 未找到 Python！请先安装 Python 3.10+"
    echo ""
    echo "  安装方法:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  macOS: brew install python@3.11"
    echo "  或访问: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VER=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "       ${GREEN}✓${NC} Python $PYTHON_VER 已就绪"

# ==================== 检查Node.js ===================
echo -e "${YELLOW}[2/5]${NC} 检查 Node.js 环境..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}[错误]${NC} 未找到 Node.js！请先安装 Node.js 18+"
    echo ""
    echo "  安装方法:"
    echo "  使用 nvm (推荐): curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
    echo "  直接下载: https://nodejs.org/"
    exit 1
fi

NODE_VER=$(node --version 2>&1)
NPM_VER=$(npm --version 2>&1)
echo -e "       ${GREEN}✓${NC} Node.js $NODE_VER 已就绪"
echo -e "       ${GREEN}✓${NC} npm $NPM_VER 已就绪"

# ==================== 检查并安装依赖 ====================
echo -e "${YELLOW}[3/5]${NC} 检查项目依赖..."

# Python依赖
$PYTHON_CMD -c "import fastapi, uvicorn, sqlmodel" &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "       [提示] 安装 Python 依赖..."
    pip3 install -q fastapi uvicorn sqlmodel python-jose passlib requests
    if [ $? -ne 0 ]; then
        echo -e "${RED}[错误]${NC} Python 依赖安装失败！"
        exit 1
    fi
fi
echo -e "       ${GREEN}✓${NC} Python 依赖已就绪"

# 前端依赖
if [ ! -d "frontend/node_modules" ] || [ ! -f "frontend/node_modules/vue/index.js" ]; then
    if [ -f "frontend/package.json" ]; then
        echo -e "       [提示] 安装前端依赖（首次需要几分钟）..."
        cd frontend && npm install --silent && cd ..
        if [ $? -ne 0 ]; then
            echo -e "${RED}[错误]${NC} 前端依赖安装失败！"
            exit 1
        fi
    else
        echo -e "${YELLOW}[警告]${NC} frontend/package.json 不存在，跳过前端依赖安装"
    fi
fi
echo -e "       ${GREEN}✓${NC} 前端依赖已就绪"

# ==================== 启动后端 ====================
echo -e "${YELLOW}[4/5]${NC} 启动后端服务 (端口 8000)..."
$PYTHON_CMD main.py &
BACKEND_PID=$!
sleep 3

# 等待后端启动
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo -e "       ${GREEN}✓${NC} 后端服务已启动 (PID: $BACKEND_PID)"

# ==================== 启动前端 ====================
echo -e "${YELLOW}[5/5]${NC} 启动前端服务 (端口 3000)..."
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    cd frontend && npm run dev &
    FRONTEND_PID=$!
    cd ..
    sleep 3
    echo -e "       ${GREEN}✓${NC} 前端服务已启动 (PID: $FRONTEND_PID)"
else
    echo -e "${YELLOW}[提示]${NC} 前端目录不存在或配置缺失，跳过前端启动"
    FRONTEND_PID=""
fi

# 完成
echo -e "\n${CYAN}"
echo "╔════════════════════════════════════════════════╗"
echo "║                                                ║"
echo -e "║     ${GREEN}✅ 所有服务已启动完成！${NC}                        ║"
echo "║                                                ║"
echo "║  🌐  前端界面: http://localhost:3000           ║"
echo "║  🔧  后端API:  http://localhost:8000           ║"
echo "║  📖  API文档:  http://localhost:8000/docs      ║"
echo "║                                                ║"
echo "║  💡 使用提示:                                ║"
echo "║    • 登录后点击右上角 '🐢海龟汤' 进入游戏      ║"
echo "║    • 无API Key时使用预设题库（完全可用）      ║"
echo "║    • 需要AI功能? 先运行: ollama serve          ║"
echo "║                                                ║"
echo "╚════════════════════════════════════════════════╝"
echo -e "${NC}"

# 尝试打开浏览器
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000 &>/dev/null &
elif command -v open &> /dev/null; then
    open http://localhost:3000 &>/dev/null &
elif command -s cmd.exe &> /dev/null; then
    # Git Bash on Windows
    cmd.exe //C start http://localhost:3000 &>/dev/null &
fi

echo ""
echo -e "   ${YELLOW}按 Ctrl+C 停止所有服务${NC}"

# 清理函数
cleanup() {
    echo -e "\n\n${YELLOW}[清理] 正在停止所有服务...${NC}"
    
    if [ ! -z "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null
        echo "       已停止前端服务"
    fi
    
    if [ ! -z "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null
        echo "       已停止后端服务"
    fi
    
    # 额外清理可能残留的进程
    pkill -f "uvicorn main:app" 2>/dev/null
    pkill -f "vite" 2>/dev/null
    
    echo -e "${GREEN}✓ 所有服务已停止${NC}\n"
    exit 0
}

# 注册信号处理
trap cleanup SIGINT SIGTERM SIGHUP

# 等待
wait
