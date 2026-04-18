from sqlmodel import Field,SQLModel
from typing import Optional
import uuid
from uuid import UUID

#定义数据库表
class User(SQLModel,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)
    uid:UUID=Field(default_factory=uuid.uuid4,unique=True,index=True,nullable=False)
    username:str=Field(unique=True,index=True)
    nickname:Optional[str]=Field(default=None)
    hashed_password:str
    avatar_url:Optional[str]=Field(default=None)