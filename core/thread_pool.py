# core/thread_pool.py
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ThreadPoolManager:
    _instance: Optional['ThreadPoolManager'] = None
    _executor: Optional[ThreadPoolExecutor] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init_pool(self, max_workers: int = 10):
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=max_workers)
            logger.info(f"线程池已创建，最大工作线程数: {max_workers}")

    def submit(self, fn, *args, **kwargs):
        if self._executor is None:
            self.init_pool()
        future = self._executor.submit(fn, *args, **kwargs)
        return future

    def shutdown(self, wait: bool = True):
        if self._executor is not None:
            self._executor.shutdown(wait=wait)
            self._executor = None
            logger.info("线程池已关闭")

    def get_executor(self) -> Optional[ThreadPoolExecutor]:
        return self._executor

tp_manager = ThreadPoolManager()