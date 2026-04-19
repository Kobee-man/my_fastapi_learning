# models/db_models.py
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from core.database import Base  # 改为从core.database导入Base

# 用户表
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(10), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    nickname = Column(String(50), default="")
    avatar_url = Column(String(255), default="")
    created_at = Column(TIMESTAMP, default=datetime.now, nullable=False)
    last_login_at = Column(TIMESTAMP, nullable=True)
    is_online = Column(Boolean, default=False, nullable=False)

# 公共聊天消息表
class PublicChatMessage(Base):
    __tablename__ = "public_chat_messages"

    msg_id = Column(Integer, primary_key=True, autoincrement=True)
    sender_uid = Column(String(10), ForeignKey("users.uid"), nullable=False)
    content = Column(Text, nullable=False)
    send_time = Column(TIMESTAMP, default=datetime.now, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)

# 私聊会话表
class PrivateChatSession(Base):
    __tablename__ = "private_chat_sessions"

    session_id = Column(Integer, primary_key=True, autoincrement=True)
    user1_uid = Column(String(10), ForeignKey("users.uid"), nullable=False)
    user2_uid = Column(String(10), ForeignKey("users.uid"), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now, nullable=False)

    __table_args__ = (UniqueConstraint("user1_uid", "user2_uid", name="unique_user_pair"),)

# 私聊消息表
class PrivateChatMessage(Base):
    __tablename__ = "private_chat_messages"

    msg_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("private_chat_sessions.session_id"), nullable=False)
    sender_uid = Column(String(10), ForeignKey("users.uid"), nullable=False)
    receiver_uid = Column(String(10), ForeignKey("users.uid"), nullable=False)
    content = Column(Text, nullable=False)
    send_time = Column(TIMESTAMP, default=datetime.now, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)