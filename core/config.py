# core/config.py - 统一数据库配置（SQLAlchemy）
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# -------------------------- MySQL 连接配置 --------------------------
DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/fastapi_chat?charset=utf8mb4"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=False  # 调试时可改为 True
)

# -------------------------- ORM 基类 --------------------------
Base = declarative_base()

# -------------------------- 其他配置 --------------------------
AVATAR_DIR = Path(__file__).parent.parent / "static" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# -------------------------- 数据库表创建/会话依赖 --------------------------
def create_db_and_tables():
    """创建所有表（首次运行执行）"""
    from models.db_models import User, PublicChatMessage, PrivateChatSession, PrivateChatMessage
    Base.metadata.create_all(bind=engine)

def get_db():
    """获取数据库会话（FastAPI依赖注入用）"""
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
