from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import Response
from pydantic import BaseModel, field_validator
from sqlmodel import Session, select
from typing import Optional

from core.config import get_db
from core.security import get_password_hash, verify_password, create_access_token
from core.utils import generate_10digit_numeric_uid
from models.db_models import User

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    password: str
    nickname: Optional[str] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v or len(v) < 3 or len(v) > 20:
            raise ValueError('用户名长度3-20位')
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError('密码至少6位')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class ForgotPasswordRequest(BaseModel):
    username: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError('新密码至少6位')
        return v

@router.post("/register", summary="用户注册")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.exec(select(User).where(User.username == user.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    hashed_pw = get_password_hash(user.password)
    new_uid = generate_10digit_numeric_uid(db)
    db_user = User(
        uid=new_uid,
        username=user.username,
        nickname=user.nickname,
        password=hashed_pw
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"msg": "注册成功", "username": user.username}

@router.post("/login", summary="登录获取 Token")
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.exec(select(User).where(User.username == login_data.username)).first()
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token = create_access_token(data={"sub": login_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password", summary="忘记密码-重置密码")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.exec(select(User).where(User.username == req.username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.password = get_password_hash(req.new_password)
    db.add(user)
    db.commit()
    return {"msg": "密码重置成功，请使用新密码登录"}
