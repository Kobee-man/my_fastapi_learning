"""
权限管理系统 - 实现三级权限分层：
1. Public (公开) - 无需任何验证
2. Authenticated (已认证) - 需要JWT Token
3. Premium (高级) - 需要API Key (用于LLM等功能)
"""

from fastapi import HTTPException, Depends, Request, Header
from typing import Optional
from functools import wraps
import os


class PermissionLevel:
    """权限级别常量"""
    PUBLIC = "public"           # 公开访问，无需验证
    AUTHENTICATED = "auth"     # 已认证（需要Token）
    PREMIUM = "premium"        # 高级功能（需要API Key）
    ADMIN = "admin"            # 管理员（预留）


class PermissionManager:
    """权限管理器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # API Key配置
        self.api_key_env_var = "OPENAI_API_KEY"
        self.api_url_env_var = "OPENAI_API_URL"
        self.api_model_env_var = "OPENAI_MODEL"
        
        # 功能开关
        self.features = {
            "llm_enabled": self._check_llm_available(),
            "preset_puzzles": True,  # 预设题目始终可用
            "registration": True,  # 注册功能
            "chat": True,          # 聊天功能
            "profile_edit": True,  # 资料编辑
            "avatar_upload": True, # 头像上传
        }
        
        print(f"[PermissionManager] 初始化完成")
        print(f"  - LLM功能: {'[OK]' if self.features['llm_enabled'] else '[X] 未配置'}")
        print(f"  - 预设题目: {'[OK]' if self.features['preset_puzzles'] else '[X] 禁用'}")
    
    def _check_llm_available(self) -> bool:
        """检查LLM API是否可用"""
        api_key = os.getenv(self.api_key_env_var)
        return bool(api_key and len(api_key) > 10)
    
    def get_api_config(self) -> dict:
        """获取API配置（不暴露密钥）"""
        return {
            "llm_available": self.features["llm_enabled"],
            "api_key_configured": bool(os.getenv(self.api_key_env_var)),
            "api_url": os.getenv(self.api_url_env_var, ""),
            "model": os.getenv(self.api_model_env_var, "gpt-3.5-turbo"),
            "features": self.features
        }
    
    def require_permission(self, level: str):
        """
        权限装饰器工厂
        
        用法:
            @router.get("/endpoint")
            @permission_manager.require_permission(PermissionLevel.AUTHENTICATED)
            async def endpoint():
                ...
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request = None
                
                # 从参数中提取request对象
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if not request:
                    # 尝试从kwargs中查找
                    request = kwargs.get('request')
                
                # 根据权限级别进行验证
                if level == PermissionLevel.PUBLIC:
                    # 公开接口，无需验证
                    pass
                    
                elif level == PermissionLevel.AUTHENTICATED:
                    # 需要JWT Token验证
                    token = self._extract_token(request)
                    if not token:
                        raise HTTPException(
                            status_code=401,
                            detail="需要登录才能访问此功能",
                            headers={"WWW-Authenticate": "Bearer"}
                        )
                    
                    # 可以在这里添加Token验证逻辑
                    # 当前简化处理，实际应调用security模块
                    
                elif level == PermissionLevel.PREMIUM:
                    # 首先需要是已认证用户
                    token = self._extract_token(request)
                    if not token:
                        raise HTTPException(
                            status_code=401,
                            detail="需要登录才能使用此功能",
                            headers={"WWW-Authenticate": "Bearer"}
                        )
                    
                    # 然后检查API Key是否可用
                    if not self.features["llm_enabled"]:
                        raise HTTPException(
                            status_code=503,
                            detail="此功能需要API Key支持 - 请联系管理员配置或使用预设功能",
                            headers={
                                "X-Premium-Required": "true",
                                "X-Fallback-Available": "preset_puzzles"
                            }
                        )
                
                elif level == PermissionLevel.ADMIN:
                    # 管理员权限（预留）
                    raise HTTPException(status_code=501, detail="管理员功能尚未实现")
                
                # 执行原函数
                result = await func(*args, **kwargs)
                
                # 在响应中添加权限信息头
                if hasattr(result, 'headers'):
                    result.headers["X-Permission-Level"] = level
                    result.headers["X-Features"] = ",".join([
                        k for k, v in self.features.items() if v
                    ])
                
                return result
            
            return wrapper
        return decorator
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """从请求中提取JWT Token"""
        if not request:
            return None
            
        auth_header = request.headers.get("authorization", "")
        
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        
        # 也尝试从query参数获取（仅用于开发环境）
        token = request.query_params.get("token")
        if token:
            return token
        
        return None
    
    def check_feature_access(self, feature_name: str) -> dict:
        """
        检查特定功能的访问权限
        
        返回:
        {
            "accessible": bool,
            "reason": str,
            "fallback": Optional[str]
        }
        """
        feature_map = {
            "llm_generation": {
                "requires": "premium",
                "check": lambda: self.features["llm_enabled"],
                "error": "LLM服务未配置 - 将使用预设题目库",
                "fallback": "preset_puzzles"
            },
            "llm_judgment": {
                "requires": "premium",
                "check": lambda: self.features["llm_enabled"],
                "error": "LLM判断不可用 - 将使用简单逻辑判断",
                "fallback": "simple_judgment"
            },
            "preset_puzzles": {
                "requires": "public",
                "check": lambda: self.features["preset_puzzles"],
                "error": "预设题目功能不可用",
                "fallback": None
            },
            "user_registration": {
                "requires": "public",
                "check": lambda: self.features["registration"],
                "error": "注册功能已禁用",
                "fallback": None
            },
            "chat_room": {
                "requires": "authenticated",
                "check": lambda: self.features["chat"],
                "error": "聊天功能不可用",
                "fallback": None
            }
        }
        
        config = feature_map.get(feature_name, {
            "requires": "unknown",
            "check": lambda: False,
            "error": "未知功能",
            "fallback": None
        })
        
        accessible = config["check"]()
        
        return {
            "accessible": accessible,
            "requires": config["requires"],
            "reason": "" if accessible else config["error"],
            "fallback": config["fallback"] if not accessible else None,
            "feature": feature_name
        }


# 全局单例实例
permission_manager = PermissionManager()


# 便捷装饰器
def public_endpoint(func):
    """标记为公开接口的装饰器"""
    return permission_manager.require_permission(PermissionLevel.PUBLIC)(func)

def authenticated_endpoint(func):
    """标记为需认证接口的装饰器"""
    return permission_manager.require_permission(PermissionLevel.AUTHENTICATED)(func)

def premium_endpoint(func):
    """标记为高级功能接口的装饰器"""
    return permission_manager.require_permission(PermissionLevel.PREMIUM)(func)


# FastAPI依赖注入函数
async def get_current_user_optional(request: Request):
    """
    获取当前用户（可选）
    如果未登录返回None，不会抛出异常
    """
    token = permission_manager._extract_token(request)
    
    if not token:
        return None
    
    try:
        from core.security import decode_access_token
        payload = decode_access_token(token)
        return {"username": payload.get("sub"), "token": token}
    except Exception:
        return None


async def get_current_user_required(request: Request):
    """
    获取当前用户（必须登录）
    未登录会抛出401异常
    """
    user = await get_current_user_optional(request)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def check_premium_feature(feature_name: str = "default"):
    """
    检查高级功能是否可用（依赖注入用）
    
    用法:
        @router.post("/some-endpoint")
        async def endpoint(premium_check: dict = Depends(check_premium_feature("llm"))):
            if not premium_check["accessible"]:
                # 使用降级方案
                ...
    """
    check_result = permission_manager.check_feature_access(feature_name)
    
    if not check_result["accessible"]:
        # 返回包含错误信息的dict，让调用者决定如何处理
        return check_result
    
    return {"accessible": True, "feature": feature_name}
