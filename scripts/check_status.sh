#!/bin/bash

# 海龟汤游戏系统 - 服务状态检查 (Linux/macOS)
# Version: 2.0
# Usage: bash check_status.sh

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "╔════════════════════════════════════════════════╗"
echo "║  🐢 海龟汤游戏系统 - 服务状态检查 v2.0       ║"
echo "╚════════════════════════════════════════════════╝"
echo -e "${NC}"

# 获取当前时间
echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ==================== 检查后端 ====================
echo -e "${YELLOW}[1/4]${NC} 检查后端服务 (端口 8000)..."
BACKEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)

if [ "$BACKEND_CODE" == "200" ]; then
    echo -e "       ${GREEN}✓${NC} 后端服务运行正常 (HTTP $BACKEND_CODE)"
    
    # 获取系统状态摘要
    STATUS_INFO=$(curl -s http://localhost:8000/api/status 2>/dev/null | head -c 200)
    if [ ! -z "$STATUS_INFO" ]; then
        echo "       状态信息: $STATUS_INFO..."
    fi
else
    if [ -z "$BACKEND_CODE" ]; then
        echo -e "       ${RED}✗${NC} 后端服务未启动或无法连接"
    else
        echo -e "       ${YELLOW}!${NC} 后端服务异常 (HTTP $BACKEND_CODE)"
    fi
fi

# ==================== 检查前端 ====================
echo ""
echo -e "${YELLOW}[2/4]${NC} 检查前端服务 (端口 3000)..."
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)

if [ "$FRONTEND_CODE" == "200" ]; then
    echo -e "       ${GREEN}✓${NC} 前端服务运行正常 (HTTP $FRONTEND_CODE)"
else
    if [ -z "$FRONTEND_CODE" ]; then
        echo -e "       ${RED}✗${NC} 前端服务未启动或无法连接"
    else
        echo -e "       ${YELLOW}!${NC} 前端服务异常 (HTTP $FRONTEND_CODE)"
    fi
fi

# ==================== 检查Ollama（可选）====================
echo ""
echo -e "${YELLOW}[3/4]${NC} 检查 AI 服务 (Ollama, 可选)..."
OLLAMA_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:11434/api/tags 2>/dev/null)

if [ "$OLLAMA_CODE" == "200" ]; then
    echo -e "       ${GREEN}✓${NC} Ollama AI 服务运行中"
    
    # 显示已安装模型数量
    MODEL_COUNT=$(curl -s http://localhost:11434/api/tags 2>/dev/null | grep -c '"name"' || echo "0")
    echo "       已安装模型数: $MODEL_COUNT"
    
    # 显示模型列表（如果有的话）
    if [ "$MODEL_COUNT" -gt "0" ]; then
        echo "       模型列表:"
        curl -s http://localhost:11434/api/tags 2>/dev/null | \
            grep '"name"' | sed 's/.*"name": "//;s/".*//' | while read model; do
            echo "         • $model"
        done
    fi
else
    echo -e "       ${CYAN}○${NC} Ollama 未运行（AI功能不可用，基础功能正常）"
fi

# ==================== 检查端口占用 ====================
echo ""
echo -e "${YELLOW}[4/4]${NC} 检查端口占用情况..."

check_port() {
    local port=$1
    local name=$2
    
    if command -v lsof &> /dev/null; then
        PID=$(lsof -i :$port -t 2>/dev/null | head -1)
        if [ ! -z "$PID" ]; then
            echo -e "       ${GREEN}✓${NC} 端口 $port ($name): 运行中 (PID: $PID)"
        else
            echo -e "       ${RED}✗${NC} 端口 $port ($name): 未监听"
        fi
    elif command -v netstat &> /dev/null; then
        LISTENING=$(netstat -tlnp 2>/dev/null | grep ":$port ")
        if [ ! -z "$LISTENING" ]; then
            echo -e "       ${GREEN}✓${NC} 端口 $port ($name): 监听中"
        else
            echo -e "       ${RED}✗${NC} 端口 $port ($name): 未监听"
        fi
    elif command -v ss &> /dev/null; then
        LISTENING=$(ss -tlnp 2>/dev/null | grep ":$port ")
        if [ ! -z "$LISTENING" ]; then
            echo -e "       ${GREEN}✓${NC} 端口 $port ($name): 监听中"
        else
            echo -e "       ${RED}✗${NC} 端口 $port ($name): 未监听"
        fi
    else
        echo -e "       ${YELLOW}?${NC} 端口 $port ($name): 无法检测（缺少工具）"
    fi
}

check_port 3000 "前端"
check_port 8000 "后端"
check_port 11434 "AI服务"

# ==================== 总结 ====================
echo ""
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════╗"
echo "║              📊 运行状态总结                  ║"
echo "╠════════════════════════════════════════════════╣"

if [ "$BACKEND_CODE" == "200" ] && [ "$FRONTEND_CODE" == "200" ]; then
    echo -e "║                                                ║"
    echo -e "║     ${GREEN}${BOLD}✅ 系统完全就绪！${NC}                          ║"
    echo -e "║                                                ║"
    echo "║  请访问: http://localhost:3000                ║"
    echo "║                                                ║"
elif [ "$BACKEND_CODE" == "200" ]; then
    echo -e "║                                                ║"
    echo -e "║     ${YELLOW}⚠️ 后端正常，前端未启动${NC}                    ║"
    echo -e "║                                                ║"
    echo "║  启动命令: cd frontend && npm run dev           ║"
    echo -e "║                                                ║"
else
    echo -e "║                                                ║"
    echo -e "║     ${RED}❌ 系统未完全启动${NC}                          ║"
    echo -e "║                                                ║"
    echo "║  启动命令: ./start_all.sh                        ║"
    echo -e "║                                                ║"
fi

echo "╚════════════════════════════════════════════════╝"
echo ""

# 快速操作提示
echo -e "${CYAN}快速操作:${NC}"
echo "  • 一键启动:   bash start_all.sh"
echo "  • 查看文档:   cat README.md"
echo "  • 停止服务:   Ctrl+C (在启动脚本窗口中)"
echo ""
