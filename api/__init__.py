"""
API路由包初始化
包含所有业务模块的路由
"""

from . import auth
from . import user
from . import chat
from . import turtle_soup

__all__ = ["auth", "user", "chat", "turtle_soup"]
