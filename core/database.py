# core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# ========== MySQL连接配置 ==========
# 配置说明：mysql+pymysql://用户名:密码@主机:端口/数据库名?参数
MYSQL_USER = "root"          # 你的MySQL用户名（默认root）
MYSQL_PASSWORD = "123456"    # 你的MySQL密码
MYSQL_HOST = "localhost"     # 主机（本地填localhost，远程填IP）
MYSQL_PORT = 3306            # 你的MySQL端口
MYSQL_DB = "fastapi_chat"    # 第一步创建的数据库名

# 拼接MySQL连接URL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"

# ========== 创建引擎（适配MySQL） ==========
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # MySQL连接池配置（可选，优化性能）
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,  # 1小时回收连接，避免超时
    echo=False  # 关闭SQL日志（调试时可设为True）
)

# ========== 测试库配置（可选，保持和主库一致） ==========
TEST_MYSQL_DB = "fastapi_chat_test"  # 测试数据库（需提前创建）
TEST_SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{TEST_MYSQL_DB}?charset=utf8mb4"
test_engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
    echo=False
)

# ========== 创建数据库会话 ==========
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# ========== 基础ORM模型类 ==========
Base = declarative_base()

# ========== 初始化数据库（创建所有表） ==========
def init_db():
    # 导入所有模型（确保模型被加载，否则不会创建表）
    from models.db_models import User, PublicChatMessage, PrivateChatSession, PrivateChatMessage
    Base.metadata.create_all(bind=engine)

def init_test_db():
    from models.db_models import User, PublicChatMessage, PrivateChatSession, PrivateChatMessage
    Base.metadata.create_all(bind=test_engine)