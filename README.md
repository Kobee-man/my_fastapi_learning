# 🐢 海龟汤游戏系统 - 完整项目运行指南

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Node.js](https://img.shields.io/badge/node-18.0+-yellow)
![License](https://img.shields.io/badge/license-MIT-orange)

**FastAPI + Vue 3 + Qwen 3.5 (Ollama) 全栈海龟汤游戏系统**

[功能特性](#功能特性) · [快速开始](#快速开始) · [系统架构](#系统架构) · [部署指南](#详细部署指南) · [常见问题](#常见问题)

</div>

---

## 📖 目录

- [🎯 项目概述](#-项目概述)
- [✨ 功能特性](#-功能特性)
- [🏗️ 系统架构](#-系统架构)
- [⚙️ 技术栈](#-技术栈)
- [🚀 快速开始（5分钟启动）](#-快速开始5分钟启动)
- [📋 详细部署指南](#-详细部署指南)
  - [环境要求](#1-环境要求)
  - [安装步骤](#2-安装步骤)
  - [配置说明](#3-配置说明)
  - [启动流程](#4-启动流程)
- [🔧 一键启动脚本](#-一键启动脚本)
- [📊 服务端口分配](#-服务端口分配)
- [🔗 API接口文档](#-api接口文档)
- [🛠️ 开发指南](#-开发指南)
- [❓ 常见问题](#-常见问题)
- [📄 许可证](#-许可证)

---

## 🎯 项目概述

**海龟汤（情境猜谜）游戏系统** 是一个基于 **FastAPI + Vue 3 + 本地大语言模型(Qwen)** 的全栈Web应用。玩家通过与AI主持人进行"是/否"问答来推理出隐藏的故事真相，支持完全离线运行，保护用户隐私。

### 核心亮点
- ✅ **三层权限架构**：公开 → 认证 → 高级(AI增强)
- ✅ **本地AI集成**：使用 Ollama + Qwen 3.5，零API成本
- ✅ **优雅降级**：无AI时自动切换预设题库
- ✅ **实时聊天**：WebSocket 支持多人在线
- ✅ **响应式UI**：Vue 3 + Vite 现代化前端

---

## ✨ 功能特性

### 🎮 游戏核心功能
| 功能 | 说明 | 权限级别 |
|------|------|---------|
| 用户注册/登录 | 滑块验证码 + JWT认证 | 公开 |
| 聊天室 | WebSocket实时通讯 | 已认证 |
| 海龟汤游戏 | AI出题 + 智能判断 | 已认证 |
| LLM题目生成 | Qwen 3.5 动态生成 | 高级(需API Key) |
| 预设题库 | 3道精选题目 | 已认证 |
| 个人中心 | 头像/昵称管理 | 已认证 |

### 🔐 权限系统
```
┌─────────────────────────────────────┐
│  Level 3: PREMIUM (高级)           │
│  • LLM智能题目生成                  │
│  • AI深度答案评估                   │
│  • 需要: API Key 或 本地LLM        │
├─────────────────────────────────────┤
│  Level 2: AUTHENTICATED (已认证)    │
│  • 登录/注册                        │
│  • 聊天室                           │
│  • 预设题目游戏                      │
│  • 需要: JWT Token                 │
├─────────────────────────────────────┤
│  Level 1: PUBLIC (公开)            │
│  • 访问登录页                       │
│  • 查看系统状态                     │
│  • 查看 API 文档                    │
│  • 无需任何验证                     │
└─────────────────────────────────────┘
```

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      用户浏览器                          │
│              (Chrome / Firefox / Edge)                │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/WebSocket
                       ▼
┌─────────────────────────────────────────────────────────┐
│               前端服务 (Vite Dev Server)                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Vue 3 Application                              │   │
│  │  ├── LoginView.vue      (登录页面)             │   │
│  │  ├── ChatView.vue       (聊天+游戏)             │   │
│  │  ├── TurtleSoupGame.vue (海龟汤组件)           │   │
│  │  ├── CatAvatar.vue      (猫头像)               │   │
│  │  └── SliderVerify.vue   (滑块验证)             │   │
│  └─────────────────────────────────────────────────┘   │
│  • Port: 3000                                        │
│  • Proxy: /api → localhost:8000                      │
│  • Proxy: /ws → ws://localhost:8000                  │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API / WebSocket
                       ▼
┌─────────────────────────────────────────────────────────┐
│              后端服务 (FastAPI + Uvicorn)                │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐    │
│  │  Auth API   │  │  Chat API   │  │Turtle Soup   │    │
│  │  认证模块   │  │  聊天模块   │  │  游戏模块     │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘    │
│         │                │               │             │
│  ┌──────▼────────────────▼──────────────▼───────────┐  │
│  │              Core Modules                          │  │
│  │  ├── permissions.py   (权限管理系统)             │  │
│  │  ├── security.py       (JWT安全)                 │  │
│  │  ├── database.py       (数据库ORM)               │  │
│  │  └── thread_pool.py    (线程池管理)              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  • Port: 8000                                         │
│  • Database: SQLite (sqlite:///turtle_soup.db)        │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP (可选)
                       ▼
┌─────────────────────────────────────────────────────────┐
│           AI 服务 (Ollama + Qwen 3.5) [可选]            │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  QwenClient (专用客户端)                         │   │
│  │  • 智能连接管理                                   │   │
│  │  • 自动重试机制 (3次)                             │   │
│  │  • 响应缓存加速                                   │   │
│  │  • 性能监控统计                                   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  • Host: http://localhost:11434                       │
│  • Model: qwen3.5:4b                                 │
│  • Size: ~2.3 GB                                      │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ 技术栈

### 后端技术
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 主要开发语言 |
| FastAPI | 0.100+ | Web框架 |
| Uvicorn | 0.23+ | ASGI服务器 |
| SQLModel | 0.0.8+ | ORM数据库操作 |
| Pydantic | 2.0+ | 数据验证 |
| WebSockets | 标准 | 实时通信 |
| python-jose | 3.3+ | JWT令牌处理 |
| passlib | 1.7+ | 密码哈希 |
| requests | 2.31+ | HTTP客户端(Ollama) |

### 前端技术
| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.4+ | 前端框架 |
| Vite | 5.2+ | 构建工具 |
| Vue Router | 4.3+ | 路由管理 |
| Pinia | 2.1+ | 状态管理 |
| Axios | 1.6+ | HTTP请求 |

### AI服务（可选）
| 技术 | 版本 | 用途 |
|------|------|------|
| Ollama | 最新版 | 本地LLM运行时 |
| Qwen | 3.5:4b | 大语言模型 |

---

## 🚀 快速开始（5分钟启动）

### 方式一：基础模式（无需AI，推荐新手）

```powershell
# 1️⃣ 克隆/进入项目目录
cd d:\my_fastapi

# 2️⃣ 启动后端服务
python main.py

# 3️⃣ 新开终端，进入前端目录
cd frontend

# 4️⃣ 安装依赖（首次需要）
npm install

# 5️⃣ 启动前端开发服务器
npm run dev

# 6️⃣ 打开浏览器访问
# 前端: http://localhost:3000
# 后端: http://localhost:8000
```

### 方式二：完整模式（含AI功能）

```powershell
# 0️⃣ 预置条件：确保已安装并运行 Ollama
ollama serve
ollama pull qwen3.5:4b

# 1️⃣ - 5️⃣ 同上...

# 6️⃣ 享受AI增强的海龟汤游戏！🐢
```

### 方式三：一键启动（高级用户）

```powershell
# 使用提供的一键启动脚本
.\start_all.bat          # Windows PowerShell
# 或
bash start_all.sh        # Linux/macOS Git Bash
```

**查看详细启动状态：**
```powershell
# Windows
.\check_status.bat

# Linux/macOS
bash check_status.sh
```

---

## 📋 详细部署指南

### 1️⃣ 环境要求

#### 操作系统
- ✅ Windows 10/11 (推荐)
- ✅ macOS 12+
- ✅ Ubuntu 20.04+

#### 必须安装的软件

| 软件 | 最低版本 | 推荐版本 | 安装方式 |
|------|---------|---------|---------|
| **Python** | 3.8 | 3.10+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18.0 | 20 LTS | [nodejs.org](https://nodejs.org/) |
| **npm** | 9.0 | 10+ | 随 Node.js 安装 |
| **Git** | 2.30+ | 最新版 | [git-scm.com](https://git-scm.com/) |

#### 可选软件（AI功能需要）
| 软件 | 用途 | 安装方式 |
|------|------|---------|
| **Ollama** | 运行本地LLM | [ollama.ai](https://ollama.ai/download) |

#### 硬件要求（运行AI功能时）

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4核 | 8核+ |
| RAM | 8GB | 16GB+ |
| GPU | 无 | NVIDIA 6GB+ VRAM (可选) |
| 存储 | 10GB可用 | SSD 20GB+ |

---

### 2️⃣ 安装步骤

#### Step 1: 安装 Python 及依赖

```powershell
# 验证 Python 版本
python --version
# 应显示: Python 3.x.x (建议 >= 3.10)

# 如果未安装或版本过低:
# Windows: 从 https://www.python.org/downloads/ 下载安装
# macOS: brew install python@3.11
# Linux: sudo apt install python3.11 python3-pip

# 进入项目根目录
cd d:\my_fastapi

# 创建虚拟环境（强烈推荐）
python -m venv venv

# 激活虚拟环境
# Windows PowerShell:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt

# 如果没有 requirements.txt，手动安装核心依赖:
pip install fastapi uvicorn sqlmodel python-jose passlib bcrypt requests
```

#### Step 2: 安装 Node.js 和前端依赖

```powershell
# 验证 Node.js 版本
node --version
npm --version
# Node: v18.0.0+ / npm: 9.0.0+

# 如果未安装:
# Windows: 从 https://nodejs.org/ 下载 LTS 版本
# macOS: brew install node
# Linux: sudo apt install nodejs npm

# 进入前端目录
cd frontend

# 清理旧的依赖（如果存在）
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item package-lock.json -ErrorAction SilentlyContinue

# 安装依赖
npm install

# 验证安装成功
npm list vue vite @vitejs/plugin-vue esbuild
# 应该显示已安装的包及其版本
```

#### Step 3: （可选）安装 Ollama 和 AI 模型

```powershell
# 下载并安装 Ollama
# Windows: winget install Ollama.Ollama
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# 启动 Ollama 服务
ollama serve

# 新开终端，安装 Qwen 3.5 4B 模型
ollama pull qwen3.5:4b
# 下载约 2.3GB，等待 "Success" 提示

# 验证安装
ollama list
# 应该看到: qwen3.5:4b
```

---

### 3️⃣ 配置说明

#### 3.1 后端配置 (main.py)

编辑 `main.py` 可修改以下默认值：

```python
# 第21-52行附近的应用配置
app = FastAPI(
    title="FastAPI Vue 前端系统",
    version="2.0.0",
    # ... 其他配置
)

# 第54-60行的CORS配置（如需跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 3.2 前端配置 (frontend/vite.config.js)

```javascript
// 第4-35行
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,              // 前端端口
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',  // 后端地址
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',  // WebSocket代理
        ws: true
      }
    }
  }
})
```

#### 3.3 AI配置 (core/permissions.py)

```python
# 第39行附近
self.api_key_env_var = "OPENAI_API_KEY"  # 如使用云端API

# 对于本地Ollama，无需设置此变量
# 系统会自动检测 Ollama 是否可用
```

#### 3.4 环境变量（可选创建 .env 文件）

在项目根目录创建 `.env` 文件：

```bash
# ==================== 后端配置 ====================

# 应用端口
PORT=8000

# 数据库路径
DATABASE_URL=sqlite:///./turtle_soup.db

# JWT密钥（生产环境请更改！）
SECRET_KEY=your-secret-key-here-change-in-production

# Token过期时间（小时）
ACCESS_TOKEN_EXPIRE_HOURS=24

# ==================== AI配置（可选）====================

# OpenAI API Key（如使用云端API）
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_URL=https://api.openai.com/v1/chat/completions
OPENAI_MODEL=gpt-3.5-turbo

# ==================== Ollama配置（本地AI）===================
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3.5:4b
```

---

### 4️⃣ 启动流程

#### 正确的启动顺序

```
顺序  服务              命令                          端口    依赖
────  ────────────────  ──────────────────────────────  ────  ──────
 ①    Ollama (可选)    ollama serve                   11434   无
 ②    后端API         python main.py                  8000    ①(可选)
 ③    前端Dev Server   cd frontend && npm run dev      3000    ②
 ④    浏览器访问       http://localhost:3000            -      ③
```

#### 详细启动命令

##### **终端1：启动后端服务**

```powershell
# 进入项目根目录
cd d:\my_fastapi

# 激活虚拟环境（如果使用了venv）
venv\Scripts\activate

# 启动后端（两种方式选一）:

# 方式A：直接启动（简单）
python main.py

# 方式B：使用uvicorn启动（支持热重载）
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 预期输出:
# [PermissionManager] 初始化完成
#   - LLM功能: [X] 未配置  (或 [OK] 如果有API Key/Ollama)
#   - 预设题目: [OK]
# INFO:     Started server process [xxxxx]
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**验证后端启动成功：**
```powershell
# 新开PowerShell窗口，执行:
curl http://localhost:8000/health

# 预期返回:
# {"status":"healthy","service":"FastAPI Vue Frontend","version":"2.0.0","database":"connected","llm_status":"not_configured"}
```

##### **终端2：启动前端服务**

```powershell
# 新开一个终端窗口

# 进入前端目录
cd d:\my_fastapi\frontend

# 启动Vite开发服务器
npm run dev

# 或者使用npx（如果没有全局安装vite）
npx vite --host

# 预期输出:
#
#   VITE v5.2.8  ready in xxx ms
#
#   ➜  Local:   http://localhost:3000/
#   ➜  Network: use --host to expose
#
```

**验证前端启动成功：**
- 浏览器打开 `http://localhost:3000`
- 应该看到登录页面（带猫头像和滑块验证）

##### **终端3：（可选）启动AI服务**

```powershell
# 仅在使用AI功能时需要

# 确保Ollama正在运行
ollama serve

# 验证Ollama状态
curl http://localhost:11434/api/tags

# 运行AI测试（可选）
python turtle_soup_qwen.py
# 选择菜单 3 查看性能报告
```

---

## 🔧 一键启动脚本

### Windows PowerShell 脚本

创建文件 `start_all.bat`：

```batch
@echo off
chcp 65001 >nul
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
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2 delims=. " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo       ✓ Python %PYVER% 已就绪

:: ==================== 检查Node.js ===================
echo [2/5] 检查 Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js！请先安装 Node.js 18+
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=1 delims=v" %%v in ('node --version 2^>^&1') do set NODEVER=%%v
echo       ✓ Node.js %NODEVER% 已就绪

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
echo       ✓ Python 依赖已就绪

:: 检查前端依赖
if not exist "frontend\node_modules\.package-lock.json" (
    echo [提示] 正在安装前端依赖...
    cd frontend
    call npm install --silent
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败！
        cd ..
        pause
        exit /b 1
    )
    cd ..
)
echo       ✓ 前端依赖已就绪

:: ==================== 启动后端 ====================
echo [4/5] 启动后端服务 (端口 8000)...
start "Backend-API" cmd /k "cd /d d:\my_fastapi && python main.py"
timeout /t 3 /nobreak >nul

:: 检查后端是否启动成功
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [警告] 后端启动可能较慢，请稍候...
    timeout /t 5 /nobreak >nul
)
echo       ✓ 后端服务启动中...

:: ==================== 启动前端 ====================
echo [5/5] 启动前端服务 (端口 3000)...
start "Frontend-Vite" cmd /k "cd /d d:\my_fastapi\frontend && npm run dev"
timeout /t 3 /nobreak >nul
echo       ✓ 前端服务启动中...

echo.
echo ╔════════════════════════════════════════════════╗
echo ║                                                ║
echo ║  ✅ 所有服务已启动！                            ║
echo ║                                                ║
echo ║  🌐 前端界面: http://localhost:3000           ║
echo ║  🔧 后端API:  http://localhost:8000           ║
echo ║  📖 API文档:  http://localhost:8000/docs      ║
echo ║                                                ║
echo ║  按 Ctrl+C 关闭此窗口（不影响服务）         ║
echo ╚════════════════════════════════════════════════╝
echo.

:: 打开浏览器（可选）
start http://localhost:3000

:: 保持脚本运行（按任意键退出）
pause >nul
```

### Linux/macOS Shell 脚本

创建文件 `start_all.sh`：

```bash
#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════╗"
echo "║  🐢 海龟汤游戏系统 - 一键启动脚本 v2.0       ║"
echo "╚════════════════════════════════════════════════╝"
echo -e "${NC}"

# 检查Python
echo -e "\n${YELLOW}[1/5]${NC} 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[错误]${NC} 未找到 Python3！请先安装"
    exit 1
fi
PYTHON_VER=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "       ${GREEN}✓${NC} Python $PYTHON_VER 已就绪"

# 检查Node.js
echo -e "${YELLOW}[2/5]${NC} 检查 Node.js 环境..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}[错误]${NC} 未找到 Node.js！请先安装"
    exit 1
fi
NODE_VER=$(node --version 2>&1)
echo -e "       ${GREEN}✓${NC} Node.js $NODE_VER 已就绪"

# 检查并安装依赖
echo -e "${YELLOW}[3/5]${NC} 检查项目依赖..."

# Python依赖
python3 -c "import fastapi, uvicorn, sqlmodel" &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "       [提示] 安装 Python 依赖..."
    pip3 install -q fastapi uvicorn sqlmodel python-jose passlib requests
fi
echo -e "       ${GREEN}✓${NC} Python 依赖已就绪"

# 前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo -e "       [提示] 安装前端依赖..."
    cd frontend && npm install --silent && cd ..
fi
echo -e "       ${GREEN}✓${NC} 前端依赖已就绪"

# 启动后端
echo -e "${YELLOW}[4/5]${NC} 启动后端服务 (端口 8000)..."
python3 main.py &
BACKEND_PID=$!
sleep 3
echo -e "       ${GREEN}✓${NC} 后端服务已启动 (PID: $BACKEND_PID)"

# 启动前端
echo -e "${YELLOW}[5/5]${NC} 启动前端服务 (端口 3000)..."
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..
sleep 3
echo -e "       ${GREEN}✓${NC} 前端服务已启动 (PID: $FRONTEND_PID)"

# 完成
echo -e "\n${CYAN}"
echo "╔════════════════════════════════════════════════╗"
echo "║                                                ║"
echo "║  ${GREEN}✅ 所有服务已启动！${NC}                        ║"
echo "║                                                ║"
echo "║  🌐 前端界面: http://localhost:3000           ║"
echo "║  🔧 后端API:  http://localhost:8000           ║"
echo "║  📖 API文档:  http://localhost:8000/docs      ║"
echo "║                                                ║"
echo "║  按 Ctrl+C 停止所有服务                      ║"
echo "╚════════════════════════════════════════════════╝"
echo -e "${NC}"

# 尝试打开浏览器
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000 &>/dev/null &
elif command -v open &> /dev/null; then
    open http://localhost:3000 &>/dev/null &
fi

# 等待中断信号
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
```

**赋予执行权限：**
```bash
chmod +x start_all.sh
```

---

## 📊 服务端口分配

| 服务 | 端口 | 协议 | 用途 | 启动顺序 |
|------|------|------|------|---------|
| **前端 Dev Server** | 3000 | HTTP | Vue应用 | ③ 最后 |
| **后端 API Server** | 8000 | HTTP/WS | FastAPI服务 | ② 第二 |
| **Ollama AI Service** | 11434 | HTTP | 本地LLM运行时 | ① 最前(可选) |

### 端口占用检查

```powershell
# Windows PowerShell
netstat -an | findstr ":3000 :8000 :11434"

# Linux/macOS
lsof -i :3000 -i :8000 -i :11434 || netstat -tlnp | grep -E '3000|8000|11434'
```

**如果端口被占用：**
```powershell
# 查找占用进程
netstat -ano | findstr :3000
# 显示: TCP  0.0.0.0:3000  0.0.0.0:0  LISTENING  12345

# 结束进程（PID替换为实际ID）
taskkill /PID 12345 /F
```

---

## 🔗 API接口文档

### 在线交互式文档

启动后端服务后访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 核心API端点

#### 公开接口（无需登录）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 登录页面 |
| GET | `/health` | 健康检查 |
| GET | `/api/status` | 系统状态与权限信息 |
| GET | `/api/features` | 功能列表详情 |

#### 认证接口（需要JWT Token）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/register` | 用户注册 |
| POST | `/login` | 用户登录 |
| POST | `/forgot-password` | 找回密码 |
| GET | `/profile` | 获取个人资料 |
| PUT | `/user/nickname` | 修改昵称 |
| POST | `/user/avatar` | 上传头像 |

#### 游戏接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/turtle-soup/rules` | 游戏规则 |
| POST | `/turtle-soup/check-status` | AI/LLM状态检查 |
| POST | `/turtle-soup/create-game` | 创建新游戏 |
| POST | `/turtle-soup/join-game` | 加入游戏 |
| POST | `/turtle-soup/start-game` | 开始游戏 |
| POST | `/turtle-soup/ask-question` | 提交问题 |
| POST | `/turtle-soup/submit-answer` | 提交答案 |
| GET | `/turtle-soup/hint` | 获取提示 |
| GET | `/turtle-soup/game-status/{id}` | 游戏状态 |
| DELETE | `/turtle-soup/game/{id}` | 删除/离开游戏 |

#### WebSocket接口
| 路径 | 说明 |
|------|------|
| `/ws/chat/{token}` | 聊天室WebSocket |
| `/ws/private-chat/{token}/{uid}` | 私聊WebSocket |

---

## 🛠️ 开发指南

### 项目目录结构

```
d:\my_fastapi/
├── main.py                      # FastAPI应用入口
├── start_server.py              # 生产启动脚本
├── turtle_soup_ollama.py       # CLI独立版（Ollama通用）
├── turtle_soup_qwen.py          # CLI优化版（Qwen专用）
├── test_qwen_integration.py     # 集成测试套件
│
├── api/                         # API路由模块
│   ├── __init__.py
│   ├── auth.py                 # 认证接口
│   ├── chat.py                 # 聊天接口
│   ├── turtle_soup.py          # 海龟汤游戏接口
│   └── user.py                 # 用户接口
│
├── core/                        # 核心模块
│   ├── permissions.py           # 权限管理系统
│   ├── config.py                # 配置管理
│   ├── database.py              # 数据库连接
│   ├── security.py              # 安全/JWT
│   ├── thread_pool.py           # 线程池
│   └── utils.py                 # 工具函数
│
├── models/                      # 数据模型
│   ├── db_models.py             # 数据库模型
│   └── user.py                 # 用户模型
│
├── frontend/                    # Vue前端项目
│   ├── index.html               # 入口HTML
│   ├── package.json             # 依赖配置
│   ├── vite.config.js           # Vite配置
│   │
│   ├── src/
│   │   ├── main.js              # 入口文件
│   │   ├── App.vue              # 根组件
│   │   │
│   │   ├── views/
│   │   │   ├── LoginView.vue    # 登录页
│   │   │   └── ChatView.vue     # 聊天/游戏页
│   │   │
│   │   ├── components/
│   │   │   ├── CatAvatar.vue    # 猫头像组件
│   │   │   ├── SliderVerify.vue # 滑块验证组件
│   │   │   └── TurtleSoupGame.vue # 游戏主组件
│   │   │
│   │   ├── composables/
│   │   │   └── useEyeTracking.js # 眼睛跟踪逻辑
│   │   │
│   │   ├── router/
│   │   │   └── index.js        # 路由配置
│   │   │
│   │   └── utils/
│   │       └── api.js           # API封装
│   │
│   └── tests/
│       └── unit/
│           └── SliderVerify.spec.js
│
├── static/                      # 静态资源
│   └── (CSS/JS/Images)
│
├── login.html                   # 独立登录页（备用）
├── chat.html                    # 独立聊天页（备用）
│
├── *.md                         # 文档文件
└── README.md                    # 本文件
```

### 开发工作流

#### 1. 后端开发

```powershell
# 激活虚拟环境
venv\Scripts\activate

# 启动开发服务器（热重载模式）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
pytest tests/

# 代码格式化
black .
isort .
```

#### 2. 前端开发

```powershell
# 进入前端目录
cd frontend

# 启动开发服务器（热更新）
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 运行单元测试
npm run test:unit

# 代码检查
npm run lint
```

#### 3. AI功能开发

```powershell
# 运行CLI版本（用于调试AI功能）
python turtle_soup_qwen.py

# 运行集成测试
python test_qwen_integration.py

# 测试特定功能
python test_qwen_integration.py --help
```

---

## ❓ 常见问题

### Q1: 前端页面空白或报错？

**可能原因及解决：**

1. **后端未启动**
   ```powershell
   # 检查后端是否运行
   curl http://localhost:8000/health
   
   # 如果无响应，先启动后端
   python main.py
   ```

2. **前端依赖未安装**
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

3. **端口冲突**
   ```powershell
   # 查看端口占用
   netstat -ano | findstr :3000
   
   # 修改前端端口（编辑 vite.config.js）
   port: 3001  # 改为其他端口
   ```

---

### Q2: 注册/登录失败？

**排查步骤：**

1. **检查后端日志**
   - 查看终端是否有错误输出
   
2. **检查数据库文件**
   ```powershell
   # 项目目录下应该有 turtle_soup.db 文件
   dir *.db
   ```

3. **清除浏览器缓存**
   - 按 F12 打开开发者工具
   - Application → Storage → Clear site data
   - 刷新页面

---

### Q3: 海龟汤游戏无法使用？

**分情况处理：**

**情况A：显示"题目还没准备好"**
- 这是正常现象！系统在没有API Key时会使用预设题库
- 点击"开始新游戏"即可使用3道预设题目
- 功能完全正常，不受影响

**情况B：想使用AI功能**
```powershell
# 步骤1: 安装并启动Ollama
ollama serve

# 步骤2: 安装Qwen模型
ollama pull qwen3.5:4b

# 步骤3: 重启后端
# Ctrl+C 停止当前后端
python main.py  # 重新启动

# 步骤4: 刷新前端页面
# 应该看到 "🚀 AI增强模式" 提示
```

---

### Q4: 如何切换到其他AI模型？

**方法1：临时指定**
```powershell
python turtle_soup_qwen.py --model=mistral
```

**方法2：修改默认配置**
```python
# 编辑 turtle_soup_qwen.py 第920行
qwen_config = QwenConfig(
    model="mistral",  # ← 改为你想要的模型
    ...
)
```

**可用模型列表：**
```powershell
ollama list  # 查看已安装模型

# 推荐安装更多模型
ollama pull llama3        # Meta Llama 3
ollama pull mistral       # Mistral 7B
ollama pull phi3          # Microsoft Phi-3
```

---

### Q5: 性能太慢怎么办？

**优化方案：**

| 问题 | 解决方案 |
|------|---------|
| 前端加载慢 | 检查网络，清除浏览器缓存 |
| 后端响应慢 | 升级Python到3.11+，使用uvloop |
| AI判断慢 | 使用更小的模型（如phi3:3.8b） |
| 整体卡顿 | 关闭其他程序，增加内存 |

**启用GPU加速（如果有NVIDIA显卡）：**
```powershell
# Ollama会自动检测并使用GPU
# 可以在任务管理器查看GPU使用率

# 手动指定CUDA
$env:CUDA_VISIBLE_DEVICES="0"
ollama serve
```

---

### Q6: 如何在生产环境部署？

**推荐方案：Docker Compose**

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite:///data/turtle_soup.db
      - SECRET_KEY=${SECRET_KEY:-change-me-in-production}
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  ollama:  # 可选
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
```

**启动生产环境：**
```bash
docker-compose up -d --build
```

---

## 📄 许可证

MIT License

Copyright (c) 2026 海龟汤游戏系统项目组

**免责声明：**
- 本项目仅供学习和研究使用
- 请遵守当地法律法规
- 商用请联系作者获取授权

---

## 🙏 致谢

感谢以下开源项目的贡献者：
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Vite](https://vitejs.dev/) - 下一代前端构建工具
- [Ollama](https://ollama.ai/) - 本地大语言模型运行时
- [Qwen](https://qwenlm.github.io/) - 通义千问大语言模型

---

## 📞 技术支持

- **问题反馈**: 请提交 GitHub Issue
- **功能建议**: 欢迎 Pull Request
- **讨论交流**: 加入社区讨论组

---

<div align="center">

**Made with ❤️ using FastAPI + Vue 3 + Qwen 3.5**

**最后更新**: 2026-05-03

</div>
