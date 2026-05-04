"""
海龟汤（情境猜谜）游戏系统 - Ollama 本地LLM集成版本
Turtle Soup (Lateral Thinking Puzzle) Game System with Ollama Integration

功能特点：
- 完全本地运行，无需API Key
- 支持多种本地模型（Llama 3, Mistral, Qwen等）
- 结构化提示模板，确保AI行为一致
- 完整的游戏状态管理和进度跟踪
- CLI交互界面，易于使用

作者：AI Assistant
日期：2026-05-03
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any
from enum import Enum
import subprocess
import requests


# ==================== 配置类 ====================

@dataclass
class OllamaConfig:
    """Ollama配置"""
    host: str = "http://localhost:11434"
    model: str = "llama3"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 120
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass 
class GameConfig:
    """游戏配置"""
    difficulty: str = "medium"  # easy, medium, hard
    max_questions: int = 20
    max_hints: int = 3
    language: str = "zh"  # zh=中文, en=英文
    theme: str = "general"  # general, horror, mystery, life
    
    def to_dict(self) -> dict:
        return asdict(self)


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


class AnswerType(Enum):
    YES = "是"
    NO = "否"
    IRRELEVANT = "无关"
    PARTIAL = "部分相关"


# ==================== 提示模板系统 ====================

class PromptTemplates:
    """海龟汤游戏提示模板集合"""
    
    SYSTEM_PROMPT_ZH = """你是一位专业的海龟汤（情境猜谜）游戏主持人。你的职责是：

## 核心规则
1. **绝对保密真相**：在任何情况下都不能直接透露或暗示完整的故事真相
2. **只能用四种回答**：
   - 是：问题与真相完全吻合
   - 否：问题与真相矛盾或无关
   - 无关：问题对推断真相没有帮助
   - 部分相关：问题涉及真相的某个方面但不完全正确

3. **回答格式要求**：
   - 必须先给出判断（是/否/无关/部分相关）
   - 可以添加简短解释（不超过20字）
   - 保持神秘感，不要给太多提示

4. **角色扮演**：
   - 保持冷静、神秘的语气
   - 偶尔可以调侃玩家
   - 不要显得不耐烦

5. **特殊情况处理**：
   - 如果玩家直接问"真相是什么"，回答"无关"
   - 如果玩家问是否与某具体事物有关，根据实际情况回答
   - 如果问题模糊不清，可以请求澄清

记住：你的目标是让玩家通过逻辑推理逐步接近真相，而不是直接告诉答案。"""

    SYSTEM_PROMPT_EN = """You are a professional Turtle Soup (Lateral Thinking Puzzle) game host. Your responsibilities are:

## Core Rules
1. **Keep the truth secret**: Never reveal or hint at the complete story under any circumstances
2. **Only use four types of answers**:
   - Yes: Question matches the truth completely
   - No: Question contradicts or is irrelevant to the truth
   - Irrelevant: Question doesn't help deduce the truth
   - Partially relevant: Question touches on some aspect but isn't fully correct

3. **Response format requirements**:
   - Must give judgment first (Yes/No/Irrelevant/Partially relevant)
   - Can add brief explanation (max 20 words)
   - Maintain mystery, don't give too many hints

4. **Role-play**:
   - Keep a calm, mysterious tone
   - Occasionally tease players
   - Don't show impatience

5. **Special cases**:
   - If player asks "what's the truth directly", answer "Irrelevant"
   - If player asks about specific elements, answer based on facts
   - If question is unclear, ask for clarification

Remember: Your goal is to let players gradually approach the truth through logical reasoning, not to tell them directly."""

    PUZZLE_GENERATION_PROMPT_ZH = """请生成一个{difficulty}难度的海龟汤题目。要求：

1. **题目结构**：
   - 情境描述：一个令人困惑、看似矛盾的简短场景（50字以内）
   - 完整真相：合乎逻辑但出人意料的完整故事（200字以内）
   
2. **难度标准**：
   - 简单：日常生活场景，推理线索明显
   - 中等：需要一定联想能力，有转折
   - 困难：需要多步推理，涉及心理或社会因素

3. **质量要求**：
   - 情境必须让人产生强烈好奇心
   - 真相必须完全合理且能解释情境中的所有细节
   - 避免过于血腥或恐怖的内容
   - 确保可以通过是/否问题逐步推理出来

4. **输出格式**（严格JSON）：
```json
{{
    "title": "题目标题",
    "situation": "情境描述",
    "truth": "完整真相",
    "hints": ["提示1", "提示2", "提示3"],
    "category": "分类",
    "estimated_questions": 预估所需提问数,
    "tags": ["标签1", "标签2"]
}}
```"""

    PUZZLE_GENERATION_PROMPT_EN = """Generate a {difficulty} difficulty Turtle Soup puzzle. Requirements:

1. **Puzzle Structure**:
   - Situation: A confusing, seemingly contradictory short scene (under 50 words)
   - Complete Truth: A logical but unexpected complete story (under 200 words)

2. **Difficulty Standards**:
   - Easy: Daily life scenarios with obvious reasoning clues
   - Medium: Requires some imagination, has twists
   - Hard: Requires multi-step reasoning, involves psychological or social factors

3. **Quality Requirements**:
   - Situation must create strong curiosity
   - Truth must be completely logical and explain all details in situation
   - Avoid overly bloody or horrific content
   - Ensure it can be deduced step by step through yes/no questions

4. **Output Format** (strict JSON):
```json
{{
    "title": "Puzzle Title",
    "situation": "Situation Description", 
    "truth": "Complete Truth",
    "hints": ["Hint 1", "Hint 2", "Hint 3"],
    "category": "Category",
    "estimated_questions": estimated number of questions needed,
    "tags": ["tag1", "tag2"]
}}
```"""

    QUESTION_JUDGMENT_PROMPT_TEMPLATE = """当前海龟汤游戏信息：

【情境描述】
{situation}

【玩家问题】
{question}

【历史提问记录】
{history}

请根据以上信息，严格按照主持人规则进行判断。只输出JSON格式：
{{"answer": "是/否/无关/部分相关", "reason": "简短理由"}}"""


# ==================== 游戏状态管理 ====================

@dataclass
class GameState:
    """游戏状态数据类"""
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
        return {
            'game_id': self.game_id,
            'status': self.status.value,
            'puzzle': self.puzzle,
            'current_question_count': self.current_question_count,
            'hints_used': self.hints_used,
            'questions_history': self.questions_history,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'winner': self.winner
        }


class GameManager:
    """游戏状态管理器"""
    
    def __init__(self):
        self.games: Dict[str, GameState] = {}
        self.active_game_id: Optional[str] = None
        
    def create_game(self, config: GameConfig) -> str:
        """创建新游戏"""
        import uuid
        game_id = str(uuid.uuid4())[:8]
        
        game_state = GameState(
            game_id=game_id,
            status=GameStatus.WAITING,
            start_time=time.time()
        )
        
        self.games[game_id] = game_state
        self.active_game_id = game_id
        
        return game_id
    
    def get_active_game(self) -> Optional[GameState]:
        """获取当前活跃游戏"""
        if self.active_game_id and self.active_game_id in self.games:
            return self.games[self.active_game_id]
        return None
    
    def update_game_status(self, game_id: str, status: GameStatus):
        """更新游戏状态"""
        if game_id in self.games:
            self.games[game_id].status = status
            if status == GameStatus.FINISHED:
                self.games[game_id].end_time = time.time()
    
    def add_question(self, game_id: str, question: str, answer: str, reason: str = ""):
        """添加问题记录"""
        if game_id in self.games:
            game = self.games[game_id]
            game.questions_history.append({
                'question': question,
                'answer': answer,
                'reason': reason,
                'timestamp': time.time()
            })
            game.current_question_count += 1
            
    def use_hint(self, game_id: str) -> bool:
        """使用提示"""
        if game_id in self.games:
            game = self.games[game_id]
            if game.hints_used < len(game.puzzle.get('hints', [])):
                game.hints_used += 1
                return True
        return False
    
    def get_remaining_hints(self, game_id: str) -> List[str]:
        """获取剩余提示"""
        if game_id in self.games:
            game = self.games[game_id]
            all_hints = game.puzzle.get('hints', [])
            used = game.hints_used
            return all_hints[used:]
        return []


# ==================== Ollama集成层 ====================

class OllamaClient:
    """Ollama API客户端"""
    
    def __init__(self, config: OllamaConfig):
        self.config = config
        self.base_url = f"{config.host}/api"
        
    def check_connection(self) -> bool:
        """检查Ollama服务连接"""
        try:
            response = requests.get(f"{self.base_url}/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"[错误] 无法连接到Ollama服务: {e}")
            return False
    
    def list_models(self) -> List[str]:
        """列出可用模型"""
        try:
            response = requests.get(f"{self.base_url}/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except Exception as e:
            print(f"[错误] 获取模型列表失败: {e}")
            return []
    
    def generate(self, prompt: str, system_prompt: str = "", 
                 temperature: float = None, max_tokens: int = None) -> str:
        """
        调用Ollama生成接口
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示（可选）
            temperature: 温度参数（可选，默认使用config值）
            max_tokens: 最大token数（可选）
            
        Returns:
            生成的文本内容
        """
        url = f"{self.base_url}/generate"
        
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": max_tokens or self.config.max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            print(f"[调用] 正在调用模型 {self.config.model}...")
            response = requests.post(url, json=payload, timeout=self.config.timeout)
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('response', '')
                
                if not text.strip():
                    print("[警告] 模型返回空内容")
                    return ""
                    
                return text.strip()
            else:
                print(f"[错误] API调用失败: {response.status_code} - {response.text}")
                return ""
                
        except requests.exceptions.Timeout:
            print(f"[错误] 请求超时 ({self.config.timeout}秒)")
            return ""
        except Exception as e:
            print(f"[错误] 生成过程异常: {e}")
            return ""


# ==================== 海龟汤游戏引擎 ====================

class TurtleSoupEngine:
    """海龟汤游戏核心引擎"""
    
    def __init__(self, ollama_config: OllamaConfig, game_config: GameConfig):
        self.ollama = OllamaClient(ollama_config)
        self.game_config = game_config
        self.game_manager = GameManager()
        self.templates = PromptTemplates()
        
    def initialize(self) -> bool:
        """初始化系统"""
        print("=" * 60)
        print("🐢 海龟汤游戏系统 - Ollama 本地版")
        print("=" * 60)
        
        # 检查Ollama连接
        print("\n[检查] 正在连接Ollama服务...")
        if not self.ollama.check_connection():
            print("\n[错误] 无法连接到Ollama服务！")
            print("请确保：")
            print("  1. Ollama已安装并运行")
            print("  2. 服务地址正确:", self.ollama.config.host)
            print("  3. 执行命令启动: ollama serve")
            return False
        
        print("✓ Ollama服务连接成功")
        
        # 显示可用模型
        models = self.ollama.list_models()
        if models:
            print(f"\n可用模型列表:")
            for i, model in enumerate(models, 1):
                marker = " ← 当前选择" if model == self.ollama.config.model else ""
                print(f"  {i}. {model}{marker}")
        
        return True
    
    def generate_puzzle(self) -> Optional[Dict]:
        """生成新题目"""
        print("\n" + "=" * 40)
        print("🎲 正在生成新题目...")
        print("=" * 40)
        
        # 选择提示模板
        if self.game_config.language == "zh":
            prompt_template = self.templates.PUZZLE_GENERATION_PROMPT_ZH
            system_prompt = self.templates.SYSTEM_PROMPT_ZH
        else:
            prompt_template = self.templates.PUZZLE_GENERATION_PROMPT_EN
            system_prompt = self.templates.SYSTEM_PROMPT_EN
        
        # 填充难度参数
        difficulty_map = {
            "easy": "简单",
            "medium": "中等", 
            "hard": "困难"
        }
        prompt = prompt_template.format(
            difficulty=difficulty_map.get(
                self.game_config.difficulty, 
                self.game_config.difficulty
            )
        )
        
        # 调用模型生成
        raw_response = self.ollama.generate(prompt, system_prompt)
        
        if not raw_response:
            print("[错误] 题目生成失败")
            return None
        
        # 解析JSON响应
        try:
            # 尝试提取JSON（处理可能的markdown代码块）
            json_str = raw_response
            if "```json" in raw_response:
                start = raw_response.find("```json") + 7
                end = raw_response.find("```", start)
                json_str = raw_response[start:end].strip()
            elif "```" in raw_response:
                start = raw_response.find("```") + 3
                end = raw_response.find("```", start)
                json_str = raw_response[start:end].strip()
            
            puzzle_data = json.loads(json_str)
            
            print("✓ 题目生成成功！")
            print(f"\n标题: {puzzle_data.get('title', '未命名')}")
            print(f"难度: {self.game_config.difficulty}")
            print(f"分类: {puzzle_data.get('category', '未知')}")
            
            return puzzle_data
            
        except json.JSONDecodeError as e:
            print(f"[警告] JSON解析失败，尝试修复...")
            print(f"原始响应:\n{raw_response[:500]}...")
            
            # 返回原始数据作为备选
            return {
                'title': '自定义题目',
                'situation': raw_response.split('\n')[0] if '\n' in raw_response else raw_response[:100],
                'truth': raw_response,
                'hints': ['暂无提示'],
                'category': '未知',
                'estimated_questions': 15,
                'tags': []
            }
    
    def judge_question(self, question: str, puzzle: Dict, history: List[Dict]) -> Dict:
        """判断玩家问题"""
        # 准备历史记录文本
        history_text = "\n".join([
            f"Q{i+1}: {q['question']} → A: {q['answer']}"
            for i, q in enumerate(history[-10:])  # 只取最近10条
        ]) or "（尚无提问记录）"
        
        # 构建判断提示
        prompt = self.templates.QUESTION_JUDGMENT_PROMPT_TEMPLATE.format(
            situation=puzzle.get('situation', ''),
            question=question,
            history=history_text
        )
        
        # 获取系统提示
        system_prompt = (
            self.templates.SYSTEM_PROMPT_ZH 
            if self.game_config.language == "zh" 
            else self.templates.SYSTEM_PROMPT_EN
        )
        
        # 调用模型判断（降低温度以获得更一致的答案）
        raw_response = self.ollama.generate(
            prompt, 
            system_prompt,
            temperature=0.3  # 较低温度保证一致性
        )
        
        if not raw_response:
            return {'answer': '无关', 'reason': '判断失败'}
        
        # 解析响应
        try:
            # 提取JSON
            if "```json" in raw_response:
                start = raw_response.find("```json") + 7
                end = raw_response.find("```", start)
                json_str = raw_response[start:end].strip()
            elif "{" in raw_response:
                start = raw_response.find("{")
                end = raw_response.rfind("}") + 1
                json_str = raw_response[start:end]
            else:
                # 纯文本解析
                json_str = f'{{"answer": "{raw_response[:10]}", "reason": "{raw_response}"}}'
            
            result = json.loads(json_str)
            
            # 标准化答案
            answer = result.get('answer', '无关')
            if answer not in ['是', '否', '无关', '部分相关']:
                # 尝试映射
                if any(k in answer for k in ['yes', '是', '对', 'true']):
                    answer = '是'
                elif any(k in answer for k in ['no', '否', '错', 'false']):
                    answer = '否'
                else:
                    answer = '无关'
                    
            return {
                'answer': answer,
                'reason': result.get('reason', '')[:50]
            }
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"[警告] 判断结果解析异常: {e}")
            return {'answer': '无关', 'reason': '解析错误'}


# ==================== CLI界面 ====================

class TurtleSoupCLI:
    """命令行界面"""
    
    def __init__(self, engine: TurtleSoupEngine):
        self.engine = engine
        self.running = True
        
    def display_banner(self):
        """显示欢迎横幅"""
        banner = """
╔══════════════════════════════════════════════════╗
║                                                  ║
║     🐢 海龟汤游戏系统 - Ollama 本地版 v1.0      ║
║                                                  ║
║     Turtle Soup (Lateral Thinking Puzzle)         ║
║     Powered by Local LLM via Ollama              ║
║                                                  ║
╚══════════════════════════════════════════════════╝
        """
        print(banner)
    
    def display_menu(self):
        """显示主菜单"""
        menu = """
┌─────────────────────────────────────┐
│           🎮 主菜单                  │
├─────────────────────────────────────┤
│  1. 🆕 开始新游戏                    │
│  2. ⚙️  设置/配置                    │
│  3. 📋 查看可用模型                  │
│  4. ❓ 游戏帮助                      │
│  5. 🚪 退出                          │
└─────────────────────────────────────┘
        """
        print(menu)
    
    def display_settings_menu(self):
        """显示设置菜单"""
        settings = f"""
⚙️ 当前配置：
  • 模型: {self.engine.ollama.config.model}
  • 难度: {self.engine.game_config.difficulty}
  • 最大提问数: {self.engine.game_config.max_questions}
  • 最大提示数: {self.engine.game_config.max_hints}
  • 语言: {'中文' if self.engine.game_config.language == 'zh' else 'English'}

设置选项：
  1. 更改模型
  2. 更改难度 (easy/medium/hard)
  3. 更改最大提问数
  4. 更改语言 (zh/en)
  5. 返回主菜单
        """
        print(settings)
    
    def get_user_input(self, prompt: str = "") -> str:
        """获取用户输入"""
        try:
            return input(prompt).strip()
        except KeyboardInterrupt:
            print("\n\n检测到中断信号，正在退出...")
            sys.exit(0)
    
    def run_new_game(self):
        """运行新游戏流程"""
        print("\n" + "=" * 50)
        print("🎮 开始新游戏")
        print("=" * 50)
        
        # 创建游戏
        game_id = self.engine.game_manager.create_game(self.engine.game_config)
        game = self.engine.game_manager.get_active_game()
        
        # 生成题目
        puzzle = self.engine.generate_puzzle()
        if not puzzle:
            print("[错误] 无法生成题目，返回主菜单")
            return
        
        # 设置题目到游戏状态
        game.puzzle = puzzle
        self.engine.game_manager.update_game_status(game_id, GameStatus.PLAYING)
        
        # 显示情境
        print("\n" + "-" * 50)
        print("📖 【情境描述】")
        print("-" * 50)
        print(f"\n  {puzzle.get('situation', '')}\n")
        print("-" * 50)
        print("\n💡 请通过提问来推理真相！只能问能用'是/否'回答的问题。")
        print("   输入 'hint' 获取提示 | 'answer' 提交答案 | 'quit' 退出游戏\n")
        
        # 游戏循环
        while game.status == GameStatus.PLAYING:
            # 检查提问次数限制
            if game.current_question_count >= self.engine.game_config.max_questions:
                print(f"\n⚠️ 已达到最大提问次数 ({self.engine.game_config.max_questions})")
                self.show_truth_and_end(game)
                break
            
            # 显示当前状态
            remaining = self.engine.game_config.max_questions - game.current_question_count
            print(f"📊 进度: 已问 {game.current_question_count}/{self.engine.game_config.max_questions} 题")
            
            # 获取用户输入
            user_input = self.get_user_input("❓ 你的问题: ")
            
            if not user_input:
                continue
                
            # 处理特殊命令
            lower_input = user_input.lower()
            
            if lower_input in ['quit', 'exit', 'q', '退出']:
                print("\n👋 感谢游玩！")
                self.engine.game_manager.update_game_status(game_id, GameStatus.ABANDONED)
                break
                
            elif lower_input == 'hint':
                self.handle_hint_command(game)
                continue
                
            elif lower_input == 'answer':
                self.handle_answer_submission(game)
                break
                
            elif lower_input in ['status', '状态']:
                self.display_game_status(game)
                continue
                
            elif lower_input in ['help', '帮助', '?']:
                self.display_game_help()
                continue
            
            # 处理普通问题
            self.process_question(game, user_input)
    
    def process_question(self, game: GameState, question: str):
        """处理用户问题"""
        print(f"\n🔄 正在思考...")
        
        # 调用AI判断
        judgment = self.engine.judge_question(
            question, 
            game.puzzle, 
            game.questions_history
        )
        
        # 记录问题
        self.engine.game_manager.add_question(
            game.game_id, 
            question, 
            judgment['answer'],
            judgment.get('reason', '')
        )
        
        # 显示结果
        answer_emoji = {
            '是': '✅',
            '否': '❌', 
            '无关': '⚪',
            '部分相关': '🟡'
        }
        
        emoji = answer_emoji.get(judgment['answer'], '❓')
        reason = f" - {judgment['reason']}" if judgment.get('reason') else ''
        
        print(f"\n  {emoji} 回答: {judgment['answer']}{reason}\n")
    
    def handle_hint_command(self, game: GameState):
        """处理提示命令"""
        remaining_hints = self.engine.game_manager.get_remaining_hints(game.game_id)
        
        if not remaining_hints:
            print("\n⚠️ 已经用完所有提示了！")
            return
        
        if self.engine.game_manager.use_hint(game.game_id):
            hint = remaining_hints[0]
            print(f"\n💡 提示 {game.hints_used}: {hint}\n")
        else:
            print("\n❌ 无法获取提示")
    
    def handle_answer_submission(self, game: GameState):
        """处理答案提交"""
        print("\n" + "-" * 50)
        print("✍️ 请输入你认为的完整真相：")
        print("-" * 50)
        
        user_answer = self.get_user_input("\n你的答案: ")
        
        if not user_answer:
            print("❌ 答案不能为空")
            return
        
        # 简单验证（实际应用中可以用AI评估）
        truth = game.puzzle.get('truth', '').lower()
        user_answer_lower = user_answer.lower()
        
        # 关键词匹配验证
        truth_keywords = set(truth.replace('，', ' ').replace('。', ' ').split())
        user_keywords = set(user_answer_lower.replace('，', ' ').replace('。', ' ').split())
        
        overlap = len(truth_keywords & user_keywords) / max(len(truth_keywords), 1)
        
        if overlap > 0.3:  # 30%关键词重叠即算基本正确
            print("\n🎉 恭喜你！答案基本正确！")
            game.winner = "Player"
            self.show_truth_and_end(game, is_correct=True)
        else:
            print("\n❌ 还不太对哦，再想想~")
            print(f"💡 提示：你的答案覆盖了约 {overlap*100:.0f}% 的关键要素")
            
            # 给出选择
            choice = self.get_user_input("继续提问(1) 或 查看真相(2): ")
            if choice == '2':
                self.show_truth_and_end(game, is_correct=False)
    
    def show_truth_and_end(self, game: GameState, is_correct: bool = False):
        """显示真相并结束游戏"""
        print("\n" + "=" * 50)
        print("🔍 【完整真相】")
        print("=" * 50)
        print(f"\n{game.puzzle.get('truth', '未知')}\n")
        
        # 统计信息
        duration = time.time() - game.start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        print("-" * 50)
        print("📈 游戏统计:")
        print(f"  • 总提问数: {game.current_question_count}")
        print(f"  • 使用提示: {game.hints_used}")
        print(f"  • 用时: {minutes}分{seconds}秒")
        print(f"  • 结果: {'✅ 成功' if is_correct else '📚 学习'}")
        print("-" * 50 + "\n")
        
        self.engine.game_manager.update_game_status(game.game_id, GameStatus.FINISHED)
    
    def display_game_status(self, game: GameState):
        """显示游戏状态"""
        print(f"\n📊 当前游戏状态:")
        print(f"  • 游戏ID: {game.game_id}")
        print(f"  • 状态: {game.status.value}")
        print(f"  • 已提问: {game.current_question_count}/{self.engine.game_config.max_questions}")
        print(f"  • 剩余提示: {len(self.engine.game_manager.get_remaining_hints(game.game_id))}")
        print(f"  • 用时: {int(time.time() - game.start_time)}秒\n")
    
    def display_game_help(self):
        """显示游戏帮助"""
        help_text = """
📖 游戏帮助：

基本规则：
  • 你会看到一个令人困惑的情境
  • 通过提问来推理出背后的完整真相
  • AI只会用"是"、"否"、"无关"、"部分相关"回答
  
常用命令：
  • hint      - 获取提示（有限次）
  • answer    - 提交你的答案
  • status    - 查看当前进度
  • help      - 显示此帮助
  • quit      - 退出当前游戏

技巧提示：
  ✓ 从"为什么"开始提问往往更有效
  ✓ 注意时间、地点、人物关系等要素
  ✓ 如果卡住了，可以使用提示功能
  ✓ 真相往往比想象的更简单
        """
        print(help_text)
    
    def run_settings(self):
        """运行设置菜单"""
        while True:
            self.display_settings_menu()
            choice = self.get_user_input("请选择: ")
            
            if choice == '1':
                self.change_model_setting()
            elif choice == '2':
                self.change_difficulty_setting()
            elif choice == '3':
                self.change_max_questions_setting()
            elif choice == '4':
                self.change_language_setting()
            elif choice == '5':
                break
            else:
                print("无效选择，请重试")
    
    def change_model_setting(self):
        """更改模型设置"""
        models = self.engine.ollama.list_models()
        if not models:
            print("无法获取模型列表")
            return
            
        print("\n可用模型:")
        for i, model in enumerate(models, 1):
            print(f"  {i}. {model}")
        
        choice = self.get_user_input("选择模型编号或名称: ")
        
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                self.engine.ollama.config.model = models[idx]
                print(f"✓ 已切换到模型: {models[idx]}")
        elif choice in models:
            self.engine.ollama.config.model = choice
            print(f"✓ 已切换到模型: {choice}")
        else:
            print("无效选择")
    
    def change_difficulty_setting(self):
        """更改难度设置"""
        print("\n难度选项: easy(简单), medium(中等), hard(困难)")
        choice = self.get_user_input("选择难度: ").lower()
        
        if choice in ['easy', 'medium', 'hard']:
            self.engine.game_config.difficulty = choice
            print(f"✓ 难度已设置为: {choice}")
        else:
            print("无效选择")
    
    def change_max_questions_setting(self):
        """更改最大提问数"""
        choice = self.get_user_input("输入新的最大提问数 (5-50): ")
        
        try:
            value = int(choice)
            if 5 <= value <= 50:
                self.engine.game_config.max_questions = value
                print(f"✓ 最大提问数已设置为: {value}")
            else:
                print("请在5-50范围内")
        except ValueError:
            print("请输入有效数字")
    
    def change_language_setting(self):
        """更改语言设置"""
        print("\n语言选项: zh(中文), en(English)")
        choice = self.get_user_input("选择语言: ").lower()
        
        if choice in ['zh', 'en']:
            self.engine.game_config.language = choice
            lang_name = '中文' if choice == 'zh' else 'English'
            print(f"✓ 语言已设置为: {lang_name}")
        else:
            print("无效选择")
    
    def show_available_models(self):
        """显示可用模型"""
        print("\n📋 可用的Ollama模型:")
        print("-" * 40)
        
        models = self.engine.ollama.list_models()
        if models:
            for i, model in enumerate(models, 1):
                current = " ◄ 当前" if model == self.engine.ollama.config.model else ""
                print(f"  {i}. {model}{current}")
        else:
            print("  未找到可用模型")
            print("\n建议执行以下命令安装模型:")
            print("  ollama pull llama3")
            print("  ollama pull mistral")
            print("  ollama pull qwen")
        
        print("-" * 40)
    
    def display_help(self):
        """显示帮助信息"""
        help_text = """
📚 系统帮助：

关于海龟汤：
  海龟汤（情境猜谜）是一种通过提问和回答来推理事
  件真相的游戏。主持人知道完整故事，玩家只能问
  能用"是/否"回答的问题。

关于本系统：
  本系统使用本地运行的Ollama大语言模型作为游戏
  主持人，完全离线运行，保护隐私。

快速开始：
  1. 确保Ollama已安装并运行
  2. 安装至少一个模型（如 llama3）
  3. 选择"开始新游戏"
  4. 通过提问推理真相！

常用CLI命令：
  ollama serve          启动Ollama服务
  ollama pull <model>   安装模型
  ollama list           查看已安装模型
  python turtle_soup.py 启动游戏系统
        """
        print(help_text)
    
    def main_loop(self):
        """主循环"""
        self.display_banner()
        
        # 初始化系统
        if not self.engine.initialize():
            print("\n按任意键退出...")
            input()
            return
        
        while self.running:
            self.display_menu()
            choice = self.get_user_input("请选择操作: ")
            
            if choice == '1':
                self.run_new_game()
            elif choice == '2':
                self.run_settings()
            elif choice == '3':
                self.show_available_models()
            elif choice == '4':
                self.display_help()
            elif choice in ['5', 'quit', 'exit', 'q']:
                print("\n👋 感谢使用海龟汤游戏系统！再见！")
                self.running = False
            else:
                print("无效选择，请重新输入")


# ==================== 主程序入口 ====================

def main():
    """主函数"""
    
    # 默认配置
    ollama_config = OllamaConfig(
        host="http://localhost:11434",
        model="llama3",
        temperature=0.7,
        max_tokens=2048
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
                ollama_config.model = arg.split('=')[1]
            elif arg.startswith('--difficulty='):
                game_config.difficulty = arg.split('=')[1]
            elif arg.startswith('--host='):
                ollama_config.host = arg.split('=')[1]
            elif arg == '--help' or arg == '-h':
                print("""
用法: python turtle_soup_ollama.py [选项]

选项:
  --model=<模型名>       指定Ollama模型 (默认: llama3)
  --difficulty=<难度>    游戏难度: easy/medium/hard (默认: medium)
  --host=<地址>          Ollama服务地址 (默认: http://localhost:11434)
  --help, -h             显示此帮助信息

示例:
  python turtle_soup_ollama.py --model=mistral --difficulty=hard
  python turtle_soup_ollama.py --host=http://192.168.1.100:11434
                """)
                sys.exit(0)
    
    # 创建引擎和CLI
    engine = TurtleSoupEngine(ollama_config, game_config)
    cli = TurtleSoupCLI(engine)
    
    # 运行主循环
    try:
        cli.main_loop()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n[致命错误] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
