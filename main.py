from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from core.database import init_db, engine, Base
from api import auth, user,chat
from fastapi.middleware.cors import CORSMiddleware
from core.thread_pool import tp_manager

init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    tp_manager.init_pool(max_workers=10)
    Base.metadata.create_all(engine)
    yield
    tp_manager.shutdown()

app = FastAPI(title="登录注册系统", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=FileResponse)
async def index_page():
    return "index_justtest.html"

@app.get("/chat.html", response_class=FileResponse)
async def chat_page():
    return "chat.html"

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(chat.router)