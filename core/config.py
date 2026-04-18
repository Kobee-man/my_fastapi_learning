# core/config.py 完整修改后代码
from sqlmodel import SQLModel, create_engine
from pathlib import Path

# -------------------------- 核心修改：MySQL 连接配置 --------------------------
# 格式：mysql+pymysql://用户名:密码@主机:端口/数据库名（需先在MySQL手动创建该数据库）
# 示例：root:123456@localhost:3306/my_fastapi_db
DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/fastapi_chat"
# MySQL 无需 check_same_thread，直接创建引擎
engine = create_engine(
    DATABASE_URL,
    # 可选：开启日志便于调试SQL
    echo=True  # 生产环境建议关闭
)

# -------------------------- 其他配置（头像/JWT等，保留不变） --------------------------
# 头像保存路径
AVATAR_DIR = Path(__file__).parent.parent / "static" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

# 上传文件配置
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# JWT 配置（示例，根据你的实际情况调整）
SECRET_KEY = "your-secret-key-here"  # 建议替换为随机生成的密钥
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# -------------------------- 数据库表创建/会话依赖 --------------------------
def create_db_and_tables():
    """创建MySQL表（首次运行执行）"""
    SQLModel.metadata.create_all(engine)

def get_db():
    """获取数据库会话（FastAPI依赖注入用）"""
    from sqlmodel import Session
    with Session(engine) as session:
        try:
            yield session
            # 关键：自动提交事务（避免数据只在内存中，未写入MySQL）
            session.commit()
        except Exception as e:
            # 出错时回滚
            session.rollback()
            raise e
        finally:
            session.close()