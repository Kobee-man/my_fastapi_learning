"""
海龟汤判官模块 - 语义判断 + Token优化 + 缓存

接口：
    from core.turtle_soup_judge import judge_answer

    result = await judge_answer(story="一个人走进酒吧...", question="他生病了吗？")
    # => {"answer": "Yes", "confidence": 0.92, "reason": "故事提到此人正在打嗝"}

设计原则：
    - 与 llm_service 解耦，仅依赖其 chat() 接口
    - 与 turtle_soup API 解耦，可独立调用
    - Token 最小化：prompt 压缩 + max_tokens=100
    - 内置缓存、否定检测、对立词检测、一致性校验
"""

import re
import json
import hashlib
from typing import Optional
from dataclasses import dataclass, field

from core.llm_service import llm_service, LLMError


# ==================== 配置 ====================

JUDGE_TEMPERATURE = 0.3
JUDGE_MAX_TOKENS = 100
STORY_TRUNCATE_THRESHOLD = 300  # 超过此字符数触发裁剪
CACHE_MAX_SIZE = 256


# ==================== 缓存 ====================

_judge_cache: dict[str, dict] = {}


def _cache_key(story: str, question: str) -> str:
    """生成缓存键（SHA256 截断）"""
    raw = f"{story.strip().lower()}|||{question.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get_from_cache(story: str, question: str) -> Optional[dict]:
    return _judge_cache.get(_cache_key(story, question))


def put_to_cache(story: str, question: str, result: dict) -> None:
    if len(_judge_cache) >= CACHE_MAX_SIZE:
        # FIFO：删除最早的一半
        keys = list(_judge_cache.keys())
        for k in keys[: len(keys) // 2]:
            del _judge_cache[k]
    _judge_cache[_cache_key(story, question)] = result


def clear_cache() -> None:
    _judge_cache.clear()


# ==================== 轻量语义辅助 ====================

# 中文否定词
_NEGATION_WORDS = {"不", "没", "未", "不是", "没有", "未曾", "并非", "否", "无", "非"}

# 对立关键词对（生/死、有/无、是/否 …）
_OPPOSITES = {
    "生": "死", "死": "生",
    "有": "没有", "没有": "有",
    "是": "不是", "不是": "是",
    "在": "不在", "不在": "在",
    "会": "不会", "不会": "会",
    "能": "不能", "不能": "能",
    "活着": "死了", "死了": "活着",
    "存在": "不存在", "不存在": "存在",
    "开心": "伤心", "伤心": "开心",
    "爱": "恨", "恨": "爱",
}


def contains_negation(text: str) -> bool:
    """检测文本是否包含否定词"""
    return any(neg in text for neg in _NEGATION_WORDS)


def detect_opposite_keywords(question: str, story: str) -> Optional[str]:
    """
    检测问题与故事中是否出现对立关键词。
    返回冲突描述字符串，无冲突返回 None。
    """
    for kw_a, kw_b in _OPPOSITES.items():
        if kw_a in question and kw_b in story:
            return f"问题含'{kw_a}'但故事含'{kw_b}'"
        if kw_b in question and kw_a in story:
            return f"问题含'{kw_b}'但故事含'{kw_a}'"
    return None


def preprocess_question(question: str) -> str:
    """可选预处理：去除口语冗余，统一疑问形式"""
    q = question.strip()
    # 去掉结尾语气词
    q = re.sub(r"[吗嘛呢吧啊哦呀]+$", "", q)
    # 统一引号
    q = q.replace(""", '"').replace(""", '"').replace("'", "'").replace("'", "'")
    return q.strip()


# ==================== Story 裁剪 ====================

def _truncate_story(story: str, question: str) -> str:
    """
    Token 优化：story 超长时，保留与 question 关键词重叠最高的段落/句子。
    """
    if len(story) <= STORY_TRUNCATE_THRESHOLD:
        return story

    # 按句号/换行切分
    sentences = re.split(r"[。\n！!？?；;]+", story)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return story[:STORY_TRUNCATE_THRESHOLD]

    # 提取 question 中的关键词（长度>=2 的词）
    q_chars = set(question)
    q_keywords = {ch for ch in q_chars if len(ch.strip()) >= 1}

    # 按与 question 的字符重叠率打分
    scored = []
    for sent in sentences:
        overlap = sum(1 for ch in sent if ch in q_keywords)
        score = overlap / max(len(sent), 1)
        scored.append((score, sent))

    scored.sort(key=lambda x: x[0], reverse=True)

    # 取 top 句子，拼接后不超过阈值
    result = []
    total = 0
    for _, sent in scored:
        if total + len(sent) > STORY_TRUNCATE_THRESHOLD:
            break
        result.append(sent)
        total += len(sent)

    # 至少保留最高分的一句（硬截断）
    if not result:
        top = scored[0][1]
        result = [top[:STORY_TRUNCATE_THRESHOLD]]

    return "。".join(result) + "。"


# ==================== Prompt 构建 ====================

def build_prompt(story: str, question: str) -> tuple[str, str]:
    """
    构建判官 prompt。
    返回 (prompt, system_prompt)。

    设计要点：
    - system 定义角色和 JSON 约束（一次设定，可被 provider 缓存）
    - prompt 只含 story + question（最小化 token）
    - 隐式推理：要求内部推理后直接输出 JSON
    """
    story_text = _truncate_story(story, question)
    q_text = preprocess_question(question)

    system = (
        "你是海龟汤游戏判官。根据故事回答问题。\n"
        "规则：answer 只能是 Yes/No/Unknown。\n"
        "  Yes=符合故事事实\n"
        "  No=与故事冲突\n"
        "  Unknown=信息不足或模糊\n"
        "支持同义句/改写句识别，正确处理否定词。\n"
        "内部推理后直接输出JSON，不显示推理过程。\n"
        '格式：{"answer":"Yes|No|Unknown","confidence":0~1,"reason":"一句话"}'
    )

    prompt = f"Story:{story_text}\nQ:{q_text}\nJSON:"

    return prompt, system


# ==================== 后处理 ====================

def _parse_response(text: str) -> Optional[dict]:
    """从 LLM 响应中解析 JSON，兼容 markdown 代码块"""
    text = text.strip()
    # 直接解析
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "answer" in data:
            return data
    except json.JSONDecodeError:
        pass
    # 提取 { ... } 块
    match = re.search(r"\{[^{}]*\}", text)
    if match:
        try:
            data = json.loads(match.group())
            if isinstance(data, dict) and "answer" in data:
                return data
        except json.JSONDecodeError:
            pass
    return None


def _normalize_result(data: dict) -> dict:
    """标准化输出格式"""
    answer = str(data.get("answer", "Unknown")).strip()
    # 统一大小写
    mapping = {"yes": "Yes", "no": "No", "unknown": "Unknown",
               "是": "Yes", "否": "No", "无关": "Unknown"}
    answer = mapping.get(answer.lower(), "Unknown")

    confidence = data.get("confidence", 0.5)
    try:
        confidence = float(confidence)
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = 0.5

    reason = str(data.get("reason", "")).strip()
    if len(reason) > 100:
        reason = reason[:100]

    return {"answer": answer, "confidence": round(confidence, 2), "reason": reason}


def _self_consistency_check(result: dict, question: str, story: str) -> dict:
    """
    一致性校验：
    - 如果检测到对立关键词冲突，且 LLM 判 Yes/No 与冲突方向相反，降置信度
    - 如果问题含否定词，检查 answer 方向是否合理
    """
    confidence = result["confidence"]
    answer = result["answer"]

    # 对立关键词检测
    conflict = detect_opposite_keywords(question, story)
    if conflict:
        # 存在对立词冲突，一般应为 No 或 Unknown
        if answer == "Yes":
            confidence = min(confidence, 0.55)
            result["reason"] += f"（检测到语义对立:{conflict}）"

    # 否定词翻转校验
    if contains_negation(question) and answer in ("Yes", "No"):
        # 含否定词的问题容易被小模型搞反，额外降低置信度
        if confidence > 0.85:
            confidence = confidence * 0.9

    result["confidence"] = round(max(0.0, min(1.0, confidence)), 2)
    return result


def _fallback_result(error_msg: str = "") -> dict:
    """LLM 不可用或解析失败时的兜底结果"""
    reason = "AI判官不可用" + (f":{error_msg}" if error_msg else "")
    return {"answer": "Unknown", "confidence": 0.0, "reason": reason}


# ==================== 对外接口 ====================

async def judge_answer(story: str, question: str) -> dict:
    """
    海龟汤判官入口。

    Args:
        story: 故事/汤底（situation + truth 拼接）
        question: 玩家提问

    Returns:
        {
            "answer": "Yes | No | Unknown",
            "confidence": 0~1,
            "reason": "一句话简短理由"
        }
    """
    if not story or not question:
        return _fallback_result("故事或问题为空")

    # 1. 缓存命中
    cached = get_from_cache(story, question)
    if cached is not None:
        return cached

    # 2. 快速本地预判（对立关键词 → 直接 No，省一次 LLM 调用）
    conflict = detect_opposite_keywords(question, story)
    if conflict:
        local_result = {
            "answer": "No",
            "confidence": 0.80,
            "reason": f"语义对立:{conflict}"
        }
        put_to_cache(story, question, local_result)
        return local_result

    # 3. 构建 prompt 并调用 LLM
    prompt, system = build_prompt(story, question)

    # 临时覆盖 LLM 参数（不影响全局配置）
    original_temp = llm_service.config.temperature
    original_max = llm_service.config.max_tokens
    llm_service.config.temperature = JUDGE_TEMPERATURE
    llm_service.config.max_tokens = JUDGE_MAX_TOKENS

    try:
        response = await llm_service.chat(prompt, system)
    except LLMError:
        result = _fallback_result("LLM调用失败")
        put_to_cache(story, question, result)
        return result
    finally:
        llm_service.config.temperature = original_temp
        llm_service.config.max_tokens = original_max

    # 4. 解析 JSON
    parsed = _parse_response(response)
    if parsed is None:
        result = _fallback_result("JSON解析失败")
        put_to_cache(story, question, result)
        return result

    # 5. 标准化 + 一致性校验
    result = _normalize_result(parsed)
    result = _self_consistency_check(result, question, story)

    # 6. 存入缓存
    put_to_cache(story, question, result)
    return result
