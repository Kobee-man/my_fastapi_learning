from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import json
import re
import uuid
from datetime import datetime

from core.llm_service import llm_service, LLMError
from core.redis_service import redis_service
from core.turtle_soup_judge import judge_answer

router = APIRouter(prefix="/turtle-soup", tags=["海龟汤游戏"])

# 游戏状态存储（玩家、提问记录等），题目背景存储在Redis
games_db: dict = {}
game_history: list = []


# ==================== 请求模型 ====================

class GameCreate(BaseModel):
    """创建游戏"""
    difficulty: str = Field(default="medium", description="难度：easy/medium/hard")
    max_questions: int = Field(default=20, ge=5, le=50, description="最大提问次数")
    max_players: int = Field(default=4, ge=1, le=10, description="最大玩家数")

class PlayerJoin(BaseModel):
    """玩家加入"""
    game_id: str
    player_username: str

class QuestionSubmit(BaseModel):
    """提交问题"""
    game_id: str
    question: str
    player_username: str

class AnswerJudge(BaseModel):
    """答案判断"""
    game_id: str
    answer: str
    player_username: str

class GameInvite(BaseModel):
    """游戏邀请"""
    game_id: str
    invitee_usernames: List[str]

class SinglePlayerJudge(BaseModel):
    """单人模式问题判断请求（汤底由后端管理，不从前端传入）"""
    game_id: str
    question: str
    question_history: List[str] = []


# ==================== Prompt 模板 ====================

def build_puzzle_prompt(difficulty: str) -> tuple[str, str]:
    """构建题目生成prompt（带CoT思维链）"""
    system = (
        "你是一个专业的海龟汤出题专家。\n"
        "先在<thinking>标签中构思谜题设计（人物、事件、转折点），"
        "然后用```json和```包裹输出JSON。\n"
        "JSON之外不要输出任何其他内容。"
    )
    prompt = f"""请生成一个{difficulty}难度的海龟汤谜题。

要求：
1. 情境(situation)：令人困惑但有合理解释的场景，2-4句话
2. 真相(truth)：完整的、逻辑自洽的解释，包含所有关键转折
3. 提示(hints)：3个递进式提示，从模糊到具体
4. 分类(category)：谜题的主题分类（如：日常生活、推理悬疑、黑色幽默等）

请按以下格式输出：

<thinking>
在此构思：
- 主要人物是谁？什么身份？
- 发生了什么事件？在哪里？
- 关键的转折点或隐藏信息是什么？
- 为什么情境看起来矛盾？
</thinking>

```json
{{
    "title": "谜题标题（简短有趣）",
    "situation": "情境描述（2-4句话，制造悬念）",
    "truth": "完整真相（详细解释所有看似矛盾的细节）",
    "hints": ["提示1（模糊）", "提示2（中等）", "提示3（具体）"],
    "category": "分类"
}}
```"""
    return prompt, system


def build_question_judge_prompt(question: str, situation: str, truth: str, question_history: list = None) -> tuple[str, str]:
    """构建问题判断prompt（带CoT思维链）"""
    history_text = ""
    if question_history:
        recent = question_history[-5:]
        history_text = "\n".join([f"- {q}" for q in recent])
    else:
        history_text = "无"

    system = ""
    prompt = f"""# 角色设定
你是一位经验丰富的海龟汤（情境推理）游戏裁判。你的职责是严格、准确、一致地判断玩家的问题。

# 核心原则（必须遵守）
1. **准确性优先**：基于真相内容进行事实性判断，不允许猜测或模糊回答
2. **逻辑连贯**：同一局游戏中，对相似问题的回答必须保持一致
3. **二元约束**：只能回答"是"、"否"或"无关"，绝对不能输出其他内容
4. **相关性检测**：只有与真相核心要素直接相关的问题才值得回答

# 游戏信息
- 情境描述：{situation}
- 完整真相：{truth}

# 待判断问题
玩家问题：{question}

# 历史上下文
之前的问题记录：
{history_text}

# 判断流程（请按此步骤思考）

## 第一步：相关性分析
检查问题是否涉及以下要素：
- 人物身份、状态、行为
- 事件发生的时间、地点、原因
- 物品的存在、用途、关系
- 情境中明确提到的任何具体细节

如果问题过于抽象、与情境无关、或无法用是/否回答 → 标记为"无关"

## 第二步：事实匹配
将问题中的关键词/实体与真相进行精确比对：
1. 提取问题的主语和谓语
2. 在真相中查找对应的事实陈述
3. 判断该事实是否存在/发生

## 第三步：逻辑推理
基于匹配结果，严格按照真相内容推导答案：
- 如果问题描述的情况在真相中明确存在 → 回答"是"
- 如果问题描述的情况在真相中明确不存在或被否定 → 回答"否"
- 如果真相中没有足够信息支持判断 → 回答"无关"

## 第四步：一致性校验
思考：如果之前有类似的问题，我的回答是否会产生矛盾？
- 如果可能矛盾，重新审视判断依据
- 确保本次回答可以经受后续追问的检验

# 输出要求
用```json和```包裹，**严格JSON格式**（不要添加其他文字）：

```json
{{
    "is_relevant": true/false,
    "answer": "是"/"否"/"无关",
    "reason": "简短明确的判断依据（15-30字），说明为什么得出这个结论",
    "confidence": 0.7-1.0,
    "reasoning_steps": ["第一步的分析结果", "第二步的匹配结果", "第三步的推理过程"]
}}
```

# ⚠️ 警告
- 不要试图"帮助"玩家而放宽标准
- 不要输出"可能是"、"大概是"等模糊表述
- 如果无法确定，宁可回答"无关"也不要猜测
- answer字段的值必须是且只能是："是"、"否"、"无关" 这三个字符串之一
"""
    return prompt, system


def build_answer_check_prompt(answer: str, situation: str, truth: str) -> tuple[str, str]:
    """构建答案检查prompt（带CoT思维链）"""
    system = ""
    prompt = f"""# 角色设定
你是一位严谨的海龟汤游戏裁判，负责评估玩家推理出的答案是否正确揭示了真相。

# 评估标准（多维度分析）

## 1. 核心要素覆盖率 (权重: 40%)
检查玩家的答案是否包含了以下关键信息：
- **人物**：涉及的所有角色及其身份/关系
- **事件**：发生了什么、如何发生的
- **原因**：为什么发生、动机是什么
- **结果**：最终的结局或状态

每个要素必须准确无误才能得分。

## 2. 逻辑连贯性 (权重: 30%)
评估答案是否：
- 能够合理解释情境中的所有细节
- 不存在自相矛盾的陈述
- 因果关系清晰合理

## 3. 表述精确度 (权重: 20%)
- 关键事实必须准确（人名、物品、动作等）
- 允许合理的同义词替换（如"死亡"="去世"）
- 时间顺序和空间关系要正确

## 4. 完整性 (权重: 10%)
- 是否遗漏了重要情节转折
- 是否解释了情境中看似矛盾的地方

# 游戏信息
- 情境描述：{situation}
- 正确真相：{truth}

# 待评估答案
玩家的答案：{answer}

# 评估流程

## 步骤1：拆解真相为关键事实单元
将完整真相分解为5-8个不可遗漏的关键事实点。

## 步骤2：逐一比对
检查玩家的答案是否覆盖了每个关键事实点：
- 完全匹配（100%得分）
- 部分匹配/表述不同但意思对（70%得分）
- 缺失或错误（0%得分）

## 步骤3：逻辑一致性验证
思考：如果这个答案是正确的，能否完美解释情境？是否存在逻辑漏洞？

## 步骤4：综合评分
根据四个维度的加权得分，给出最终判定。

# 输出要求
用```json和```包裹，**严格JSON格式**：

```json
{{
    "is_correct": true/false,
    "accuracy": 0.0-1.0 (保留2位小数),
    "dimension_scores": {{
        "core_elements": 0.0-1.0,
        "logic_coherence": 0.0-1.0,
        "precision": 0.0-1.0,
        "completeness": 0.0-1.0
    }},
    "matched_facts": ["已正确识别的事实1", "已正确识别的事实2"],
    "missing_facts": ["缺失的关键事实1", "缺失的关键事实2"],
    "incorrect_claims": ["错误的陈述1（如有）"],
    "feedback": "详细反馈（50-150字），包括：肯定正确的部分 + 指出缺失/错误的部分 + 改进建议"
}}
```

# 判定阈值
- accuracy >= 0.85 → is_correct: true（优秀）
- accuracy >= 0.70 且 < 0.85 → is_correct: true（良好，允许小瑕疵）
- accuracy < 0.70 → is_correct: false（需要继续推理）

# ⚠️ 重要提醒
- 不要"放水"：即使答案接近，如果缺少核心要素也必须标记为不正确
- 反馈要有建设性：指出具体哪里对了、哪里错了、下一步该往哪个方向思考
- accuracy评分要客观公正，不要受答案长度或华丽程度影响
"""
    return prompt, system


# ==================== JSON解析 ====================

def _extract_brace_block(text: str) -> Optional[str]:
    """用括号计数法提取最外层 { ... } 块"""
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def _fix_json_issues(raw: str) -> str:
    """修复常见JSON问题"""
    # 移除尾部逗号: }, ] 之前
    raw = re.sub(r',\s*([}\]])', r'\1', raw)
    return raw


def parse_llm_json(text: str) -> Optional[dict]:
    """从LLM响应中解析JSON，多策略降级"""
    if not text or not text.strip():
        return None

    cleaned = text.strip()

    # 1. 去除 <thinking>...</thinking> 标签
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.DOTALL)

    # 2. 去除markdown代码块: ```json ... ``` 或 ``` ... ```
    cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned.strip())
    cleaned = re.sub(r'\n?```\s*$', '', cleaned.strip())

    # 3. 去除 json\n / JSON: 前缀（Ollama 常见）
    cleaned = re.sub(r'^\s*(?:json|JSON)\s*:?\s*\n?', '', cleaned)

    # 4. 直接尝试解析
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 5. 括号计数法提取
    block = _extract_brace_block(cleaned)
    if block:
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            pass
        # 6. 修复常见问题后重试
        try:
            return json.loads(_fix_json_issues(block))
        except json.JSONDecodeError:
            pass

    return None


# ==================== 辅助函数 ====================

def get_game_puzzle(game_id: str) -> Optional[dict]:
    """获取游戏的题目数据（优先内存缓存，降级Redis）"""
    game = games_db.get(game_id)
    if game:
        cached = game.get("_puzzle_cache")
        if cached:
            return cached
    return redis_service.get_puzzle(game_id)


def get_next_hint(game: dict) -> Optional[str]:
    """获取下一个提示"""
    puzzle = game.get("_puzzle_cache") or {}
    hints = puzzle.get("hints", [])
    if hints and game["hints_used"] < len(hints):
        hint = hints[game["hints_used"]]
        game["hints_used"] += 1
        return hint
    return None


def calculate_duration(start_time: str, end_time: str) -> str:
    """计算游戏时长"""
    if start_time and end_time:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        duration = end - start
        minutes = int(duration.total_seconds() // 60)
        seconds = int(duration.total_seconds() % 60)
        return f"{minutes}分{seconds}秒"
    return "未知"


# ==================== API 端点 ====================

@router.post("/check-status")
async def check_llm_status(deep: bool = False):
    """检查LLM服务状态"""
    available = llm_service.is_available()
    redis_ok = redis_service.is_available()
    llm_reachable = None
    if deep and available:
        llm_reachable = await llm_service.ping()

    return {
        "status": "ok",
        "llm_available": available,
        "llm_reachable": llm_reachable,
        "llm_mode": llm_service.mode,
        "redis_available": redis_ok,
        "message": f"LLM服务正常（{llm_service.mode}模式）" if available else "LLM服务不可用，请检查配置",
    }


@router.post("/create-game")
async def create_game(game_data: GameCreate):
    """创建新游戏 - 完全由LLM生成题目（汤底仅存后端）"""
    if not llm_service.is_available():
        raise HTTPException(status_code=503, detail="LLM服务不可用，无法生成题目")

    game_id = f"game_{uuid.uuid4().hex[:8]}"

    # LLM生成题目（最多重试2次）
    puzzle_data = None
    last_error = None
    for attempt in range(2):
        try:
            prompt, system = build_puzzle_prompt(game_data.difficulty)
            response = await llm_service.chat(prompt, system, temperature=0.6)
            parsed = parse_llm_json(response)
            if not parsed:
                last_error = f"第{attempt+1}次：无法从LLM响应中解析JSON"
                continue
            if not parsed.get("situation") or not parsed.get("truth"):
                last_error = f"第{attempt+1}次：缺少situation或truth字段（得到的keys: {list(parsed.keys())}）"
                continue
            # 补全可选字段
            parsed.setdefault("title", "未命名谜题")
            parsed.setdefault("hints", [])
            parsed.setdefault("category", "未分类")
            parsed["id"] = f"llm_{uuid.uuid4().hex[:8]}"
            parsed.setdefault("difficulty", game_data.difficulty)
            puzzle_data = parsed
            break
        except LLMError as e:
            raise HTTPException(status_code=503, detail=f"LLM生成题目失败: {e}")

    if puzzle_data is None:
        raise HTTPException(status_code=500, detail=f"LLM生成的题目格式不正确，请重试。({last_error})")

    # 存入Redis（含汤底truth）
    redis_service.set_puzzle(game_id, puzzle_data)

    game = {
        "id": game_id,
        "status": "waiting",
        "settings": {
            "difficulty": game_data.difficulty,
            "max_questions": game_data.max_questions,
            "max_players": game_data.max_players
        },
        "players": [],
        "host": None,
        "questions": [],
        "current_question_count": 0,
        "hints_used": 0,
        "winner": None,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "finished_at": None,
        "_puzzle_cache": puzzle_data,
    }

    games_db[game_id] = game

    # 只返回汤面（situation），不返回汤底（truth）
    return {
        "success": True,
        "game_id": game_id,
        "puzzle_preview": {
            "title": puzzle_data.get("title", ""),
            "situation": puzzle_data["situation"],
            "hints": puzzle_data.get("hints", []),
            "difficulty": puzzle_data.get("difficulty", game_data.difficulty),
            "category": puzzle_data.get("category", ""),
        },
        "message": "游戏创建成功（LLM生成）"
    }


@router.post("/join-game")
async def join_game(join_data: PlayerJoin):
    """加入游戏"""
    game_id = join_data.game_id
    username = join_data.player_username

    if game_id not in games_db:
        raise HTTPException(status_code=404, detail="游戏不存在")

    game = games_db[game_id]

    if len(game["players"]) >= game["settings"]["max_players"]:
        raise HTTPException(status_code=400, detail="游戏已满员")

    if any(p["username"] == username for p in game["players"]):
        raise HTTPException(status_code=400, detail="你已经在游戏中了")

    player = {
        "username": username,
        "joined_at": datetime.now().isoformat(),
        "questions_asked": 0,
        "score": 0
    }

    game["players"].append(player)

    if len(game["players"]) == 1:
        game["host"] = username

    return {
        "success": True,
        "player_id": len(game["players"]) - 1,
        "current_players": len(game["players"]),
        "max_players": game["settings"]["max_players"],
        "message": f"{username} 加入了游戏"
    }


class StartGameRequest(BaseModel):
    """开始游戏请求"""
    game_id: str
    host_username: str


@router.post("/start-game")
async def start_game(req: StartGameRequest):
    """开始游戏"""
    game_id = req.game_id
    host_username = req.host_username
    if game_id not in games_db:
        raise HTTPException(status_code=404, detail="游戏不存在")

    game = games_db[game_id]

    if game["host"] != host_username:
        raise HTTPException(status_code=403, detail="只有房主可以开始游戏")

    if len(game["players"]) < 2:
        raise HTTPException(status_code=400, detail="至少需要2名玩家才能开始游戏")

    game["status"] = "playing"
    game["started_at"] = datetime.now().isoformat()

    puzzle = game.get("_puzzle_cache") or get_game_puzzle(game_id) or {}

    return {
        "success": True,
        "game_status": "playing",
        "puzzle": {
            "title": puzzle.get("title", ""),
            "situation": puzzle.get("situation", ""),
            "difficulty": puzzle.get("difficulty", ""),
        },
        "players": [p["username"] for p in game["players"]],
        "message": "游戏开始！"
    }


@router.post("/ask-question")
async def ask_question(question_data: QuestionSubmit):
    """提问 - LLM判断（带重试）"""
    game_id = question_data.game_id
    question = question_data.question.strip()
    username = question_data.player_username

    if game_id not in games_db:
        raise HTTPException(status_code=404, detail="游戏不存在")

    game = games_db[game_id]

    if game["status"] != "playing":
        raise HTTPException(status_code=400, detail="游戏未在进行中")

    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")

    if game["current_question_count"] >= game["settings"]["max_questions"]:
        raise HTTPException(status_code=400, detail="已达到最大提问次数")

    if not llm_service.is_available():
        raise HTTPException(status_code=503, detail="LLM服务不可用，无法判断问题")

    # 获取题目数据
    puzzle = game.get("_puzzle_cache") or get_game_puzzle(game_id)
    if not puzzle:
        raise HTTPException(status_code=500, detail="题目数据丢失")

    # 组装对话历史
    history_questions = [q["question"] for q in game["questions"]]
    if not history_questions:
        try:
            redis_history = redis_service.get_history(game_id)
            history_questions = [h["q"] for h in redis_history]
        except Exception:
            pass

    # LLM判断（带重试）
    truth = puzzle["truth"]
    situation = puzzle["situation"]
    prompt, _ = build_question_judge_prompt(question, situation, truth, history_questions)

    judgment = None
    last_error = None
    for attempt in range(2):
        try:
            response = await llm_service.chat(prompt, temperature=0.3)
            parsed = parse_llm_json(response)
            if parsed and "answer" in parsed:
                judgment = parsed
                break
            last_error = f"第{attempt+1}次：解析失败"
        except LLMError as e:
            raise HTTPException(status_code=503, detail=f"LLM判断失败: {e}")

    if judgment is None:
        raise HTTPException(status_code=500, detail=f"LLM返回格式异常，请重试。({last_error})")

    question_record = {
        "id": f"q_{len(game['questions']) + 1}",
        "question": question,
        "answer": judgment.get("answer", "是"),
        "is_relevant": judgment.get("is_relevant", True),
        "reason": judgment.get("reason", ""),
        "player": username,
        "timestamp": datetime.now().isoformat()
    }

    game["questions"].append(question_record)
    game["current_question_count"] += 1

    for player in game["players"]:
        if player["username"] == username:
            player["questions_asked"] += 1
            break

    # 写入Redis历史
    try:
        redis_service.append_history(
            game_id, question,
            judgment.get("answer", "是"),
            judgment.get("reason", "")
        )
    except Exception:
        pass

    return {
        "success": True,
        "judgment": judgment,
        "remaining_questions": game["settings"]["max_questions"] - game["current_question_count"],
        "total_questions": game["current_question_count"],
        "message": f"第 {game['current_question_count']} 个问题已回答"
    }


@router.post("/submit-answer")
async def submit_answer(answer_data: AnswerJudge):
    """提交最终答案 - LLM判断（带重试，支持单人模式）"""
    game_id = answer_data.game_id
    answer = answer_data.answer.strip()
    username = answer_data.player_username

    if game_id not in games_db:
        raise HTTPException(status_code=404, detail="游戏不存在")

    game = games_db[game_id]

    # 允许 waiting（单人模式）和 playing（多人模式）
    if game["status"] not in ("playing", "waiting"):
        raise HTTPException(status_code=400, detail="游戏未在进行中")

    # 单人模式自动开始
    if game["status"] == "waiting":
        game["status"] = "playing"
        game["started_at"] = datetime.now().isoformat()

    if not answer:
        raise HTTPException(status_code=400, detail="答案不能为空")

    if not llm_service.is_available():
        raise HTTPException(status_code=503, detail="LLM服务不可用，无法判断答案")

    # 获取题目数据
    puzzle = game.get("_puzzle_cache") or get_game_puzzle(game_id)
    if not puzzle:
        raise HTTPException(status_code=500, detail="题目数据丢失")

    # LLM判断（带重试）
    truth = puzzle["truth"]
    situation = puzzle["situation"]
    prompt, _ = build_answer_check_prompt(answer, situation, truth)

    result = None
    last_error = None
    for attempt in range(2):
        try:
            response = await llm_service.chat(prompt, temperature=0.3)
            parsed = parse_llm_json(response)
            if parsed and "is_correct" in parsed:
                result = parsed
                break
            last_error = f"第{attempt+1}次：解析失败"
        except LLMError as e:
            raise HTTPException(status_code=503, detail=f"LLM判断失败: {e}")

    if result is None:
        raise HTTPException(status_code=500, detail=f"LLM返回格式异常，请重试。({last_error})")

    if result.get("is_correct"):
        game["status"] = "finished"
        game["winner"] = username
        game["finished_at"] = datetime.now().isoformat()

        for player in game["players"]:
            if player["username"] == username:
                player["score"] += 100
                break

        history_entry = {
            "game_id": game_id,
            "puzzle_title": puzzle.get("title", ""),
            "winner": username,
            "players": [p["username"] for p in game["players"]],
            "duration": calculate_duration(game["started_at"], game["finished_at"]),
            "questions_count": game["current_question_count"],
            "finished_at": game["finished_at"]
        }
        game_history.append(history_entry)

        # 清理Redis
        redis_service.delete_puzzle(game_id)
        try:
            redis_service.delete_history(game_id)
        except Exception:
            pass

        return {
            "success": True,
            "is_correct": True,
            "result": result,
            "winner": username,
            "truth": truth,
            "message": "恭喜！答案正确！"
        }
    else:
        return {
            "success": True,
            "is_correct": False,
            "result": result,
            "hint": get_next_hint(game),
            "message": "答案不对哦，再想想~"
        }


@router.post("/judge-question")
async def judge_single_player_question(judge_data: SinglePlayerJudge):
    """单人模式：LLM判断问题（汤底从后端获取）"""
    if not judge_data.question or not judge_data.game_id:
        raise HTTPException(status_code=400, detail="问题和游戏ID不能为空")

    if not llm_service.is_available():
        raise HTTPException(status_code=503, detail="LLM服务不可用")

    # 从后端获取汤底
    puzzle = get_game_puzzle(judge_data.game_id)
    if not puzzle:
        raise HTTPException(status_code=404, detail="题目数据不存在或已过期")

    truth = puzzle["truth"]
    situation = puzzle["situation"]

    # 组装对话历史（前端传入 + Redis补充）
    redis_history = []
    try:
        redis_history = redis_service.get_history(judge_data.game_id)
    except Exception:
        pass
    redis_questions = [h["q"] for h in redis_history]
    all_history = judge_data.question_history if len(judge_data.question_history) > len(redis_questions) else redis_questions

    # LLM判断（带重试）
    prompt, _ = build_question_judge_prompt(judge_data.question, situation, truth, all_history)

    judgment = None
    last_error = None
    for attempt in range(2):
        try:
            response = await llm_service.chat(prompt, temperature=0.3)
            parsed = parse_llm_json(response)
            if parsed and "answer" in parsed:
                judgment = parsed
                break
            last_error = f"第{attempt+1}次：解析失败"
        except LLMError as e:
            raise HTTPException(status_code=503, detail=f"LLM判断失败: {e}")

    if judgment is None:
        raise HTTPException(status_code=500, detail=f"LLM返回格式异常，请重试。({last_error})")

    # 写入Redis历史
    try:
        redis_service.append_history(
            judge_data.game_id,
            judge_data.question,
            judgment.get("answer", "是"),
            judgment.get("reason", "")
        )
    except Exception:
        pass

    # 同步到内存（如果game存在）
    game = games_db.get(judge_data.game_id)
    if game:
        question_record = {
            "id": f"q_{len(game['questions']) + 1}",
            "question": judge_data.question,
            "answer": judgment.get("answer", "是"),
            "is_relevant": judgment.get("is_relevant", True),
            "reason": judgment.get("reason", ""),
            "player": "single_player",
            "timestamp": datetime.now().isoformat()
        }
        game["questions"].append(question_record)
        game["current_question_count"] += 1

    return {
        "success": True,
        "judgment": judgment,
        "message": "问题已通过AI智能判断"
    }


class JudgeAnswerRequest(BaseModel):
    """语义判官请求"""
    story: str = Field(..., description="故事/汤底内容")
    question: str = Field(..., description="玩家提问")


@router.post("/semantic-judge")
async def semantic_judge(req: JudgeAnswerRequest):
    """语义判官：低Token消耗的智能判断"""
    result = await judge_answer(req.story, req.question)
    return {"success": True, "judgment": result}


@router.get("/hint")
async def get_hint(game_id: str):
    """获取提示"""
    if game_id not in games_db:
        raise HTTPException(status_code=404, detail="游戏不存在")

    game = games_db[game_id]
    hint = get_next_hint(game)

    puzzle = game.get("_puzzle_cache") or get_game_puzzle(game_id) or {}

    if hint:
        return {
            "success": True,
            "hint": hint,
            "hints_remaining": len(puzzle.get("hints", [])) - game["hints_used"]
        }
    else:
        return {"success": False, "message": "没有更多提示了"}


@router.get("/game-status/{game_id}")
async def get_game_status(game_id: str):
    """获取游戏状态"""
    if game_id not in games_db:
        raise HTTPException(status_code=404, detail="游戏不存在")

    game = games_db[game_id]
    puzzle = game.get("_puzzle_cache") or get_game_puzzle(game_id) or {}

    return {
        "game_id": game_id,
        "status": game["status"],
        "puzzle": {
            "title": puzzle.get("title", ""),
            "situation": puzzle.get("situation", "") if game["status"] != "waiting" else None,
            "truth": puzzle.get("truth", "") if game["status"] == "finished" else None,
            "difficulty": puzzle.get("difficulty", ""),
            "hints_used": game["hints_used"],
            "total_hints": len(puzzle.get("hints", []))
        },
        "players": game["players"],
        "settings": game["settings"],
        "questions_count": game["current_question_count"],
        "recent_questions": game["questions"][-5:] if game["questions"] else [],
        "winner": game["winner"],
        "created_at": game["created_at"],
        "started_at": game["started_at"],
        "finished_at": game["finished_at"]
    }


@router.post("/invite")
async def send_invite(invite_data: GameInvite):
    """发送游戏邀请"""
    game_id = invite_data.game_id

    if game_id not in games_db:
        raise HTTPException(status_code=404, detail="游戏不存在")

    game = games_db[game_id]
    puzzle = game.get("_puzzle_cache") or get_game_puzzle(game_id) or {}

    invites_sent = []
    for username in invite_data.invitee_usernames:
        invites_sent.append({
            "to": username,
            "game_id": game_id,
            "game_title": puzzle.get("title", ""),
            "host": game["host"],
            "status": "pending"
        })

    return {
        "success": True,
        "invites_sent": len(invites_sent),
        "invited_users": invite_data.invitee_usernames,
        "message": f"已向 {len(invites_sent)} 位玩家发送邀请"
    }


@router.get("/history")
async def get_game_history(limit: int = 10):
    """获取游戏历史记录"""
    recent_history = sorted(game_history, key=lambda x: x.get("finished_at", ""), reverse=True)[:limit]

    return {
        "success": True,
        "count": len(recent_history),
        "history": recent_history
    }


@router.delete("/game/{game_id}")
async def delete_game(game_id: str):
    """删除游戏"""
    if game_id not in games_db:
        raise HTTPException(status_code=404, detail="游戏不存在")

    del games_db[game_id]
    redis_service.delete_puzzle(game_id)
    try:
        redis_service.delete_history(game_id)
    except Exception:
        pass

    return {"success": True, "message": "游戏已删除"}


@router.get("/rules")
async def get_rules():
    """获取游戏规则"""
    return {
        "rules": """
## 海龟汤游戏规则

### 游戏目标
通过提问"是/否"问题来推断出一个完整故事的真相。

### 游戏流程
1. **出题**：AI自动生成一个令人困惑的**情境**
2. **提问**：玩家轮流提出只能用"是"、"否"、"无关"回答的问题
3. **推理**：根据问题的答案逐步还原真相
4. **猜真相**：当你认为已经知道真相时，可以提出你的完整解答

### 提问规则
- 问题必须能用"是"、"否"、"无关"来回答
- 不能直接问"真相是什么"
- 每个玩家每次只能问一个问题
- 有提问次数限制

### 获胜条件
- 第一个正确说出完整真相的玩家获胜
- 答案需要包含故事的关键要素

### 示例
**情境**：一个人走进酒吧，要了一杯水，酒保拿出一把枪指着他。那个人说"谢谢"，然后离开了。

**真相**：这个人在打嗝，他听说被枪吓到能治好打嗝，所以让酒保吓他一下。

### 注意事项
- 这是一个推理游戏，发挥想象力！
- 善于利用排除法
- 注意细节，每个细节都可能是线索
        """,
        "tips": [
            "从'为什么'开始提问往往更有效",
            "注意时间、地点、人物关系等关键要素",
            "如果卡住了，可以使用提示功能",
            "真相往往比想象的更简单"
        ]
    }
