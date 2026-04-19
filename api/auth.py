from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import Session,select
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

# 注册
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

# 登录
@router.post("/login", summary="登录获取 Token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}