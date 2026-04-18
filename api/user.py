from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import Optional

from core.config import get_db, ALLOWED_EXTENSIONS, MAX_FILE_SIZE, AVATAR_DIR
from core.security import get_current_user
from models.db_models import User

router = APIRouter()

class UserUpdate(BaseModel):
    nickname: Optional[str] = None

# 获取个人信息
@router.get("/profile", summary="当前登录用户信息")
def profile(current_user: User = Depends(get_current_user)):
    return {
        "msg": "获取成功",
        "data": {
            "uid": current_user.uid,
            "username": current_user.username,
            "nickname": current_user.nickname or current_user.username,
            "avatar_url": current_user.avatar_url,
            "avatar_access_url": f"http://127.0.0.1:8000{current_user.avatar_url}" if current_user.avatar_url else None
        }
    }

# 修改昵称
@router.put("/user/nickname", summary="修改用户昵称")
def update_nickname(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user_update.nickname:
        raise HTTPException(status_code=400, detail="昵称不能为空")
    
    # 从当前Session重新查询用户
    db_user = db.exec(select(User).where(User.uid == current_user.uid)).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    db_user.nickname = user_update.nickname
    db.commit()
    db.refresh(db_user)
    return {"msg": "昵称修改成功", "data": {"nickname": db_user.nickname}}


# 上传头像
def allowed_file(filename: str | None) -> bool:
    if not filename:
        return False
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@router.post("/user/avatar", summary="上传用户头像")
def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    if not allowed_file(filename):
        raise HTTPException(status_code=400, detail="仅支持jpg/jpeg/png/gif格式的图片")
    
    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过限制（最大10MB）")
    
    #从当前session重新查询用户实例
    db_user = db.exec(select(User).where(User.uid==current_user.uid)).first()
    if not db_user:
        raise HTTPException(status_code=404,detail="用户不存在")
    
    file_ext = filename.rsplit(".", 1)[1].lower()
    save_filename = f"{current_user.uid}.{file_ext}"
    file_path = AVATAR_DIR / save_filename

    with open(file_path, "wb") as f:
        f.write(contents)

    db_user.avatar_url = f"/static/avatars/{save_filename}"
    db.commit()
    db.refresh(db_user)

    return {
        "msg": "头像上传成功",
        "avatar_url": current_user.avatar_url,
        "access_url": f"http://127.0.0.1:8000{current_user.avatar_url}"
    }