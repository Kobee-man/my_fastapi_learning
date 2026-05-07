# Turtle Soup Game | 海龟汤游戏

**FastAPI + Vue 3 + Qwen 3.5 (Ollama)** — A full-stack "Turtle Soup" situation puzzle game with real-time chat.

---

## Features

- User registration/login with JWT authentication
- Real-time chat room (WebSocket)
- Turtle Soup puzzle game with AI host (LLM-powered)
- Preset puzzle bank (works without AI)
- Graceful degradation when LLM is unavailable
- Cat avatar generator + slider verification

---

## Quick Start

### 1. Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Start server (port 8000)
python main.py
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev    # Dev server at http://localhost:3000
```

### 3. One-click Start

```bash
# Windows
scripts/start_all.bat

# Linux/macOS
bash scripts/start_all.sh
```

Open http://localhost:3000 in your browser.

---

## AI Features (Optional)

Install [Ollama](https://ollama.ai) for AI-powered puzzle generation and judgment:

```bash
ollama serve
ollama pull qwen3.5:4b
```

The game works fine without AI — it falls back to 3 preset puzzles.

---

## Project Structure

```
├── main.py                  # FastAPI entry point
├── requirements.txt         # Python dependencies
├── api/                     # API route handlers
│   ├── auth.py              # Register / Login
│   ├── user.py              # Profile / Avatar
│   ├── chat.py              # WebSocket chat
│   └── turtle_soup.py       # Game logic
├── core/                    # Core modules
│   ├── config.py            # DB engine, JWT config
│   ├── security.py          # Password hashing, JWT
│   ├── llm_service.py       # LLM integration
│   ├── thread_pool.py       # Thread pool manager
│   └── utils.py             # Utilities
├── models/
│   └── db_models.py         # SQLAlchemy models
├── frontend/                # Vue 3 SPA
│   └── src/
│       ├── views/           # LoginView, ChatView
│       ├── components/      # TurtleSoupGame, CatAvatar, SliderVerify
│       └── utils/api.js     # API client
├── static/avatars/          # User avatar uploads
└── scripts/                 # Startup scripts
```

---

## API Docs

After starting the backend, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Environment Variables

Create a `.env` file in the project root (optional):

```bash
# LLM mode: "local" (Ollama) or "external" (OpenAI-compatible API)
LLM_MODE=local

# For external API mode
LLM_API_KEY=your-api-key
LLM_API_URL=https://api.example.com/v1/chat/completions
LLM_API_MODEL=gpt-3.5-turbo

# Ollama config (for local mode)
OLLAMA_HOST=http://localhost:11434
```

---

## License

MIT

---

---

# 海龟汤游戏系统

基于 **FastAPI + Vue 3 + Qwen 3.5 (Ollama)** 的全栈海龟汤（情境猜谜）游戏，支持实时聊天。

## 功能

- 用户注册/登录（JWT 认证）
- 实时聊天室（WebSocket）
- 海龟汤游戏 — AI 主持人出题与判断
- 预设题库（无需 AI 即可游玩）
- LLM 不可用时自动降级
- 猫头像生成 + 滑块验证码

## 快速启动

### 1. 后端

```bash
pip install -r requirements.txt
python main.py        # 启动后端，端口 8000
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev           # 开发服务器 http://localhost:3000
```

### 3. 一键启动

```bash
# Windows
scripts/start_all.bat

# Linux / macOS
bash scripts/start_all.sh
```

浏览器打开 http://localhost:3000

## AI 功能（可选）

安装 [Ollama](https://ollama.ai) 启用 AI 出题与判断：

```bash
ollama serve
ollama pull qwen3.5:4b
```

不安装 AI 也可正常游戏，系统内置 3 道预设题目。

## API 文档

启动后端后访问：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 环境变量

在项目根目录创建 `.env` 文件（可选）：

```bash
LLM_MODE=local                          # local = Ollama, external = OpenAI兼容API
LLM_API_KEY=your-api-key                # 外部API模式需要
LLM_API_URL=https://api.example.com/v1/chat/completions
OLLAMA_HOST=http://localhost:11434
```

## 许可证

MIT
