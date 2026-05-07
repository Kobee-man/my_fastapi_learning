import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from core.config import create_db_and_tables
from api import auth, user, chat, turtle_soup
from fastapi.middleware.cors import CORSMiddleware
from core.thread_pool import tp_manager


def _llm_available() -> bool:
    mode = os.getenv("LLM_MODE", "external")
    if mode == "local":
        return True
    return bool(os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY"))

create_db_and_tables()


@asynccontextmanager
async def lifespan(app: FastAPI):
    tp_manager.init_pool(max_workers=10)
    yield
    tp_manager.shutdown()

app = FastAPI(
    title="Turtle Soup Game API",
    description="海龟汤游戏系统 - FastAPI + Vue 3 全栈应用",
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

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")


# ==================== 系统状态 ====================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "llm": "available" if _llm_available() else "not_configured"
    }

@app.get("/api/status")
async def system_status():
    return {
        "status": "online",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "llm_available": _llm_available(),
    }


# ==================== 注册路由器 ====================

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(chat.router)
app.include_router(turtle_soup.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
