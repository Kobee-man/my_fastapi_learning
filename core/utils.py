import random
from sqlalchemy.orm import Session
from models.db_models import User

def generate_10digit_numeric_uid(db: Session, max_retry: int = 10) -> str:
    """
    生成 10位纯数字唯一UID（字符串类型）
    :param db: 数据库会话
    :param max_retry: 最大重试次数，防止死循环
    :return: 10位纯数字字符串，如 "1234567890"
    """
    retry = 0
    while retry < max_retry:
        # 生成10位纯数字字符串（核心修改）
        uid = ''.join(random.choice('0123456789') for _ in range(10))
        # 校验数据库是否重复
        exists = db.query(User).filter(User.uid == uid).first()
        if not exists:
            return uid
        retry += 1
    # 重试耗尽，抛出异常（极端情况才会触发）
    raise RuntimeError("10位纯数字UID生成失败：重试次数上限")