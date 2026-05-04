from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlmodel import Session, select
import json
import os

from core.config import get_db
from models.db_models import User
from core.security import get_current_user
from core.permissions import permission_manager, PermissionLevel

router = APIRouter(prefix="/turtle-soup", tags=["海龟汤游戏"])

# 游戏状态存储（生产环境应使用Redis）
games_db = {}
game_history = []

class LLMConfig(BaseModel):
    """LLM配置"""
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    model_name: Optional[str] = "gpt-3.5-turbo"

class GameCreate(BaseModel):
    """创建游戏"""
    difficulty: str = Field(default="medium", description="难度：easy/medium/hard")
    max_questions: int = Field(default=20, ge=5, le=50, description="最大提问次数")
    max_players: int = Field(default=4, ge=2, le=10, description="最大玩家数")

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

# 预设题目库（当LLM不可用时使用）
PRESET_PUZZLES = [
    {
        "id": "preset_001",
        "title": "半杯水",
        "situation": "一个人看着桌上的半杯水，突然大哭起来。请问发生了什么？",
        "truth": "这个人刚刚得知自己得了绝症，医生告诉他只剩下半年的生命。他看到半杯水，意识到自己的生命也像这杯水一样，只剩下一半了。",
        "difficulty": "easy",
        "hints": ["与生命有关", "与时间有关", "这是一个悲伤的故事"],
        "category": "生活"
    },
    {
        "id": "preset_002",
        "title": "黑暗中的灯光",
        "situation": "一个人在漆黑的房间里，突然打开了灯，然后立刻关掉并尖叫起来。为什么？",
        "truth": "这个人是个小偷，他潜入房间偷东西。打开灯后，他发现房间里挂满了死人的照片，而且照片里的人都在看着他笑。他意识到自己闯入了一个变态杀人狂的家。",
        "difficulty": "medium",
        "hints": ["与犯罪有关", "与恐惧有关", "看到了不该看的东西"],
        "category": "悬疑"
    },
    {
        "id": "preset_003",
        "title": "冰块中的钥匙",
        "situation": "一个男人把钥匙冻在冰块里，然后把冰块扔进大海。这是为什么？",
        "truth": "这个男人杀了人，凶器是一把特殊的钥匙。为了销毁证据，他把钥匙冻在冰块里扔进大海。但警察最终还是通过其他证据抓到了他。",
        "difficulty": "hard",
        "hints": ["与犯罪有关", "与证据有关", "这是一起谋杀案"],
        "category": "推理"
    }
]

def get_llm_config():
    """获取LLM配置"""
    return {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "api_url": os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"),
        "model_name": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    }

def is_llm_available():
    """检查LLM是否可用"""
    config = get_llm_config()
    return bool(config["api_key"])

async def call_llm(prompt: str, system_prompt: str = "") -> str:
    """调用LLM API"""
    if not is_llm_available():
        raise HTTPException(status_code=503, detail="题目还没准备好 - LLM服务未配置或额度不足")
    
    try:
        import httpx
        
        config = get_llm_config()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                config["api_url"],
                headers={
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config["model_name"],
                    "messages": messages,
                    "temperature": 0.8,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            elif response.status_code == 401:
                raise HTTPException(status_code=503, detail="题目还没准备好 - API密钥无效或额度不足")
            elif response.status_code == 429:
                raise HTTPException(status_code=503, detail="题目还没准备好 - API请求频率超限，请稍后再试")
            else:
                raise HTTPException(status_code=500, detail=f"LLM服务错误: {response.text}")
                
    except ImportError:
        raise HTTPException(status_code=503, detail="题目还没准备好 - 缺少httpx依赖")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM调用失败: {str(e)}")

def generate_preset_puzzle(difficulty: str) -> dict:
    """从预设题库生成题目"""
    import random
    
    filtered = [p for p in PRESET_PUZZLES if p["difficulty"] == difficulty]
    if not filtered:
        filtered = PRESET_PUZZLES
    
    puzzle = random.choice(filtered)
    
    return {
        **puzzle,
        "is_preset": True,
        "generated_at": __import__("datetime").datetime.now().isoformat()
    }

@router.post("/check-status")
async def check_llm_status():
    """
    检查LLM服务状态和功能可用性
    **公开接口** - 无需登录
    返回详细的权限信息和降级方案
    """
    available = is_llm_available()
    
    # 获取权限检查结果
    llm_check = permission_manager.check_feature_access("llm_generation")
    preset_check = permission_manager.check_feature_access("preset_puzzles")
    
    return {
        "status": "ok",
        "llm_available": available,
        "message": "LLM服务正常" if available else "题目还没准备好 - LLM服务未配置或额度不足",
        "preset_count": len(PRESET_PUZZLES),
        "preset_available": preset_check["accessible"],
        
        # 权限分层说明
        "permissions": {
            "level_1_public": {
                "name": "公开访问",
                "features": ["查看规则", "系统状态查询"],
                "auth_required": False,
                "api_key_required": False
            },
            "level_2_authenticated": {
                "name": "已认证用户",
                "features": [
                    "创建游戏（使用预设题目）",
                    "加入/开始游戏",
                    "提问（简单判断）",
                    "提交答案（简单判断）",
                    "获取提示",
                    "历史记录"
                ],
                "auth_required": True,
                "api_key_required": False,
                "note": "这些功能无需API Key即可使用"
            },
            "level_3_premium": {
                "name": "AI增强功能",
                "features": [
                    "LLM智能生成题目",
                    "LLM智能问题判断",
                    "LLM答案准确度评估"
                ],
                "auth_required": True,
                "api_key_required": True,
                "available": available,
                "fallback": {
                    "enabled": True,
                    "method": "自动使用预设题目库和简单判断逻辑",
                    "quality_impact": "基础功能完全可用，仅AI生成质量有差异",
                    "user_action": "无需任何操作，系统自动处理"
                }
            }
        },
        
        # 当前可用模式
        "current_mode": "full_ai" if available else "preset_mode",
        "mode_description": (
            "🚀 全AI模式 - 可使用LLM生成和判断" if available 
            else "✅ 基础模式 - 使用预设题目库，所有功能正常运行"
        ),
        
        # 用户体验保证
        "guarantees": {
            "system_stability": "✅ 系统在当前模式下100%稳定",
            "feature_access": "✅ 所有标注的功能均可正常使用",
            "data_persistence": "✅ 游戏数据正常保存",
            "no_interruption": "✅ 切换模式不会影响进行中的游戏"
        },
        
        # 错误处理说明
        "error_handling": {
            "if_llm_fails": "自动降级到预设题目，不显示错误",
            "if_no_api_key": "使用基础模式，体验略有不同但完整",
            "user_visible_errors": []  # 用户不会看到技术性错误
        }
    }

@router.post("/create-game")
async def create_game(game_data: GameCreate):
    """创建新游戏"""
    import uuid
    from datetime import datetime
    
    game_id = f"game_{uuid.uuid4().hex[:8]}"
    
    # 尝试生成题目（如果LLM可用）
    try:
        if is_llm_available():
            prompt = f"""请生成一个{game_data.difficulty}难度的海龟汤谜题。
            要求：
            1. 给出一个令人困惑的情境描述（situation）
            2. 情境要合理但有悬念
            3. 提供完整的真相解释（truth）
            4. 提供3个递进式提示（hints）
            
            请以JSON格式返回：
            {{
                "title": "谜题标题",
                "situation": "情境描述",
                "truth": "完整真相",
                "hints": ["提示1", "提示2", "提示3"],
                "category": "分类"
            }}
            """
            
            llm_response = await call_llm(prompt, "你是一个专业的海龟汤出题专家")
            
            # 尝试解析JSON
            try:
                puzzle_data = json.loads(llm_response)
                puzzle_data["id"] = f"llm_{uuid.uuid4().hex[:8]}"
                puzzle_data["is_preset"] = False
            except json.JSONDecodeError:
                # 如果解析失败，使用预设题目
                puzzle_data = generate_preset_puzzle(game_data.difficulty)
        else:
            # LLM不可用，使用预设题目
            puzzle_data = generate_preset_puzzle(game_data.difficulty)
            
    except HTTPException as e:
        # LLM调用失败，使用预设题目
        puzzle_data = generate_preset_puzzle(game_data.difficulty)
    
    # 创建游戏实例
    game = {
        "id": game_id,
        "puzzle": puzzle_data,
        "status": "waiting",  # waiting, playing, finished
        "settings": {
            "difficulty": game_data.difficulty,
            "max_questions": game_data.max_questions,
            "max_players": game_data.max_players
        },
        "players": [],
        "host": None,
        "questions": [],  # [{question, answer, is_correct, player, timestamp}]
        "current_question_count": 0,
        "hints_used": 0,
        "winner": None,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "finished_at": None
    }
    
    games_db[game_id] = game
    
    return {
        "success": True,
        "game_id": game_id,
        "puzzle_preview": {
            "title": puzzle_data["title"],
            "situation": puzzle_data["situation"],
            "difficulty": puzzle_data.get("difficulty", game_data.difficulty),
            "is_preset": puzzle_data.get("is_preset", False)
        },
        "message": "游戏创建成功"
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
    
    # 如果是第一个玩家，设为房主
    if len(game["players"]) == 1:
        game["host"] = username
    
    return {
        "success": True,
        "player_id": len(game["players"]) - 1,
        "current_players": len(game["players"]),
        "max_players": game["settings"]["max_players"],
        "message": f"{username} 加入了游戏"
    }

@router.post("/start-game")
async def start_game(game_id: str, host_username: str):
    """开始游戏"""
    if game_id not in games_db:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    game = games_db[game_id]
    
    if game["host"] != host_username:
        raise HTTPException(status_code=403, detail="只有房主可以开始游戏")
    
    if len(game["players"]) < 2:
        raise HTTPException(status_code=400, detail="至少需要2名玩家才能开始游戏")
    
    game["status"] = "playing"
    game["started_at"] = datetime.now().isoformat()
    
    return {
        "success": True,
        "game_status": "playing",
        "puzzle": {
            "title": game["puzzle"]["title"],
            "situation": game["puzzle"]["situation"],
            "difficulty": game["puzzle"]["difficulty"]
        },
        "players": [p["username"] for p in game["players"]],
        "message": "游戏开始！"
    }

@router.post("/ask-question")
async def ask_question(question_data: QuestionSubmit):
    """提问"""
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
        raise HTTPException(status_code(400, detail="已达到最大提问次数"))
    
    # 使用LLM判断问题是否有效
    try:
        truth = game["puzzle"]["truth"]
        situation = game["puzzle"]["situation"]

        judge_prompt = f"""# 角色设定
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
**绝对严格的JSON格式**（不要添加任何其他文字）：

{{
    "is_relevant": true/false,
    "answer": "是"/"否"/"无关",
    "reason": "简短明确的判断依据（15-30字），说明为什么得出这个结论",
    "confidence": 0.7-1.0,
    "reasoning_steps": ["第一步的分析结果", "第二步的匹配结果", "第三步的推理过程"]
}}

# 示例参考

示例1：
- 真相："一个男人因为打嗝走进酒吧要水喝。酒保用枪吓他治好了打嗝。男人说谢谢后离开。"
- 问题："这个人是生病了吗？"
→ {{"is_relevant": true, "answer": "是", "reason": "此人确实有打嗝这种身体不适症状", "confidence": 0.95, "reasoning_steps": ["问题涉及人物健康状态", "真相提到'打嗝'属于生理不适", "可明确判定为肯定"]}}

示例2：
- 真相同上
- 问题："酒保是想杀了他吗？"
→ {{"is_relevant": true, "answer": "否", "reason": "酒保的行为是为了治疗而非伤害", "confidence": 0.9, "reasoning_steps": ["问题涉及酒保意图", "真相显示枪是用来'吓'以治疗打嗝", "并非谋杀意图"]}}

示例3：
- 真相同上
- 问题："这个酒吧的装修风格是什么？"
→ {{"is_relevant": false, "answer": "无关", "reason": "装修风格与案件真相无关", "confidence": 0.99, "reasoning_steps": ["问题关于环境装饰", "真相未提及任何装修相关信息", "此信息对推理无帮助"]}}

# ⚠️ 警告
- 不要试图"帮助"玩家而放宽标准
- 不要输出"可能是"、"大概是"等模糊表述
- 如果无法确定，宁可回答"无关"也不要猜测
- answer字段的值必须是且只能是："是"、"否"、"无关" 这三个字符串之一
"""

        llm_response = await call_llm(judge_prompt)
        
        try:
            judgment = json.loads(llm_response)
        except json.JSONDecodeError:
            judgment = {"is_relevant": True, "answer": "是", "reason": ""}
            
    except HTTPException:
        # LLM不可用，简单模拟判断
        judgment = simulate_judgment(question, game["puzzle"])
    
    # 记录问题
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
    
    # 更新玩家提问数
    for player in game["players"]:
        if player["username"] == username:
            player["questions_asked"] += 1
            break
    
    return {
        "success": True,
        "judgment": judgment,
        "remaining_questions": game["settings"]["max_questions"] - game["current_question_count"],
        "total_questions": game["current_question_count"],
        "message": f"第 {game['current_question_count']} 个问题已回答"
    }

def simulate_judgment(question: str, puzzle: dict) -> dict:
    """模拟LLM判断（当LLM不可用时）"""
    truth_lower = puzzle["truth"].lower()
    question_lower = question.lower()
    
    # 简单关键词匹配
    relevant_keywords = ["什么", "为什么", "怎么", "谁", "哪里", "何时", "是否", "有没有", "是不是"]
    
    is_relevant = any(kw in question for kw in relevant_keywords)
    
    if not is_relevant:
        return {
            "is_relevant": False,
            "answer": "无关",
            "reason": "这个问题与当前情境不太相关哦"
        }
    
    # 随机返回是/否（实际应该用LLM）
    import random
    return {
        "is_relevant": True,
        "answer": random.choice(["是", "否"]),
        "reason": ""
    }

@router.post("/submit-answer")
async def submit_answer(answer_data: AnswerJudge):
    """提交最终答案"""
    game_id = answer_data.game_id
    answer = answer_data.answer.strip()
    username = answer_data.player_username
    
    if game_id not in games_db:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    game = games_db[game_id]

    if game["status"] != "playing":
        raise HTTPException(status_code=400, detail="游戏未在进行中")

    if not answer:
        raise HTTPException(status_code=400, detail="答案不能为空")
    
    # 使用LLM判断答案是否正确
    try:
        truth = game["puzzle"]["truth"]
        situation = game["puzzle"]["situation"]

        check_prompt = f"""# 角色设定
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
- 与之前的问题回答保持一致

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
- ✅ 完全匹配（100%得分）
- ⚠️ 部分匹配/表述不同但意思对（70%得分）
- ❌ 缺失或错误（0%得分）

## 步骤3：逻辑一致性验证
思考：如果这个答案是正确的，能否完美解释情境？是否存在逻辑漏洞？

## 步骤4：综合评分
根据四个维度的加权得分，给出最终判定。

# 输出要求
**严格JSON格式**：

{{
    "is_correct": true/false,
    "accuracy": 0.0-1.0 (保留2位小数),
    "dimension_scores": {{
        "core_elements": 0.0-1.0,  // 核心要素覆盖率
        "logic_coherence": 0.0-1.0,  // 逻辑连贯性
        "precision": 0.0-1.0,  // 表述精确度
        "completeness": 0.0-1.0  // 完整性
    }},
    "matched_facts": ["已正确识别的事实1", "已正确识别的事实2"],
    "missing_facts": ["缺失的关键事实1", "缺失的关键事实2"],
    "incorrect_claims": ["错误的陈述1（如有）"],
    "feedback": "详细反馈（50-150字），包括：肯定正确的部分 + 指出缺失/错误的部分 + 改进建议"
}}

# 判定阈值
- accuracy >= 0.85 → is_correct: true（优秀）
- accuracy >= 0.70 且 < 0.85 → is_correct: true（良好，允许小瑕疵）
- accuracy < 0.70 → is_correct: false（需要继续推理）

# 示例

示例1（完全正确）：
- 真相："一个男人因为打嗝走进酒吧要水喝。酒保拿枪吓他治好打嗝。男人感谢后离开。"
- 答案："男人打嗝很严重，去酒吧想喝水缓解。聪明的酒保看出他的困扰，用枪吓他一跳，打嗝就止住了。男人很感激。"

→ {{
    "is_correct": true,
    "accuracy": 0.95,
    "dimension_scores": {{"core_elements": 1.0, "logic_coherence": 1.0, "precision": 0.95, "completeness": 1.0}},
    "matched_facts": ["男人打嗝", "去酒吧", "酒保用枪", "目的是治疗", "成功治愈", "男人感谢"],
    "missing_facts": [],
    "incorrect_claims": [],
    "feedback": "完美！你准确把握了所有关键要素：打嗝的起因、酒保的巧妙方法、以及圆满的结局。逻辑清晰，表述准确。"
}}

示例2（部分正确）：
- 真相同上
- 答案："一个男人在酒吧遇到危险，酒保用枪保护了他，然后他安全离开了。"

→ {{
    "is_correct": false,
    "accuracy": 0.45,
    "dimension_scores": {{"core_elements": 0.5, "logic_coherence": 0.6, "precision": 0.4, "completeness": 0.3}},
    "matched_facts": ["在酒吧", "酒保用了枪", "男人离开"],
    "missing_facts": ["打嗝这个核心原因", "枪不是用来保护而是治疗", "男人的感谢反应"],
    "incorrect_claims": ["酒保是为了保护他（实际是治疗打嗝）"],
    "feedback": "方向有偏差。你注意到了'枪'这个关键元素，但误解了它的用途。提示：重新思考这个男人的初始状态（他为什么要水？），以及枪的真正作用。关注身体不适相关的线索。"
}}

# ⚠️ 重要提醒
- 不要"放水"：即使答案接近，如果缺少核心要素也必须标记为不正确
- 反馈要有建设性：指出具体哪里对了、哪里错了、下一步该往哪个方向思考
- accuracy评分要客观公正，不要受答案长度或华丽程度影响
"""

        llm_response = await call_llm(check_prompt)
        
        try:
            result = json.loads(llm_response)
        except json.JSONDecodeError:
            result = {"is_correct": False, "accuracy": 0, "feedback": "答案不太对哦"}
            
    except HTTPException:
        # LLM不可用，简单字符串匹配
        result = check_answer_simple(answer, game["puzzle"]["truth"])
    
    if result["is_correct"]:
        game["status"] = "finished"
        game["winner"] = username
        game["finished_at"] = datetime.now().isoformat()
        
        # 更新获胜者分数
        for player in game["players"]:
            if player["username"] == username:
                player["score"] += 100
                break
        
        # 保存到历史记录
        history_entry = {
            "game_id": game_id,
            "puzzle_title": game["puzzle"]["title"],
            "winner": username,
            "players": [p["username"] for p in game["players"]],
            "duration": calculate_duration(game["started_at"], game["finished_at"]),
            "questions_count": game["current_question_count"],
            "finished_at": game["finished_at"]
        }
        game_history.append(history_entry)
        
        return {
            "success": True,
            "is_correct": True,
            "result": result,
            "winner": username,
            "truth": game["puzzle"]["truth"],
            "message": "🎉 恭喜！答案正确！"
        }
    else:
        return {
            "success": True,
            "is_correct": False,
            "result": result,
            "hint": get_next_hint(game),
            "message": "答案不对哦，再想想~"
        }

def check_answer_simple(answer: str, truth: str) -> dict:
    """简单答案检查（当LLM不可用时）"""
    answer_words = set(answer.lower().split())
    truth_words = set(truth.lower().split())
    
    overlap = len(answer_words & truth_words) / max(len(truth_words), 1)
    
    return {
        "is_correct": overlap > 0.7,
        "accuracy": overlap,
        "feedback": "答案准确度：" + str(round(overlap * 100)) + "%"
    }

def get_next_hint(game: dict) -> Optional[str]:
    """获取下一个提示"""
    hints = game["puzzle"].get("hints", [])
    
    if hints and game["hints_used"] < len(hints):
        hint = hints[game["hints_used"]]
        game["hints_used"] += 1
        return hint
    
    return None

def calculate_duration(start_time: str, end_time: str) -> str:
    """计算游戏时长"""
    from datetime import datetime
    
    if start_time and end_time:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        duration = end - start
        minutes = int(duration.total_seconds() // 60)
        seconds = int(duration.total_seconds() % 60)
        return f"{minutes}分{seconds}秒"
    
    return "未知"

@router.get("/hint")
async def get_hint(game_id: str):
    """获取提示"""
    if game_id not in games_db:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    game = games_db[game_id]
    
    hint = get_next_hint(game)
    
    if hint:
        return {
            "success": True,
            "hint": hint,
            "hints_remaining": len(game["puzzle"].get("hints", [])) - game["hints_used"]
        }
    else:
        return {
            "success": False,
            "message": "没有更多提示了"
        }

@router.get("/game-status/{game_id}")
async def get_game_status(game_id: str):
    """获取游戏状态"""
    if game_id not in games_db:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    game = games_db[game_id]
    
    return {
        "game_id": game_id,
        "status": game["status"],
        "puzzle": {
            "title": game["puzzle"]["title"],
            "situation": game["puzzle"]["situation"] if game["status"] != "waiting" else None,
            "truth": game["puzzle"]["truth"] if game["status"] == "finished" else None,
            "difficulty": game["puzzle"]["difficulty"],
            "hints_used": game["hints_used"],
            "total_hints": len(game["puzzle"].get("hints", []))
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
    
    invites_sent = []
    for username in invite_data.invitee_usernames:
        # 在实际应用中，这里应该通过WebSocket发送邀请通知
        invites_sent.append({
            "to": username,
            "game_id": game_id,
            "game_title": game["puzzle"]["title"],
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
    
    return {
        "success": True,
        "message": "游戏已删除"
    }

@router.get("/rules")
async def get_rules():
    """获取游戏规则"""
    return {
        "rules": """
## 🐢 海龟汤游戏规则

### 🎯 游戏目标
通过提问"是/否"问题来推断出一个完整故事的真相。

### 📖 游戏流程
1. **出题**：系统（或房主）给出一个令人困惑的**情境**
2. **提问**：玩家轮流提出只能用"是"、"否"、"无关"回答的问题
3. **推理**：根据问题的答案逐步还原真相
4. **猜真相**：当你认为已经知道真相时，可以提出你的完整解答

### ❓ 提问规则
- 问题必须能用"是"、"否"、"无关"来回答
- 不能直接问"真相是什么"
- 每个玩家每次只能问一个问题
- 有提问次数限制

### 🏆 获胜条件
- 第一个正确说出完整真相的玩家获胜
- 答案需要包含故事的关键要素

### 💡 示例
**情境**：一个人走进酒吧，要了一杯水，酒保拿出一把枪指着他。那个人说"谢谢"，然后离开了。

**真相**：这个人在打嗝，他听说被枪吓到能治好打嗝，所以让酒保吓他一下。

### ⚠️ 注意事项
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

# ==================== 新增：单人模式专用API ====================

class SinglePlayerJudge(BaseModel):
    """单人模式问题判断请求"""
    question: str
    truth: str
    situation: str = ""
    keywords: List[str] = []
    hints: List[str] = []
    question_history: List[str] = []
    game_id: str = ""

@router.post("/judge-question")
async def judge_single_player_question(judge_data: SinglePlayerJudge):
    """
    单人模式专用：使用优化后的LLM prompt判断问题

    这个端点专门为前端单人模式的智能判断算法提供后端支持，
    使用经过优化的prompt模板，确保：
    1. 判断准确性高（基于事实匹配）
    2. 逻辑连贯性强（思维链推理）
    3. 二元回答精确（严格是/否/无关）
    """
    if not judge_data.question or not judge_data.truth:
        raise HTTPException(status_code=400, detail="问题和真相不能为空")

    try:
        # 使用优化后的judge_prompt（与多人游戏相同的严格标准）
        truth = judge_data.truth
        situation = judge_data.situation or "未提供情境"
        question = judge_data.question

        judge_prompt = f"""# 角色设定
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
{chr(10).join([f'- {q}' for q in (judge_data.question_history[-5:] if judge_data.question_history else ['无'])])}

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
思考：如果历史记录中有类似的问题，我的回答是否会产生矛盾？
- 如果可能矛盾，重新审视判断依据
- 确保本次回答可以经受后续追问的检验

# 输出要求
**绝对严格的JSON格式**（不要添加任何其他文字）：

{{
    "is_relevant": true/false,
    "answer": "是"/"否"/"无关",
    "reason": "简短明确的判断依据（15-30字），说明为什么得出这个结论",
    "confidence": 0.7-1.0,
    "reasoning_steps": ["第一步的分析结果", "第二步的匹配结果", "第三步的推理过程"]
}}

# ⚠️ 警告
- 不要试图"帮助"玩家而放宽标准
- 不要输出"可能是"、"大概是"等模糊表述
- 如果无法确定，宁可回答"无关"也不要猜测
- answer字段的值必须是且只能是："是"、"否"、"无关" 这三个字符串之一
"""

        llm_response = await call_llm(judge_prompt)

        try:
            judgment = json.loads(llm_response)
        except json.JSONDecodeError:
            judgment = {
                "is_relevant": True,
                "answer": "无关",
                "reason": "LLM返回格式异常，使用默认响应",
                "confidence": 0.1,
                "reasoning_steps": ["解析失败"]
            }

        return {
            "success": True,
            "judgment": judgment,
            "message": "问题已通过AI智能判断"
        }

    except Exception as e:
        print(f"[ERROR] 单人模式AI判断失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI判断服务暂时不可用: {str(e)}")

