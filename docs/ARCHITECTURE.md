# 🏗️ 项目架构设计文档

**项目名称**: 海龟汤游戏系统 (Turtle Soup Game System)  
**版本**: v2.0  
**最后更新**: 2026-05-03

---

## 一、系统概述

本项目是一个基于 **FastAPI + Vue 3 + 本地LLM(Qwen)** 的全栈Web应用，实现海龟汤（情境猜谜）在线游戏功能。

### 核心特性
- ✅ 三层权限架构（公开 → 认证 → 高级AI）
- ✅ 完全本地化运行，支持Ollama + Qwen 3.5
- ✅ 实时WebSocket聊天室
- ✅ 响应式Vue 3前端界面

---

## 二、目录结构说明

```
d:\my_fastapi/
│
├── 📄 main.py                    # FastAPI应用入口点
├── 📄 requirements.txt           # Python依赖清单
├── 📄 .gitignore                 # Git忽略规则
├── 📄 README.md                  # 项目主文档（精简版）
│
├── 📁 api/                       # 【后端】API路由层
│   ├── __init__.py               # 包初始化 & 路由注册
│   ├── auth.py                   # 认证接口（登录/注册/JWT）
│   ├── chat.py                   # 聊天接口（WebSocket/消息）
│   ├── turtle_soup.py            # 游戏接口（海龟汤核心逻辑）
│   └── user.py                   # 用户接口（资料/头像）
│
├── 📁 core/                      # 【后端】核心业务层
│   ├── config.py                 # 配置管理（数据库/JWT/文件上传）
│   ├── database.py               # 数据库连接与会话管理
│   ├── permissions.py            # 权限系统（三层架构核心）
│   ├── security.py               # 安全模块（密码哈希/Token生成）
│   ├── thread_pool.py            # 线程池管理器
│   └── utils.py                  # 通用工具函数
│
├── 📁 models/                    # 【后端】数据模型层
│   ├── db_models.py              # SQLModel数据库模型定义
│   └── user.py                   # 用户模型扩展
│
├── 📁 frontend/                  # 【前端】Vue 3应用
│   ├── src/
│   │   ├── main.js               # 应用入口
│   │   ├── App.vue               # 根组件
│   │   ├── views/                # 页面视图
│   │   │   ├── LoginView.vue     # 登录/注册页
│   │   │   └── ChatView.vue      # 聊天/游戏主页
│   │   ├── components/           # 可复用组件
│   │   │   ├── CatAvatar.vue    # 猫咪头像（眼睛跟踪+动画）
│   │   │   ├── SliderVerify.vue # 滑块验证组件
│   │   │   └── TurtleSoupGame.vue # 海龟汤游戏主组件
│   │   ├── composables/          # 组合式函数
│   │   │   └── useEyeTracking.js # 眼睛跟踪逻辑
│   │   ├── router/               # 路由配置
│   │   │   └── index.js
│   │   └── utils/                # 工具函数
│   │       └── api.js            # API封装（含权限感知）
│   ├── package.json              # 前端依赖配置
│   ├── vite.config.js            # Vite构建配置（代理设置）
│   └── vitest.config.js          # 测试框架配置
│
├── 📁 cli/                       # 【工具】命令行工具
│   └── turtle_soup.py            # 海龟汤CLI客户端（Qwen优化版）
│
├── 📁 tests/                     # 【测试】集成测试
│   └── test_qwen_integration.py  # Qwen模型集成测试套件
│
├── 📁 docs/                      # 【文档】详细文档库
│   ├── QWEN_INTEGRATION_GUIDE.md     # Qwen集成详细指南
│   └── TURTLE_SOUP_OLLAMA_GUIDE.md  # Ollama使用手册
│
├── 📁 scripts/                   # 【脚本】运维脚本
│   ├── start_all.bat             # Windows一键启动
│   ├── start_all.sh              # Linux/macOS一键启动
│   ├── check_status.bat          # Windows服务状态检查
│   ├── check_status.sh           # Linux服务状态检查
│   └── start_server.py           # 生产环境启动脚本
│
├── 📁 legacy/                    # 【归档】历史版本（已废弃）
│   ├── login.html                # 旧版独立HTML登录页
│   ├── chat.html                 # 旧版独立HTML聊天页
│   └── turtle_soup_ollama_legacy.py  # 旧版CLI工具（通用版）
│
└── 📁 static/                    # 【资源】静态文件
    └── avatars/                 # 用户上传的头像
```

---

## 三、模块依赖关系图

### 3.1 后端依赖层次

```
┌─────────────────────────────────────────────┐
│                main.py                       │
│            (FastAPI Application)             │
└─────────────────────┬───────────────────────┘
                      │ imports
                      ▼
┌─────────────────────────────────────────────┐
│              api/ (路由层)                     │
│  ┌─────────┬─────────┬─────────┬──────────┐  │
│  │ auth.py │ chat.py │turtle_  │ user.py  │  │
│  │         │         │soup.py  │          │  │
│  └────┬────┴────┬────┴────┬────┴────┬─────┘  │
└───────┼─────────┼─────────┼─────────┼────────┘
        │         │         │         │
        ▼         ▼         ▼         ▼
┌─────────────────────────────────────────────┐
│            core/ (核心层)                     │
│  ┌──────────┬──────────┬──────────────────┐  │
│  │permissions│ security │ config/database │  │
│  │   .py    │   .py    │      .py         │  │
│  └──────────┴──────────┴──────────────────┘  │
└─────────────────────┬───────────────────────┘
                      │ uses
                      ▼
┌─────────────────────────────────────────────┐
│           models/ (数据层)                   │
│       db_models.py / user.py                │
└─────────────────────────────────────────────┘
```

### 3.2 前端依赖关系

```
┌─────────────────────────────────────────────┐
│               main.js                        │
│            (应用入口)                        │
└─────────────────────┬───────────────────────┘
                      │ mounts
                      ▼
┌─────────────────────────────────────────────┐
│               App.vue                        │
│            (根组件)                          │
└─────────────────────┬───────────────────────┘
                      │ renders
                      ▼
┌─────────────────────────────────────────────┐
│           router/ (路由)                     │
│         LoginView / ChatView                │
└─────────────────────┬───────────────────────┘
                      │ uses components
                      ▼
┌─────────────────────────────────────────────┐
│        components/ (可复用组件)               │
│  CatAvatar / SliderVerify / TurtleSoupGame  │
└─────────────────────┬───────────────────────┘
                      │ uses composables
                      ▼
┌─────────────────────────────────────────────┐
│       composables/ (组合函数)                │
│          useEyeTracking.js                  │
└─────────────────────┬───────────────────────┘
                      │ calls API
                      ▼
┌─────────────────────────────────────────────┐
│         utils/api.js (API封装)               │
│     权限感知 · 缓存 · 错误处理              │
└─────────────────────┬───────────────────────┘
                      │ HTTP requests
                      ▼
┌─────────────────────────────────────────────┐
│         Backend API (FastAPI :8000)          │
└─────────────────────────────────────────────┘
```

### 3.3 全栈数据流

```
用户浏览器
    │
    ▼ HTTP/WebSocket
┌──────────────┐
│ Frontend     │  Vue 3 + Vite (:3000)
│ (SPA)        │
└──────┬───────┘
       │ REST API / WebSocket
       ▼
┌──────────────┐
│ FastAPI      │  Python + Uvicorn (:8000)
│ Backend      │
└──────┬───────┘
       │
       ├─→ api/auth.py ──→ JWT认证
       ├─→ api/chat.py ──→ WebSocket管理
       ├─→ api/turtle_soup.py → 游戏逻辑
       └─→ api/user.py ──→ 用户CRUD
              │
              ▼
       ┌──────────────┐
       │ core/        │  业务逻辑层
       │ permissions  │  权限控制
       │ security     │  Token验证
       │ database     │  MySQL/SQLite
       └──────┬───────┘
              │ (可选)
              ▼
       ┌──────────────┐
       │ Ollama/Qwen  │  AI服务 (:11434)
       │ LLM          │  题目生成/问题判断
       └──────────────┘
```

---

## 四、关键模块说明

### 4.1 权限系统 (core/permissions.py)

**三层权限架构**：

| 层级 | 名称 | 访问条件 | 功能范围 |
|------|------|---------|---------|
| Level 1 | PUBLIC | 无需认证 | 系统状态、API文档 |
| Level 2 | AUTHENTICATED | JWT Token | 登录/聊天/预设游戏 |
| Level 3 | PREMIUM | Token + API Key/LLM | AI题目生成、智能判断 |

**核心类**：
```python
class PermissionManager:
    """单例模式 - 全局权限管理"""
    
    def require_permission(level):  # 装饰器工厂
    def check_feature_access(feature):  # 特性检查
    def get_current_user_optional(request):  # 可选用户获取
```

### 4.2 API路由层 (api/)

**接口清单**：

| 模块 | 前缀 | 核心方法 |
|------|------|---------|
| auth | `/register`, `/login` | 用户认证 |
| chat | `/ws/chat`, `/ws/private-chat` | 实时通讯 |
| turtle_soup | `/turtle-soup/*` | 15个游戏接口 |
| user | `/user/*` | 个人中心 |

**中间件**：
- CORS跨域支持
- 权限头注入 (`X-API-Version`, `X-Features-*`, `X-LLM-Available`)
- 请求日志记录

### 4.3 前端组件架构

**视图层 (views/)**：
- `LoginView.vue`: 登录/注册/找回密码
- `ChatView.vue`: 聊天室 + 海龟汤入口

**组件层 (components/)**：
- `CatAvatar.vue`: SVG猫咪 + 眼睛跟踪 + 动画
- `SliderVerify.vue`: 拖拽滑块验证
- `TurtleSoupGame.vue`: 完整游戏流程（1100+行）

**工具层 (utils/)**：
- `api.js`: 封装所有后端调用，包含：
  - 状态缓存（5分钟TTL）
  - 权限检查
  - 错误处理与降级
  - 自动重试

---

## 五、技术栈详情

### 后端技术栈

| 技术 | 版本 | 用途 | 许可证 |
|------|------|------|--------|
| Python | 3.10+ | 主要语言 | PSF |
| FastAPI | 0.100+ | Web框架 | MIT |
| Uvicorn | 0.23+ | ASGI服务器 | BSD |
| SQLModel | 0.0.8+ | ORM | MIT |
| Pydantic | 2.0+ | 数据验证 | MIT |
| python-jose | 3.3+ | JWT处理 | MIT |
| passlib | 1.7+ | 密码哈希 | BSD |

### 前端技术栈

| 技术 | 版本 | 用途 | 许可证 |
|------|------|------|--------|
| Vue | 3.4+ | UI框架 | MIT |
| Vite | 5.2+ | 构建工具 | MIT |
| Vue Router | 4.3+ | 路由 | MIT |
| Pinia | 2.1+ | 状态管理 | MIT |
| Axios | 1.6+ | HTTP客户端 | MIT |

### AI服务（可选）

| 技术 | 版本 | 用途 | 说明 |
|------|------|------|------|
| Ollama | 最新 | LLM运行时 | 本地推理 |
| Qwen | 3.5:4b | 大语言模型 | 中文优化 |

---

## 六、配置管理

### 6.1 后端配置 (core/config.py)

```python
# 数据库连接
DATABASE_URL = "mysql+pymysql://..."

# JWT配置
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 文件上传
AVATAR_DIR = Path("static/avatars")
ALLOWED_EXTENSIONS = {".jpg", ".png"}
MAX_FILE_SIZE = 5MB
```

### 6.2 前端配置 (frontend/vite.config.js)

```javascript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://127.0.0.1:8000',  // 后端代理
      '/ws': 'ws://127.0.0.1:8000'     // WebSocket代理
    }
  },
  plugins: [vue()]
})
```

### 6.3 环境变量 (.env)

```bash
# 应用端口
PORT=8000

# 数据库
DATABASE_URL=mysql+pymysql://...

# JWT密钥
SECRET_KEY=change-me-in-production

# AI服务（可选）
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3.5:4b
OPENAI_API_KEY=sk-...  # 或使用本地LLM
```

---

## 七、部署架构

### 开发环境

```
用户 → localhost:3000 (Vite Dev Server)
              ↓ proxy
        localhost:8000 (FastAPI + Uvicorn)
              ↓ (可选)
        localhost:11434 (Ollama)
```

### 生产环境

```
用户 → Nginx (:80/:443)
       ↓ 反向代理
   ┌─────────────────────┐
   │ Frontend (dist/)    │  静态资源
   │ Backend (FastAPI)   │  API服务
   └─────────────────────┘
       ↓
   MySQL / SQLite        # 数据持久化
   Ollama (可选)         # AI推理
```

**Nginx 配置示例**：
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://127.0.0.1:8000;
    }
    
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 八、扩展指南

### 8.1 添加新的API模块

1. 在 `api/` 创建新文件 `new_module.py`
2. 定义 `APIRouter()` 和路由函数
3. 在 `api/__init__.py` 注册路由
4. 更新权限装饰器（如需要）

**示例**：
```python
# api/new_module.py
from fastapi import APIRouter

router = APIRouter(prefix="/new-module", tags=["新模块"])

@router.get("/endpoint")
async def new_endpoint():
    return {"message": "Hello"}
```

### 8.2 添加新的Vue页面

1. 在 `src/views/` 创建 `NewPage.vue`
2. 在 `src/router/index.js` 添加路由
3. 在导航组件添加链接

### 8.3 集成新的AI模型

1. 安装模型：`ollama pull new-model`
2. 修改 `cli/turtle_soup.py` 的默认配置
3. 测试兼容性：`python tests/test_qwen_integration.py`

---

## 九、性能优化建议

### 后端优化

- ✅ 使用 `uvloop` 替代默认事件循环
- ✅ 启用数据库连接池
- ✅ 使用 Redis缓存会话（生产环境）
- ✅ Gzip压缩响应

### 前端优化

- ✅ 组件懒加载（路由级代码分割）
- ✅ 图片懒加载与CDN
- ✅ 启用 Vite 构建优化（tree-shaking, minification）
- ✅ PWA 支持（离线访问）

---

## 十、维护指南

### 日常维护任务

| 任务 | 频率 | 命令/操作 |
|------|------|----------|
| 依赖更新 | 月度 | `pip update`, `npm update` |
| 安全扫描 | 月度 | `pip audit`, `npm audit` |
| 数据库备份 | 每日 | 导出 `.db` 或 MySQL dump |
| 日志清理 | 每周 | 清理 `logs/` 目录 |
| 测试执行 | 提交前 | `pytest`, `npm test` |

### 故障排查

**常见问题及解决方案**详见 [README.md](./README.md) 的"常见问题"章节。

---

**文档维护者**: AI Assistant  
**最后审核**: 2026-05-03  
**适用版本**: v2.0+
