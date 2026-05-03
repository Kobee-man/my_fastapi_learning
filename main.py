from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from core.database import init_db, engine, Base
from api import auth, user, chat, turtle_soup
from fastapi.middleware.cors import CORSMiddleware
from core.thread_pool import tp_manager
from core.permissions import permission_manager

init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    tp_manager.init_pool(max_workers=10)
    Base.metadata.create_all(engine)
    yield
    tp_manager.shutdown()

app = FastAPI(
    title="FastAPI Vue 前端系统",
    description="""
    ## 🎯 系统功能概览
    
    ### 🔓 公开功能 (无需登录)
    - 访问登录/注册页面
    - 查看游戏规则说明
    - 查看系统状态信息
    
    ### 👤 认证用户功能 (需要登录)
    - 用户注册/登录/找回密码
    - 进入聊天室
    - 使用预设题库玩海龟汤游戏
    - 个人资料管理
    - 头像上传
    
    ### ⭐ 高级功能 (需要API Key)
    - LLM智能生成海龟汤题目
    - LLM智能判断问题答案
    - AI辅助推理（未来扩展）
    
    ---
    
    **权限说明：**
    - 所有基础功能在**无API Key情况下完全可用**
    - 高级AI功能会自动降级到预设方案
    - 系统始终保持稳定运行
    """,
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局权限信息中间件
@app.middleware("http")
async def add_permission_headers(request: Request, call_next):
    """
    为所有响应添加权限相关头信息
    帮助前端了解当前可用的功能
    """
    response = await call_next(request)
    
    # 添加权限级别头
    response.headers["X-API-Version"] = "2.0.0"
    response.headers["X-Features-Public"] = "true"
    response.headers["X-Features-Auth"] = "login,register,chat,preset_games"
    response.headers["X-Features-Premium"] = "llm_generation,llm_judgment" if permission_manager.features["llm_enabled"] else "none"
    response.headers["X-LLM-Available"] = str(permission_manager.features["llm_enabled"]).lower()
    
    return response


# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")


# ==================== 页面路由 ====================

@app.get("/", response_class=FileResponse)
async def index_page():
    """登录页面 - 公开访问"""
    return "login.html"

@app.get("/chat.html", response_class=FileResponse)
async def chat_page():
    """聊天页面 - 需要登录（由前端控制重定向）"""
    return "chat.html"


# ==================== 系统状态API ====================

@app.get("/api/status")
async def system_status():
    """
    获取系统状态和功能可用性
    **公开接口** - 无需任何验证
    """
    config = permission_manager.get_api_config()
    
    return {
        "status": "online",
        "version": "2.0.0",
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "features": {
            "public": {
                "access": True,
                "endpoints": ["/", "/chat.html", "/api/status", "/turtle-soup/rules"]
            },
            "authenticated": {
                "access": True,
                "requires_login": True,
                "endpoints": [
                    "/register",
                    "/login", 
                    "/forgot-password",
                    "/profile",
                    "/user/*",
                    "/ws/chat/*",
                    "/ws/private-chat/*",
                    "/turtle-soup/create-game",
                    "/turtle-soup/join-game",
                    "/turtle-soup/start-game",
                    "/turtle-soup/ask-question",
                    "/turtle-soup/submit-answer",
                    "/turtle-soup/hint",
                    "/turtle-soup/game-status/*",
                    "/turtle-soup/history",
                    "/chat/online-users"
                ]
            },
            "premium": {
                "access": config["llm_available"],
                "requires_api_key": True,
                "description": "LLM智能功能",
                "endpoints": [
                    "/turtle-soup/check-status",  # 检查LLM状态
                    # 以下端点内部会根据LLM可用性自动降级
                    "/turtle-soup/create-game",      # 创建时选择LLM或预设
                    "/turtle-soup/ask-question",     # 提问判断
                    "/turtle-soup/submit-answer"     # 答案判断
                ],
                "fallback_behavior": "当LLM不可用时，自动使用预设题目库和简单判断逻辑"
            }
        },
        "llm_config": {
            "available": config["llm_available"],
            "configured": config["api_key_configured"],
            "model": config["model"],
            "note": "即使LLM未配置，所有基础功能仍可正常使用" if not config["llm_available"] else "LLM已就绪，可使用全部功能"
        },
        "preset_puzzles": {
            "available": True,
            "count": 3,
            "difficulties": ["easy", "medium", "hard"],
            "note": "预设题目始终可用，无需API Key"
        },
        "permissions": {
            "public_endpoints_work_without_auth": True,
            "auth_endpoints_require_token": True,
            "premium_features_graceful_degradation": True,
            "system_stable_without_api_key": True
        }
    }


@app.get("/api/features")
async def features_list():
    """
    获取详细的功能列表和访问要求
    **公开接口**
    """
    return {
        "categories": [
            {
                "name": "用户认证",
                "level": "authenticated",
                "features": [
                    {"name": "注册", "endpoint": "/register", "method": "POST"},
                    {"name": "登录", "endpoint": "/login", "method": "POST"},
                    {"name": "找回密码", "endpoint": "/forgot-password", "method": "POST"}
                ]
            },
            {
                "name": "聊天功能",
                "level": "authenticated",
                "features": [
                    {"name": "公共聊天室", "endpoint": "/ws/chat/{token}", "type": "websocket"},
                    {"name": "私聊", "endpoint": "/ws/private-chat/{token}/{uid}", "type": "websocket"},
                    {"name": "在线用户列表", "endpoint": "/chat/online-users", "method": "GET"}
                ]
            },
            {
                "name": "个人中心",
                "level": "authenticated",
                "features": [
                    {"name": "查看资料", "endpoint": "/profile", "method": "GET"},
                    {"name": "修改昵称", "endpoint": "/user/nickname", "method": "PUT"},
                    {"name": "上传头像", "endpoint": "/user/avatar", "method": "POST"}
                ]
            },
            {
                "name": "海龟汤游戏 - 基础",
                "level": "authenticated",
                "note": "这些功能无需API Key即可使用",
                "features": [
                    {"name": "查看规则", "endpoint": "/turtle-soup/rules", "method": "GET"},
                    {"name": "使用预设题目", "endpoint": "/turtle-soup/create-game", "method": "POST", "params": {"use_preset": true}},
                    {"name": "加入游戏", "endpoint": "/turtle-soup/join-game", "method": "POST"},
                    {"name": "开始游戏", "endpoint": "/turtle-soup/start-game", "method": "POST"},
                    {"name": "提问（简单判断）", "endpoint": "/turtle-soup/ask-question", "method": "POST"},
                    {"name": "提交答案（简单判断）", "endpoint": "/turtle-soup/submit-answer", "method": "POST"},
                    {"name": "获取提示", "endpoint": "/turtle-soup/hint", "method": "GET"},
                    {"name": "历史记录", "endpoint": "/turtle-soup/history", "method": "GET"}
                ]
            },
            {
                "name": "海龟汤游戏 - AI增强",
                "level": "premium",
                "requires_api_key": True,
                "fallback": "自动降级到基础功能",
                "features": [
                    {"name": "LLM生成题目", "endpoint": "/turtle-soup/create-game", "method": "POST", "condition": "llm_available"},
                    {"name": "LLM智能判断", "endpoint": "/turtle-soup/ask-question", "method": "POST", "condition": "llm_available"},
                    {"name": "LLM答案评估", "endpoint": "/turtle-soup/submit-answer", "method": "POST", "condition": "llm_available"}
                ]
            }
        ],
        "important_notes": [
            "✅ 系统在无API Key状态下完全稳定运行",
            "✅ 用户认证、聊天、基础游戏功能不受影响",
            "⚠️ AI增强功能会优雅降级为预设方案",
            "🔒 API Key仅影响LLM调用，不影响其他功能"
        ]
    }


# ==================== 注册路由器 ====================

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(chat.router)
app.include_router(turtle_soup.router)


# ==================== 健康检查 ====================

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "FastAPI Vue Frontend",
        "version": "2.0.0",
        "database": "connected",
        "llm_status": "available" if permission_manager.features["llm_enabled"] else "not_configured"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
