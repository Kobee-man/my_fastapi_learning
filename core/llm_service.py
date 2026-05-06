"""
LLM服务模块 - 支持本地Ollama和外部API两种模式

使用方式：
    from core.llm_service import llm_service

    response = await llm_service.chat("你好")
    response = await llm_service.chat("生成题目", system_prompt="你是出题专家")

切换模式：修改下方 LLM_CONFIG 中的 mode 字段，或设置环境变量 LLM_MODE
"""

import os
import json
import httpx
from typing import Optional
from dataclasses import dataclass, field


# ==================== 配置 ====================

@dataclass
class LLMConfig:
    """LLM配置"""
    # 模式: "local" (Ollama) 或 "external" (OpenAI兼容API)
    mode: str = field(default_factory=lambda: os.getenv("LLM_MODE", "local"))

    # 本地模式 (Ollama)
    ollama_host: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen3.5:4b"))

    # 外部API模式 (OpenAI兼容)
    api_url: str = field(default_factory=lambda: os.getenv(
        "LLM_API_URL", "https://api.openai.com/v1/chat/completions"
    ))
    api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    api_model: str = field(default_factory=lambda: os.getenv("LLM_API_MODEL", "gpt-3.5-turbo"))

    # 通用参数
    temperature: float = 0.8
    max_tokens: int = 1000
    timeout: float = 30.0


# ==================== 服务 ====================

class LLMService:
    """LLM服务，支持本地/外部API双模式"""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()

    @property
    def mode(self) -> str:
        return self.config.mode

    def is_available(self) -> bool:
        """检查当前模式的LLM是否可用"""
        if self.config.mode == "local":
            return True  # Ollama本地服务始终认为可用（由调用时判断连接）
        elif self.config.mode == "external":
            return bool(self.config.api_key)
        return False

    async def chat(self, prompt: str, system_prompt: str = "") -> str:
        """
        调用LLM进行对话

        Args:
            prompt: 用户输入
            system_prompt: 系统提示词

        Returns:
            LLM响应文本

        Raises:
            LLMError: 调用失败时抛出
        """
        if self.config.mode == "local":
            return await self._call_ollama(prompt, system_prompt)
        elif self.config.mode == "external":
            return await self._call_external_api(prompt, system_prompt)
        else:
            raise LLMError(f"不支持的模式: {self.config.mode}")

    async def _call_ollama(self, prompt: str, system_prompt: str = "") -> str:
        """调用本地Ollama服务"""
        url = f"{self.config.ollama_host}/api/generate"

        payload = {
            "model": self.config.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(url, json=payload)

                if response.status_code != 200:
                    raise LLMError(f"Ollama服务错误 (HTTP {response.status_code}): {response.text}")

                data = response.json()
                text = data.get("response", "").strip()
                if not text:
                    raise LLMError("Ollama返回空内容")
                return text

        except httpx.ConnectError:
            raise LLMError("无法连接Ollama服务，请确认 ollama serve 已启动")
        except httpx.TimeoutException:
            raise LLMError(f"Ollama请求超时 ({self.config.timeout}s)")
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f"Ollama调用失败: {e}")

    async def _call_external_api(self, prompt: str, system_prompt: str = "") -> str:
        """调用外部OpenAI兼容API"""
        if not self.config.api_key:
            raise LLMError("外部API模式需要设置 LLM_API_KEY")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.config.api_model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    self.config.api_url,
                    headers=headers,
                    json=payload,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                elif response.status_code == 401:
                    raise LLMError("API密钥无效或额度不足")
                elif response.status_code == 429:
                    raise LLMError("API请求频率超限，请稍后再试")
                else:
                    raise LLMError(f"外部API错误 (HTTP {response.status_code}): {response.text}")

        except LLMError:
            raise
        except httpx.ConnectError:
            raise LLMError(f"无法连接外部API: {self.config.api_url}")
        except httpx.TimeoutException:
            raise LLMError(f"外部API请求超时 ({self.config.timeout}s)")
        except Exception as e:
            raise LLMError(f"外部API调用失败: {e}")


class LLMError(Exception):
    """LLM调用异常"""
    pass


# ==================== 全局实例 ====================

llm_service = LLMService()
