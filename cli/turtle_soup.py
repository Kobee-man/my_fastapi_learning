"""
海龟汤游戏系统 - Qwen 3.5 4B 完美集成版
Turtle Soup Game System - Optimized for Qwen 3.5 4B Model

特性：
✅ Qwen 3.5 4B 模型深度优化
✅ 智能连接管理与自动重连
✅ 响应数据格式化与解析优化
✅ 性能监控与调优
✅ 中文语境特别增强
✅ 错误恢复机制

作者：AI Assistant
日期：2026-05-03
"""

import json
import os
import sys
import time
import re
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
import requests
from datetime import datetime


# ==================== Qwen 专用配置 ====================

@dataclass
class QwenConfig:
    """Qwen 3.5 4B 专属配置"""
    # 连接配置
    host: str = "http://localhost:11434"
    model: str = "qwen3.5:4b"
    
    # 推理参数（针对Qwen 3.5优化）
    temperature: float = 0.6        # 较低温度保证一致性
    top_p: float = 0.9              # 核采样参数
    top_k: int = 40                 # Top-K采样
    repeat_penalty: float = 1.1     # 重复惩罚
    
    # Token控制
    max_tokens: int = 2048          # 最大输出token数
    context_window: int = 32768     # 上下文窗口大小
    
    # 超时设置
    timeout: int = 180              # 请求超时(秒)
    connect_timeout: int = 30       # 连接超时(秒)
    
    # 重试机制
    max_retries: int = 3            # 最大重试次数
    retry_delay: float = 2.0        # 重试延迟(秒)
    
    # 缓存配置
    enable_cache: bool = True       # 启用响应缓存
    cache_ttl: int = 3600           # 缓存有效期(秒)
    
    # 性能监控
    log_requests: bool = True       # 记录请求日志
    performance_stats: bool = True  # 收集性能统计


@dataclass 
class GameConfig:
    """游戏配置"""
    difficulty: str = "medium"
    max_questions: int = 20
    max_hints: int = 3
    language: str = "zh"
    theme: str = "general"


# ==================== 枚举类型 ====================

class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"  
    HARD = "hard"

class GameStatus(Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"
    ABANDONED = "abandoned"

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    ERROR = "error"
    SLOW = "slow"


# ==================== Qwen优化的提示模板 ====================

class QwenPromptTemplates:
    """针对 Qwen 3.5 优化的提示模板"""
    
    SYSTEM_PROMPT_ZH = """你是一位经验丰富的海龟汤（情境猜谜）游戏主持人，名叫"小Q"。你正在使用通义千问大语言模型。

## 你的核心职责

### 🎯 规则铁律（必须严格遵守）
1. **真相保密**：绝对不能直接或间接透露完整故事真相
2. **四种回答**：只能使用以下标准回答：
   ✅ **是**：问题与真相完全吻合
   ❌ **否**：问题与真相矛盾或不相关  
   ⚪ **无关**：问题对推理没有帮助
   🟡 **部分相关**：涉及某个方面但不完全正确

### 💬 回答规范
- 格式：`【判断】简短理由（≤15字）`
- 示例：`【是】确实与时间有关`
- 保持神秘感，不要给太多线索
- 语气要冷静、专业、略带神秘

### 🎭 角色特点
- 你叫"小Q"，是海龟汤游戏专家
- 偶尔可以用"嗯..."、"有意思的问题"等开场
- 不要显得不耐烦，即使被问了很多次
- 可以适当调侃："这个问题很刁钻呢~"

### ⚠️ 特殊情况处理
- 直接问真相 → 【无关】请通过提问来推理吧
- 问题模糊 → 【无关】可以更具体一点吗？
- 重复问题 → 正常回答，不要提醒重复
- 多个问题 → 只回答第一个

记住：你的目标是引导玩家思考，而不是直接给答案！"""

    PUZZLE_GENERATION_PROMPT_ZH = """作为海龟汤出题专家，请生成一个{difficulty}难度的中文情境猜谜题目。

## 📋 题目要求

### 结构要求
1. **情境描述**（30-60字）
   - 制造强烈的认知冲突或悬念
   - 让人产生"为什么？"的疑问
   - 包含关键但隐晦的线索
   
2. **完整真相**（150-250字）
   - 逻辑严密，无漏洞
   - 能合理解释情境中的所有细节
   - 结局要有反转或意外性

### {difficulty_label}难度标准
{difficulty_criteria}

### 质量红线
✅ 必须遵守：
- 情境真实可信（非科幻奇幻）
- 真相完全合理且可推导
- 避免血腥暴力内容
- 适合全年龄段玩家

❌ 绝对禁止：
- 使用超自然元素解释
- 真相包含逻辑矛盾
- 情境过于抽象无法理解

## 📤 输出格式（严格JSON）
```json
{{
    "title": "题目标题（2-6字）",
    "situation": "情境描述",
    "truth": "完整真相", 
    "hints": ["提示1", "提示2", "提示3"],
    "category": "分类标签",
    "estimated_questions": 15,
    "tags": ["生活", "悬疑"],
    "key_elements": ["关键词1", "关键词2"]
}}
```

现在请生成题目："""

    QUESTION_JUDGMENT_PROMPT_TEMPLATE = """【海龟汤判断任务】

📖 当前情境：
{situation}

❓ 玩家第{question_num}问：
"{question}"

📜 近期问答记录：
{history}

---

请严格按照主持人规则进行判断。

⚠️ 重要：只输出JSON，不要其他内容！
```json
{{"answer": "是/否/无关/部分相关", "reason": "判断依据（≤15字）"}}
```"""


# ==================== 性能监控类 ====================

@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    cache_hits: int = 0
    average_response_time: float = 0.0
    
    def record_request(self, success: bool, latency_ms: float, tokens: int = 0):
        """记录一次请求"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        self.total_latency_ms += latency_ms
        self.total_tokens += tokens
        self.average_response_time = (
            self.total_latency_ms / self.total_requests
        )
    
    def get_summary(self) -> Dict:
        """获取统计摘要"""
        return {
            'total_requests': self.total_requests,
            'success_rate': f"{(self.successful_requests/max(1,self.total_requests))*100:.1f}%",
            'avg_latency': f"{self.average_response_time:.0f}ms",
            'total_tokens': self.total_tokens,
            'cache_hits': self.cache_hits
        }


# ==================== 响应缓存系统 ====================

class ResponseCache:
    """响应缓存管理器"""
    
    def __init__(self, ttl: int = 3600):
        self.cache: Dict[str, Tuple[str, float]] = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[str]:
        """获取缓存的响应"""
        if key in self.cache:
            response, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return response
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: str):
        """设置缓存"""
        self.cache[key] = (value, time.time())
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
    
    def generate_key(self, prompt: str, system_prompt: str = "", 
                     temperature: float = 0.7) -> str:
        """生成缓存键"""
        import hashlib
        content = f"{prompt}|{system_prompt}|{temperature}"
        return hashlib.md5(content.encode()).hexdigest()


# ==================== Qwen客户端（增强版） ====================

class QwenClient:
    """Qwen 3.5 4B 专用客户端 - 增强版"""
    
    def __init__(self, config: QwenConfig):
        self.config = config
        self.base_url = f"{config.host}/api"
        self.status = ConnectionStatus.DISCONNECTED
        self.metrics = PerformanceMetrics()
        self.cache = ResponseCache(config.cache_ttl) if config.enable_cache else None
        self._session = None
        self.last_error: Optional[str] = None
        self.model_info: Optional[Dict] = None
        
    @property
    def session(self) -> requests.Session:
        """获取或创建HTTP会话"""
        if self._session is None or self._session.closed:
            self._session = requests.Session()
            # 配置会话
            self._session.headers.update({
                'Content-Type': 'application/json',
                'User-Agent': 'TurtleSoup-Qwen/1.0'
            })
            # 设置超时
            self._session.timeout = (
                self.config.connect_timeout,
                self.config.timeout
            )
        return self._session
    
    def check_connection(self) -> Tuple[ConnectionStatus, str]:
        """
        检查Ollama服务连接状态（增强版）
        
        Returns:
            (status, message) 元组
        """
        try:
            start_time = time.time()
            
            # 测试基本连接
            response = self.session.get(
                f"{self.base_url}/tags",
                timeout=10
            )
            
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查模型是否存在
                models = [m['name'] for m in data.get('models', [])]
                
                if self.config.model in models:
                    self.status = ConnectionStatus.CONNECTED
                    
                    # 获取模型详细信息
                    self.model_info = self._get_model_info()
                    
                    msg = f"✓ 服务正常 (延迟: {latency:.0f}ms)"
                    if latency > 1000:
                        self.status = ConnectionStatus.SLOW
                        msg = f"⚠ 服务较慢 (延迟: {latency:.0f}ms)"
                    
                    return (self.status, msg)
                else:
                    self.status = ConnectionStatus.ERROR
                    available = ", ".join(models[:5]) or "无"
                    return (ConnectionStatus.ERROR, 
                           f"模型 '{self.config.model}' 未安装\n可用模型: {available}")
            
            else:
                self.status = ConnectionStatus.ERROR
                return (ConnectionStatus.ERROR, 
                       f"服务异常 (HTTP {response.status_code})")
                
        except requests.exceptions.ConnectionError:
            self.status = ConnectionStatus.DISCONNECTED
            return (ConnectionStatus.DISCONNECTED, 
                   "无法连接到Ollama服务")
        except requests.exceptions.Timeout:
            self.status = ConnectionStatus.SLOW
            return (ConnectionStatus.SLOW, "连接超时")
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.last_error = str(e)
            return (ConnectionStatus.ERROR, f"连接错误: {e}")
    
    def _get_model_info(self) -> Optional[Dict]:
        """获取模型详细信息"""
        try:
            response = self.session.post(
                f"{self.base_url}/show",
                json={"name": self.config.model},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    def list_models(self) -> List[Dict]:
        """列出所有可用模型及详情"""
        try:
            response = self.session.get(f"{self.base_url}/tags", timeout=10)
            if response.status_code == 200:
                models_data = response.json().get('models', [])
                result = []
                for m in models_data:
                    info = {
                        'name': m['name'],
                        'size': m.get('size', 0),
                        'modified_at': m.get('modified_at', ''),
                        'is_current': m['name'] == self.config.model
                    }
                    result.append(info)
                return sorted(result, key=lambda x: x['name'])
        except Exception as e:
            print(f"[警告] 获取模型列表失败: {e}")
        return []
    
    def generate_with_retry(
        self, 
        prompt: str, 
        system_prompt: str = "",
        temperature: float = None,
        max_retries: int = None
    ) -> Tuple[bool, str, Dict]:
        """
        带重试机制的生成方法（核心方法）
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度参数
            max_retries: 最大重试次数
            
        Returns:
            (success, response_text, metadata) 元组
            metadata包含: latency_ms, tokens_used, cache_hit, attempt
        """
        
        temp = temperature or self.config.temperature
        retries = max_retries or self.config.max_retries
        metadata = {
            'latency_ms': 0,
            'tokens_used': 0,
            'cache_hit': False,
            'attempt': 0,
            'model': self.config.model
        }
        
        # 检查缓存
        if self.cache:
            cache_key = self.cache.generate_key(
                prompt, system_prompt, temp
            )
            cached = self.cache.get(cache_key)
            if cached:
                metadata['cache_hit'] = True
                self.metrics.cache_hits += 1
                return (True, cached, metadata)
        
        last_error = None
        
        for attempt in range(1, retries + 1):
            metadata['attempt'] = attempt
            
            try:
                start_time = time.time()
                
                # 构建请求payload
                payload = {
                    "model": self.config.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temp,
                        "top_p": self.config.top_p,
                        "top_k": self.config.top_k,
                        "repeat_penalty": self.config.repeat_penalty,
                        "num_predict": self.config.max_tokens
                    }
                }
                
                if system_prompt:
                    payload["system"] = system_prompt
                
                # 发送请求
                print(f"  [调用] 第{attempt}次尝试 | 模型: {self.config.model} | "
                      f"温度: {temp}...")
                
                response = self.session.post(
                    f"{self.base_url}/generate",
                    json=payload
                )
                
                # 计算延迟
                latency = (time.time() - start_time) * 1000
                metadata['latency_ms'] = latency
                
                if response.status_code == 200:
                    result = response.json()
                    text = result.get('response', '').strip()
                    
                    # 提取token信息
                    eval_count = result.get('eval_count', 0)
                    prompt_count = result.get('prompt_eval_count', 0)
                    metadata['tokens_used'] = eval_count + prompt_count
                    
                    if not text:
                        print(f"  [警告] 模型返回空内容 (attempt {attempt})")
                        continue
                    
                    # 记录成功指标
                    self.metrics.record_request(True, latency, metadata['tokens_used'])
                    
                    # 存入缓存
                    if self.cache and text:
                        self.cache.set(cache_key, text)
                    
                    # 日志输出
                    if self.config.log_requests:
                        print(f"  [完成] 延迟: {latency:.0f}ms | "
                              f"Token: {metadata['tokens_used']} | "
                              f"长度: {len(text)}字符")
                    
                    return (True, text, metadata)
                    
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                    last_error = error_msg
                    print(f"  [错误] {error_msg}")
                    
            except requests.exceptions.Timeout:
                last_error = "请求超时"
                print(f"  [超时] 第{attempt}次超时 ({self.config.timeout}秒)")
                
            except requests.exceptions.ConnectionError:
                last_error = "连接断开"
                print(f"  [断开] 第{attempt}次连接失败")
                # 尝试重新检查连接
                self.check_connection()
                
            except Exception as e:
                last_error = str(e)
                print(f"  [异常] {e}")
            
            # 等待后重试
            if attempt < retries:
                wait_time = self.config.retry_delay * attempt
                print(f"  [等待] {wait_time:.1f}秒后重试...")
                time.sleep(wait_time)
        
        # 所有重试都失败
        self.metrics.record_request(False, metadata['latency_ms'])
        self.last_error = last_error
        return (False, "", metadata)
    
    def generate_puzzle(self, difficulty: str = "medium") -> Tuple[bool, Optional[Dict]]:
        """
        生成海龟汤题目（专用方法）
        
        Returns:
            (success, puzzle_dict) 元组
        """
        templates = QwenPromptTemplates()
        
        # 难度映射
        diff_map = {
            'easy': ('简单', '• 情境贴近日常生活\n• 推理线索明显直接\n• 适合新手入门'),
            'medium': ('中等', '• 需要一定联想能力\n• 故事有转折和悬念\n• 适合有经验的玩家'),
            'hard': ('困难', '• 需要多步复杂推理\n• 涉及心理或社会因素\n• 适合高阶推理爱好者')
        }
        
        diff_label, criteria = diff_map.get(difficulty, ('中等', ''))
        
        prompt = templates.PUZZLE_GENERATION_PROMPT_ZH.format(
            difficulty=difficulty,
            difficulty_label=diff_label,
            difficulty_criteria=criteria
        )
        
        system_prompt = templates.SYSTEM_PROMPT_ZH
        
        # 使用较低温度确保结构化输出
        success, raw_response, meta = self.generate_with_retry(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5  # 低温度以获得更结构化的输出
        )
        
        if not success or not raw_response:
            return (False, None)
        
        # 解析JSON响应
        puzzle = self._parse_puzzle_json(raw_response)
        
        if puzzle:
            # 补充元数据
            puzzle['_meta'] = {
                'generated_at': datetime.now().isoformat(),
                'model': self.config.model,
                'difficulty': difficulty,
                'generation_time_ms': meta['latency_ms']
            }
            return (True, puzzle)
        
        return (False, None)
    
    def judge_question(
        self, 
        question: str, 
        situation: str, 
        history: List[Dict],
        question_num: int
    ) -> Tuple[bool, Dict]:
        """
        判断玩家问题（专用方法）
        
        Returns:
            (success, judgment_dict) 元组
            judgment_dict: {'answer': str, 'reason': str}
        """
        templates = QwenPromptTemplates()
        
        # 格式化历史记录
        history_lines = []
        for i, q in enumerate(history[-8:], 1):  # 最近8条
            ans_emoji = {'是': '✅', '否': '❌', '无关': '⚪', '部分相关': '🟡'}
            emoji = ans_emoji.get(q.get('answer', ''), '❓')
            history_lines.append(f"  Q{i}: {q.get('question', '')} → {emoji} {q.get('answer', '')}")
        
        history_text = "\n".join(history_lines) if history_lines else "  （暂无历史记录）"
        
        prompt = templates.QUESTION_JUDGMENT_PROMPT_TEMPLATE.format(
            situation=situation,
            question=question,
            question_num=question_num,
            history=history_text
        )
        
        system_prompt = templates.SYSTEM_PROMPT_ZH
        
        # 使用极低温度保证一致性
        success, raw_response, meta = self.generate_with_retry(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3  # 很低温度以确保一致的判断
        )
        
        if not success or not raw_response:
            return (False, {'answer': '无关', 'reason': '判断服务暂不可用'})
        
        # 解析判断结果
        judgment = self._parse_judgment_json(raw_response)
        
        if judgment:
            return (True, judgment)
        
        # 解析失败时的降级处理
        return (False, {'answer': '无关', 'reason': '解析异常'})
    
    def _parse_puzzle_json(self, raw_text: str) -> Optional[Dict]:
        """解析题目JSON（增强版）"""
        # 清理文本
        text = raw_text.strip()
        
        # 移除markdown代码块标记
        patterns_to_remove = [
            r'```json\s*',
            r'```\s*',
            r'``\s*',
        ]
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 尝试提取JSON对象
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                data = json.loads(json_str)
                
                # 验证必要字段
                required_fields = ['situation', 'truth']
                if all(k in data for k in required_fields):
                    # 补充默认值
                    defaults = {
                        'title': '未命名',
                        'hints': [],
                        'category': '未分类',
                        'estimated_questions': 20,
                        'tags': [],
                        'key_elements': []
                    }
                    for key, val in defaults.items():
                        if key not in data:
                            data[key] = val
                    
                    return data
                    
            except json.JSONDecodeError as e:
                print(f"  [警告] JSON解析错误: {e}")
        
        # JSON解析失败的降级方案
        print("  [降级] 使用纯文本解析...")
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        return {
            'title': lines[0][:50] if lines else '未知',
            'situation': text[:200],
            'truth': text,
            'hints': ['暂无提示'],
            'category': '自动生成',
            'estimated_questions': 20,
            'tags': [],
            '_raw': True
        }
    
    def _parse_judgment_json(self, raw_text: str) -> Optional[Dict]:
        """解析判断结果JSON（增强版）"""
        text = raw_text.strip()
        
        # 清理
        for pattern in [r'```json\s*', r'```\s*', r'``\s*']:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 提取JSON
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                
                answer = data.get('answer', '').strip()
                reason = data.get('reason', '').strip()
                
                # 标准化答案
                valid_answers = ['是', '否', '无关', '部分相关']
                
                if answer in valid_answers:
                    return {
                        'answer': answer,
                        'reason': reason[:50] if reason else ''
                    }
                
                # 模糊匹配
                for valid in valid_answers:
                    if valid in answer or answer in valid:
                        return {'answer': valid, 'reason': reason[:50]}
                
            except json.JSONDecodeError:
                pass
        
        # 纯文本解析
        if any(k in text for k in ['是', '否', '无关', '部分相关']):
            for ans in ['是', '否', '部分相关', '无关']:
                if ans in text:
                    return {'answer': ans, 'reason': ''}
        
        return None
    
    def get_performance_report(self) -> str:
        """获取性能报告"""
        stats = self.metrics.get_summary()
        
        report = f"""
╔══════════════════════════════════════╗
║     📊 Qwen 3.5 4B 性能报告         ║
╠══════════════════════════════════════╣
║  模型: {self.config.model:<28} ║
║  总请求: {stats['total_requests']:<26} ║
║  成功率: {stats['success_rate']:<27} ║
║  平均延迟: {stats['avg_latency']:<25} ║
║  总Token: {stats['total_tokens']:<26} ║
║  缓存命中: {stats['cache_hits']:<26} ║
╚══════════════════════════════════════╝
        """
        return report
    
    def cleanup(self):
        """清理资源"""
        if self._session and not self._session.closed:
            self._session.close()
            self._session = None
        if self.cache:
            self.cache.clear()


# ==================== 游戏状态管理 ====================

@dataclass
class GameState:
    """游戏状态"""
    game_id: str
    status: GameStatus = GameStatus.WAITING
    puzzle: Optional[Dict] = None
    current_question_count: int = 0
    hints_used: int = 0
    questions_history: List[Dict] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    winner: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


class GameManager:
    """游戏管理器"""
    
    def __init__(self):
        self.games: Dict[str, GameState] = {}
        self.active_id: Optional[str] = None
    
    def create_game(self, config: GameConfig) -> str:
        import uuid
        game_id = uuid.uuid4().hex[:8]
        
        self.games[game_id] = GameState(
            game_id=game_id,
            status=GameStatus.WAITING,
            start_time=time.time()
        )
        self.active_id = game_id
        return game_id
    
    def get_active(self) -> Optional[GameState]:
        if self.active_id and self.active_id in self.games:
            return self.games[self.active_id]
        return None
    
    def update_status(self, gid: str, status: GameStatus):
        if gid in self.games:
            self.games[gid].status = status
            if status == GameStatus.FINISHED:
                self.games[gid].end_time = time.time()
    
    def add_question(self, gid: str, q: str, a: str, r: str = ""):
        if gid in self.games:
            g = self.games[gid]
            g.questions_history.append({
                'question': q,
                'answer': a,
                'reason': r,
                'time': time.time()
            })
            g.current_question_count += 1
    
    def use_hint(self, gid: str) -> bool:
        if gid in self.games:
            g = self.games[gid]
            hints = g.puzzle.get('hints', [])
            if g.hints_used < len(hints):
                g.hints_used += 1
                return True
        return False
    
    def get_remaining_hints(self, gid: str) -> List[str]:
        if gid in self.games:
            g = self.games[gid]
            hints = g.puzzle.get('hints', [])
            return hints[g.hints_used:]
        return []


# ==================== CLI界面 ====================

class TurtleSoupCLI_Qwen:
    """Qwen版CLI界面"""
    
    def __init__(self, client: QwenClient, game_config: GameConfig):
        self.client = client
        self.game_config = game_config
        self.manager = GameManager()
        self.running = True
    
    def show_banner(self):
        banner = """
╔══════════════════════════════════════════════════════╗
║                                                      ║
║   🐢 海龟汤游戏系统 v2.0                             ║
║   ─────────────────────                              ║
║   🔌 Powered by Qwen 3.5 4B (Ollama)               ║
║   🧠 本地AI · 零延迟 · 完全离线                       ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def initialize_system(self) -> bool:
        """初始化并检查系统"""
        print("\n🔍 正在初始化系统...\n")
        
        # 检查连接
        status, msg = self.client.check_connection()
        print(f"  {msg}\n")
        
        if status == ConnectionStatus.CONNECTED:
            print("✅ 系统就绪！\n")
            
            # 显示模型信息
            if self.client.model_info:
                info = self.client.model_info
                details = info.get('details', {})
                size_gb = details.get('parameter_size', '未知')
                family = details.get('family', '未知')
                print(f"  📦 模型信息:")
                print(f"     名称: {self.client.config.model}")
                print(f"     家族: {family}")
                print(f"     大小: {size_gb}")
                print()
            
            return True
        else:
            print("❌ 初始化失败！")
            print("\n请检查:")
            print("  1. Ollama是否运行: ollama serve")
            print(f"  2. 模型是否已安装: ollama pull {self.client.config.model}")
            print(f"  3. 服务地址是否正确: {self.client.config.host}\n")
            return False
    
    def main_menu(self):
        menu = """
┌──────────────────────────────────────┐
│         🎮 主菜单                    │
├──────────────────────────────────────┤
│  1. 🆕 开始新游戏                    │
│  2. ⚙️  系统设置                     │
│  3. 📊 性能报告                     │
│  4. 📋 模型管理                     │
│  5. ❓ 帮助文档                     │
│  6. 🚪 退出系统                     │
└──────────────────────────────────────┘
        """
        print(menu)
    
    def run_new_game(self):
        """运行新游戏"""
        print("\n" + "=" * 55)
        print("🎮 创建新游戏")
        print("=" * 55)
        
        # 创建游戏实例
        game_id = self.manager.create_game(self.game_config)
        game = self.manager.get_active()
        
        print(f"\n  🆔 游戏ID: {game_id}")
        print(f"  📊 难度: {self.game_config.difficulty}")
        print(f"\n  🔄 正在调用 AI 生成题目...\n")
        
        # 生成题目
        success, puzzle = self.client.generate_puzzle(
            difficulty=self.game_config.difficulty
        )
        
        if not success or not puzzle:
            print("  ❌ 题目生成失败！")
            print("  可能原因:")
            print("    • 模型未正确加载")
            print("    • 网络/内存问题")
            print("  请稍后重试或更换模型。\n")
            return
        
        # 设置题目
        game.puzzle = puzzle
        self.manager.update_status(game_id, GameStatus.PLAYING)
        
        # 显示题目
        print("=" * 55)
        print("  📖 【情境描述】")
        print("-" * 55)
        print(f"\n  {puzzle.get('situation', '')}\n")
        print("-" * 55)
        
        meta = puzzle.get('_meta', {})
        if meta:
            gen_time = meta.get('generation_time_ms', 0)
            print(f"  ⏱️  生成耗时: {gen_time:.0f}ms | "
                  f"模型: {meta.get('model', 'unknown')}")
        
        print("\n  💡 提示: 通过提问推理真相！")
        print("     命令: hint | answer | status | quit\n")
        
        # 游戏循环
        self._game_loop(game)
    
    def _game_loop(self, game: GameState):
        """游戏主循环"""
        while game.status == GameStatus.PLAYING:
            # 检查提问限制
            if game.current_question_count >= self.game_config.max_questions:
                print(f"\n  ⚠️ 达到最大提问数 ({self.game_config.max_questions})")
                self._end_game(game, False)
                break
            
            # 状态栏
            remaining = self.game_config.max_questions - game.current_question_count
            print(f"  📈 进度: [{game.current_question_count}/{self.game_config.max_questions}] "
                  f"剩余 {remaining} 题")
            
            # 用户输入
            try:
                user_input = input("  ❓ 提问 > ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n\n  👋 游戏中断")
                break
            
            if not user_input:
                continue
            
            cmd = user_input.lower()
            
            # 命令处理
            if cmd in ['quit', 'exit', 'q']:
                print("\n  👋 游戏结束")
                self.manager.update_status(game.game_id, GameStatus.ABANDONED)
                break
                
            elif cmd == 'hint':
                self._handle_hint(game)
                continue
                
            elif cmd == 'answer':
                self._handle_answer(game)
                break
                
            elif cmd == 'status':
                self._show_status(game)
                continue
                
            elif cmd in ['help', '?']:
                self._show_help()
                continue
            
            # 处理普通问题
            self._process_question(game, user_input)
    
    def _process_question(self, game: GameState, question: str):
        """处理玩家问题"""
        print(f"\n  🤔 AI正在思考...\n")
        
        success, judgment = self.client.judge_question(
            question=question,
            situation=game.puzzle.get('situation', ''),
            history=game.questions_history,
            question_num=game.current_question_count + 1
        )
        
        if not success:
            print("  ⚠️ 判断失败，默认回复: 无关\n")
            judgment = {'answer': '无关', 'reason': '服务暂时不可用'}
        
        # 记录问题
        self.manager.add_question(
            game.game_id,
            question,
            judgment['answer'],
            judgment.get('reason', '')
        )
        
        # 显示结果
        emojis = {'是': '✅', '否': '❌', '无关': '⚪', '部分相关': '🟡'}
        emoji = emojis.get(judgment['answer'], '❓')
        reason = f" - {judgment['reason']}" if judgment.get('reason') else ""
        
        print(f"  {emoji} {judgment['answer']}{reason}\n")
    
    def _handle_hint(self, game: GameState):
        """处理提示命令"""
        remaining = self.manager.get_remaining_hints(game.game_id)
        
        if not remaining:
            print("  ⚠️ 提示已用完！\n")
            return
        
        if self.manager.use_hint(game.game_id):
            hint = remaining[0]
            print(f"\n  💡 提示 {game.hints_used}: {hint}\n")
    
    def _handle_answer(self, game: GameState):
        """处理答案提交"""
        print("\n" + "-" * 55)
        print("  ✍️ 请输入你认为的完整真相:")
        print("-" * 55)
        
        try:
            user_answer = input("\n  你的答案 > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  取消提交\n")
            return
        
        if not user_answer:
            print("  ❌ 答案不能为空\n")
            return
        
        # 简单验证（关键词匹配）
        truth = game.puzzle.get('truth', '').lower()
        answer_lower = user_answer.lower()
        
        truth_words = set(re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', truth))
        answer_words = set(re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', answer_lower))
        
        overlap = len(truth_words & answer_words) / max(len(truth_words), 1)
        
        if overlap > 0.35:
            print("\n  🎉 恭喜！答案正确！")
            game.winner = "Player"
            self._end_game(game, True)
        else:
            print(f"\n  ❌ 还不太对哦 (匹配度: {overlap*100:.0f}%)")
            
            choice = input("  继续(1) 或 查看真相(2) > ").strip()
            if choice == '2':
                self._end_game(game, False)
    
    def _end_game(self, game: GameState, is_correct: bool):
        """结束游戏并显示结果"""
        print("\n" + "=" * 55)
        print("  🔍 【完整真相】")
        print("=" * 55)
        print(f"\n{game.puzzle.get('truth', '未知')}\n")
        
        duration = time.time() - (game.start_time or 0)
        mins = int(duration // 60)
        secs = int(duration % 60)
        
        print("-" * 55)
        print("  📈 游戏统计:")
        print(f"     • 提问数: {game.current_question_count}")
        print(f"     • 使用提示: {game.hints_used}")
        print(f"     • 用时: {mins}分{secs}秒")
        print(f"     • 结果: {'✅ 成功' if is_correct else '📚 学习'}")
        print("-" * 55 + "\n")
        
        self.manager.update_status(game.game_id, GameStatus.FINISHED)
    
    def _show_status(self, game: GameState):
        """显示游戏状态"""
        elapsed = int(time.time() - (game.start_time or 0))
        print(f"\n  📊 游戏状态:")
        print(f"     ID: {game.game_id}")
        print(f"     状态: {game.status.value}")
        print(f"     进度: {game.current_question_count}/{self.game_config.max_questions}")
        print(f"     提示: {game.hints_used}/{len(game.puzzle.get('hints', []))}")
        print(f"     用时: {elapsed}秒\n")
    
    def _show_help(self):
        """显示帮助"""
        help_text = """
  📖 游戏帮助:

  命令列表:
    • hint      获取提示
    • answer    提交最终答案
    • status    查看当前进度
    • help/?    显示此帮助
    • quit/q    退出游戏

  技巧提示:
    ✓ 从"为什么"开始提问
    ✓ 关注时间、地点、人物关系
    ✓ 利用排除法缩小范围
    ✓ 卡住时使用提示功能
        """
        print(help_text)
    
    def show_performance(self):
        """显示性能报告"""
        print(self.client.get_performance_report())
    
    def show_models(self):
        """显示可用模型"""
        print("\n  📋 可用模型:\n")
        models = self.client.list_models()
        
        if models:
            for i, m in enumerate(models, 1):
                current = " ◄ 当前" if m['is_current'] else ""
                size_mb = m['size'] / (1024*1024)
                print(f"  {i}. {m['name']:<25} {size_mb:>8.1f}MB{current}")
        else:
            print("  未找到可用模型")
            print("\n  安装命令:")
            print(f"    ollama pull {self.client.config.model}")
        print()
    
    def run_settings(self):
        """设置菜单"""
        while True:
            print(f"\n  ⚙️ 当前配置:")
            print(f"     模型: {self.client.config.model}")
            print(f"     难度: {self.game_config.difficulty}")
            print(f"     最大提问: {self.game_config.max_questions}")
            print(f"     语言: {'中文' if self.game_config.language=='zh' else 'English'}")
            print("\n  选项:")
            print("  1. 更改模型")
            print("  2. 更改难度")
            print("  3. 更改最大提问数")
            print("  4. 返回主菜单")
            
            choice = input("\n  选择 > ").strip()
            
            if choice == '1':
                self._change_model()
            elif choice == '2':
                self._change_difficulty()
            elif choice == '3':
                self._change_max_questions()
            elif choice == '4':
                break
    
    def _change_model(self):
        """更改模型"""
        models = self.client.list_models()
        names = [m['name'] for m in models]
        
        print("\n  可用模型:")
        for i, name in enumerate(names, 1):
            print(f"    {i}. {name}")
        
        choice = input("\n  选择编号或输入名称 > ").strip()
        
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(names):
                self.client.config.model = names[idx]
                print(f"  ✓ 已切换: {names[idx]}")
        elif choice in names:
            self.client.config.model = choice
            print(f"  ✓ 已切换: {choice}")
        else:
            print("  ✗ 无效选择")
    
    def _change_difficulty(self):
        """更改难度"""
        print("\n  难度: easy(简单) | medium(中等) | hard(困难)")
        d = input("  选择 > ").strip().lower()
        
        if d in ['easy', 'medium', 'hard']:
            self.game_config.difficulty = d
            print(f"  ✓ 难度: {d}")
        else:
            print("  ✗ 无效选择")
    
    def _change_max_questions(self):
        """更改最大提问数"""
        n = input("  新的最大提问数 (5-50) > ").strip()
        
        try:
            val = int(n)
            if 5 <= val <= 50:
                self.game_config.max_questions = val
                print(f"  ✓ 最大提问数: {val}")
            else:
                print("  ✗ 请输入5-50之间的数字")
        except ValueError:
            print("  ✗ 请输入有效数字")
    
    def main_loop(self):
        """主循环"""
        self.show_banner()
        
        if not self.initialize_system():
            input("\n按回车键退出...")
            return
        
        while self.running:
            self.main_menu()
            
            try:
                choice = input("  选择操作 > ").strip()
            except (KeyboardInterrupt, EOFError):
                break
            
            if choice == '1':
                self.run_new_game()
            elif choice == '2':
                self.run_settings()
            elif choice == '3':
                self.show_performance()
            elif choice == '4':
                self.show_models()
            elif choice == '5':
                self._show_help()
            elif choice in ['6', 'quit', 'exit', 'q']:
                print("\n  👋 感谢使用！再见！")
                self.running = False
            else:
                print("  ✗ 无效选择，请重试\n")
        
        # 清理资源
        self.client.cleanup()


# ==================== 主程序入口 ====================

def main():
    """主函数"""
    
    # Qwen 3.5 4B 优化配置
    qwen_config = QwenConfig(
        host="http://localhost:11434",
        model="qwen3.5:4b",
        temperature=0.6,
        max_tokens=2048,
        timeout=180,
        max_retries=3,
        enable_cache=True,
        log_requests=True,
        performance_stats=True
    )
    
    game_config = GameConfig(
        difficulty="medium",
        max_questions=20,
        max_hints=3,
        language="zh"
    )
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith('--model='):
                qwen_config.model = arg.split('=')[1]
            elif arg.startswith('--host='):
                qwen_config.host = arg.split('=')[1]
            elif arg.startswith('--difficulty='):
                game_config.difficulty = arg.split('=')[1]
            elif arg in ['--help', '-h']:
                print("""
用法: python turtle_soup_qwen.py [选项]

选项:
  --model=<模型名>       指定模型 (默认: qwen3.5:4b)
  --host=<地址>          Ollama服务地址
  --difficulty=<难度>    easy/medium/hard
  --help, -h             帮助信息

示例:
  python turtle_soup_qwen.py
  python turtle_soup_qwen.py --model=qwen3.5:4b --difficulty=hard
                """)
                sys.exit(0)
    
    # 创建客户端和界面
    client = QwenClient(qwen_config)
    cli = TurtleSoupCLI_Qwen(client, game_config)
    
    # 运行主程序
    try:
        cli.main_loop()
    except KeyboardInterrupt:
        print("\n\n程序中断")
    except Exception as e:
        print(f"\n[致命错误] {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.cleanup()


if __name__ == "__main__":
    main()
