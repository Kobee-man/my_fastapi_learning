from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from typing import Dict, List, Set,Optional
from datetime import datetime
import logging
import uuid
import asyncio

from core.config import SECRET_KEY, ALGORITHM, get_db
from core.security import get_current_user
from models.db_models import User
from models.db_models import PublicChatMessage
from core.thread_pool import tp_manager
from sqlmodel import Session, select

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 管理活跃的WebSocket连接
class ConnectionManager:
    def __init__(self):
        # 存储用户连接: {user_id: {connection_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # 存储连接ID到用户ID的映射: {connection_id: user_id}
        self.connection_to_user: Dict[str, str] = {}

    async def connect(self, user_id: str, websocket: WebSocket, db: Session):
        # 生成唯一的连接ID
        connection_id = str(uuid.uuid4())
        await websocket.accept()
        
        # 初始化用户连接字典
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        
        # 添加连接
        self.active_connections[user_id][connection_id] = websocket
        self.connection_to_user[connection_id] = user_id
        
        logger.info(f"用户 {user_id} 通过连接 {connection_id} 连接到聊天室")
        
        # 从数据库加载历史消息
        history_messages = []
        try:
            # 查询最近50条消息
            statement = select(PublicChatMessage).order_by(PublicChatMessage.send_time.desc()).limit(50)
            messages: List[PublicChatMessage] = list(db.exec(statement).all())
            # 反转顺序，使最早的消息在前
            messages.reverse()
            
            # 转换为前端需要的格式
            for msg in messages:
                # 查询发送者信息
                user_statement = select(User).where(User.uid == msg.sender_uid)
                user = db.exec(user_statement).first()
                if user:
                    history_messages.append({
                        "type": "system" if msg.is_system else "message",
                        "content": msg.content,
                        "username": user.username,
                        "nickname": user.nickname or user.username,
                        "avatar_url": user.avatar_url,
                        "timestamp": msg.send_time.isoformat()
                    })
        except Exception as e:
            logger.error(f"加载历史消息失败: {e}")
        
        # 发送历史消息
        await websocket.send_json({
            "type": "history",
            "messages": history_messages,
            "timestamp": datetime.now().isoformat()
        })

    def disconnect(self, connection_id: str):
        if connection_id in self.connection_to_user:
            user_id = self.connection_to_user[connection_id]
            if user_id in self.active_connections:
                if connection_id in self.active_connections[user_id]:
                    del self.active_connections[user_id][connection_id]
                    # 如果用户的所有连接都断开了，清理用户入口
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
            del self.connection_to_user[connection_id]
            logger.info(f"连接 {connection_id} 断开，用户 {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id].values():
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"发送个人消息失败: {e}")

# 广播消息给所有在线用户
    async def broadcast(self, message: dict, db: Session, user_id: Optional[int] = None):
        logger.info(f"广播消息: {message['content'][:20]}...")

        def save_message_to_db():
            try:
                if user_id:
                    db_message = PublicChatMessage(
                        sender_uid=user_id,
                        content=message['content'],
                        is_system=False
                    )
                else:
                    db_message = PublicChatMessage(
                        sender_uid=1,
                        content=message['content'],
                        is_system=True
                    )
                db.add(db_message)
                db.commit()
                db.refresh(db_message)
            except Exception as e:
                logger.error(f"保存消息到数据库失败: {e}")
                db.rollback()

        tp_manager.submit(save_message_to_db)

        await self._broadcast_to_connections(message)

    async def _broadcast_to_connections(self, message: dict):
        disconnected_connections = []
        tasks = []
        for user_connections in self.active_connections.values():
            for connection_id, connection in user_connections.items():
                try:
                    task = asyncio.create_task(connection.send_json(message))
                    tasks.append((connection_id, task))
                except Exception as e:
                    logger.error(f"发送消息失败: {e}")
                    disconnected_connections.append(connection_id)

        for connection_id, task in tasks:
            try:
                await task
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                disconnected_connections.append(connection_id)

        for conn_id in disconnected_connections:
            self.disconnect(conn_id)

# 创建连接管理器实例
manager = ConnectionManager()

# 复用core/security中已有的get_current_user，避免重复造轮子
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@router.websocket("/ws/chat/{token}")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    user_id = None
    connection_id = None
    try:
        # 验证token并获取用户信息（复用已有的认证逻辑）
        credentials_exception = HTTPException(
            status_code=401,
            detail="无效的认证凭证"
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub") # type: ignore   
            if username is None:
                raise credentials_exception
        except JWTError:
            logger.error("JWT解码失败")
            raise credentials_exception
        
        # 使用正确的sqlmodel语法查询用户
        statement = select(User).where(User.username == username)
        user = db.exec(statement).first()
        if user is None:
            logger.error(f"用户 {username} 不存在")
            raise credentials_exception
            
        user_id = str(user.uid)
        
        # 建立连接
        await manager.connect(user_id, websocket, db)
        connection_id = None
        for cid, ws in manager.active_connections[user_id].items():
            if ws == websocket:
                connection_id = cid
                break

        if connection_id is None:
            logger.error(f"无法找到用户的连接ID: {user_id}")
            await websocket.close(code=1008, reason="无法找到连接")
            return

        # 广播用户上线消息
        await manager.broadcast({
            "type": "system",
            "content": f"{user.nickname or user.username} 加入了聊天室",
            "username": user.username,
            "nickname": user.nickname or user.username,
            "avatar_url": user.avatar_url,
            "timestamp": datetime.now().isoformat()
        }, db)
        
        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_json()
                
                # 构建消息体
                message = {
                    "type": "message",
                    "content": data.get("content"),
                    "username": user.username,
                    "nickname": user.nickname or user.username,
                    "avatar_url": user.avatar_url,
                    "timestamp": datetime.now().isoformat()
                }
                
                # 广播消息
                await manager.broadcast(message, db, user.uid)
                
        except WebSocketDisconnect:
            # 用户断开连接
            if connection_id:
                manager.disconnect(connection_id)
                await manager.broadcast({
                    "type": "system",
                    "content": f"{user.nickname or user.username} 离开了聊天室",
                    "username": user.username,
                    "nickname": user.nickname or user.username,
                    "timestamp": datetime.now().isoformat()
                }, db)
    except HTTPException as e:
        logger.error(f"WebSocket认证失败: {e.detail}")
        await websocket.close(code=1008, reason=f"认证失败: {e.detail}")
    except Exception as e:
        logger.error(f"WebSocket连接异常: {str(e)}")
        await websocket.close(code=1008, reason=str(e))

# 获取在线用户列表
@router.get("/chat/online-users", summary="获取在线用户列表")
async def get_online_users(
    current_user: User = Depends(get_current_user),  # 复用已有的认证依赖
    db: Session = Depends(get_db)
):
    online_users = []
    seen_user_ids = set()  # 防止重复添加同一用户
    
    for user_id_str in manager.connection_to_user.values():
        if user_id_str in seen_user_ids:
            continue
        seen_user_ids.add(user_id_str)
        
        try:
            # 将字符串转换为整数UID，然后查询用户
            user_id_int = int(user_id_str)
            statement = select(User).where(User.uid == user_id_int)
            user = db.exec(statement).first()
            if user:
                online_users.append({
                    "uid": user.uid,
                    "username": user.username,
                    "nickname": user.nickname or user.username,
                    "avatar_url": user.avatar_url
                })
        except ValueError:
            logger.warning(f"无效的用户ID: {user_id_str}")
        except Exception as e:
            logger.error(f"查询用户失败: {e}")
            
    return {
        "msg": "获取成功",
        "data": online_users
    }

# 获取聊天历史
@router.get("/chat/history", summary="获取聊天历史")
async def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 从数据库查询历史消息
        statement = select(PublicChatMessage).order_by(PublicChatMessage.send_time.desc()).limit(limit)
        messages: List[PublicChatMessage] = list(db.exec(statement).all())
        # 反转顺序，使最早的消息在前
        messages.reverse()
        
        # 转换为前端需要的格式
        history_messages = []
        for msg in messages:
            # 查询发送者信息
            user_statement = select(User).where(User.uid == msg.sender_uid)
            user = db.exec(user_statement).first()
            if user:
                history_messages.append({
                    "type": "system" if msg.is_system else "message",
                    "content": msg.content,
                    "username": user.username,
                    "nickname": user.nickname or user.username,
                    "avatar_url": user.avatar_url,
                    "timestamp": msg.send_time.isoformat()
                })
        
        return {
            "msg": "获取成功",
            "data": history_messages
        }
    except Exception as e:
        logger.error(f"获取聊天历史失败: {e}")
        return {
            "msg": "获取失败",
            "data": []
        }

# 添加调试路由
@router.get("/debug/ws-status", summary="调试WebSocket状态")
async def debug_ws_status():
    return {
        "active_users": len(manager.active_connections),
        "total_connections": len(manager.connection_to_user),
        "connection_mapping": manager.connection_to_user
    }