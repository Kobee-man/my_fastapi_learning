"""
Redis服务模块 - 存储LLM生成的海龟汤题目背景

使用方式：
    from core.redis_service import redis_service

    redis_service.set_puzzle("game_abc", puzzle_dict)
    puzzle = redis_service.get_puzzle("game_abc")
    redis_service.delete_puzzle("game_abc")
"""

import json
import redis
from typing import Optional


# ==================== 配置 ====================

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
PUZZLE_EXPIRE_SECONDS = 7200  # 2小时过期


# ==================== 服务 ====================

class RedisService:
    """Redis服务，用于存储游戏题目数据"""

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True,
            )
        return self._client

    def is_available(self) -> bool:
        """检查Redis连接是否可用"""
        try:
            self.client.ping()
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            return False

    # ---- Puzzle CRUD ----

    def _puzzle_key(self, game_id: str) -> str:
        return f"turtle_soup:puzzle:{game_id}"

    def set_puzzle(self, game_id: str, puzzle: dict, expire: int = PUZZLE_EXPIRE_SECONDS) -> None:
        """存储题目到Redis"""
        self.client.set(self._puzzle_key(game_id), json.dumps(puzzle, ensure_ascii=False), ex=expire)

    def get_puzzle(self, game_id: str) -> Optional[dict]:
        """从Redis读取题目"""
        raw = self.client.get(self._puzzle_key(game_id))
        if raw is None:
            return None
        return json.loads(raw)

    def delete_puzzle(self, game_id: str) -> None:
        """删除Redis中的题目"""
        self.client.delete(self._puzzle_key(game_id))

    # ---- 对话历史 ----

    def _history_key(self, game_id: str) -> str:
        return f"turtle_soup:history:{game_id}"

    def append_history(self, game_id: str, question: str, answer: str, reason: str = "") -> None:
        """追加一条问答记录到Redis"""
        entry = json.dumps({"q": question, "a": answer, "r": reason}, ensure_ascii=False)
        key = self._history_key(game_id)
        self.client.rpush(key, entry)
        self.client.expire(key, PUZZLE_EXPIRE_SECONDS)

    def get_history(self, game_id: str, limit: int = 10) -> list:
        """获取最近N条问答记录"""
        key = self._history_key(game_id)
        raw_list = self.client.lrange(key, -limit, -1)
        return [json.loads(item) for item in raw_list]

    def delete_history(self, game_id: str) -> None:
        """删除问答历史"""
        self.client.delete(self._history_key(game_id))


# ==================== 全局实例 ====================

redis_service = RedisService()
