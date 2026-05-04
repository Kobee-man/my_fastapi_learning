/**
 * 海龟汤游戏 - 本地LLM集成服务
 * Turtle Soup Game - Local LLM Integration Service
 *
 * 功能：
 * ✅ 自动检测Ollama服务状态
 * ✅ 智能连接管理（自动重连/降级）
 * ✅ Qwen 3.5 4B 模型深度优化
 * ✅ 响应缓存与性能监控
 * ✅ 离线模式支持
 */

// LLM配置
const LLM_CONFIG = {
  // Ollama服务地址
  host: 'http://localhost:11434',
  
  // 模型配置
  model: 'qwen3.5:4b',
  
  // 推理参数
  temperature: {
    judgment: 0.3,    // 问题判断：极低温度保证一致性
    generation: 0.5,   // 题目生成：低温度保证结构化
    evaluation: 0.4    // 答案评估：中等偏低保证客观性
  },
  
  // 超时设置
  timeout: 30000,           // 请求超时30秒
  connectionTimeout: 10000, // 连接超时10秒
  
  // 重试机制
  maxRetries: 2,
  retryDelay: 1500,
  
  // 缓存配置
  enableCache: true,
  cacheTTL: 3600000, // 1小时
};

// 连接状态枚举
const ConnectionStatus = {
  DISCONNECTED: 'disconnected',
  CONNECTED: 'connected',
  ERROR: 'error',
  SLOW: 'slow',
  UNKNOWN: 'unknown'
};

// 性能指标收集器
class PerformanceTracker {
  constructor() {
    this.metrics = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      cacheHits: 0,
      totalTime: 0,
      totalTokens: 0,
      errors: []
    };
  }
  
  record(success, latency, tokens = 0, error = null) {
    this.metrics.totalRequests++;
    if (success) {
      this.metrics.successfulRequests++;
      this.metrics.totalTime += latency;
      this.metrics.totalTokens += tokens;
    } else {
      this.metrics.failedRequests++;
      if (error) {
        this.metrics.errors.push({
          time: new Date().toISOString(),
          error: error.message || String(error)
        });
        // 只保留最近20条错误
        if (this.metrics.errors.length > 20) {
          this.metrics.errors.shift();
        }
      }
    }
  }
  
  getSummary() {
    const successRate = this.metrics.totalRequests > 0 
      ? (this.metrics.successfulRequests / this.metrics.totalRequests * 100).toFixed(1)
      : 0;
    
    const avgLatency = this.metrics.successfulRequests > 0
      ? Math.round(this.metrics.totalTime / this.metrics.successfulRequests)
      : 0;
    
    return {
      successRate: `${successRate}%`,
      avgLatency: `${avgLatency}ms`,
      totalRequests: this.metrics.totalRequests,
      cacheHits: this.metrics.cacheHits,
      totalTokens: this.metrics.totalTokens,
      recentErrors: this.metrics.errors.slice(-5)
    };
  }
}

// 响应缓存系统
class ResponseCache {
  constructor(ttl = 3600000) {
    this.cache = new Map();
    this.ttl = ttl;
  }
  
  generateKey(prompt, systemPrompt = '', temperature = 0.7) {
    const content = `${prompt}|${systemPrompt}|${temperature}`;
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return `cache_${Math.abs(hash).toString(36)}`;
  }
  
  get(key) {
    if (!this.cache.has(key)) return null;
    
    const item = this.cache.get(key);
    const now = Date.now();
    
    if (now - item.timestamp < this.ttl) {
      return item.data;
    } else {
      this.cache.delete(key);
      return null;
    }
  }
  
  set(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
    
    // 缓存大小限制（最多100条）
    if (this.cache.size > 100) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
  }
  
  clear() {
    this.cache.clear();
  }
  
  size() {
    return this.cache.size;
  }
}

// 主LLM客户端类
class TurtleSoupLLMClient {
  constructor(config = {}) {
    this.config = { ...LLM_CONFIG, ...config };
    this.status = ConnectionStatus.UNKNOWN;
    this.performance = new PerformanceTracker();
    this.cache = new ResponseCache(this.config.cacheTTL);
    this.lastError = null;
    this.modelInfo = null;
    
    // 初始化时检查连接
    this.checkConnection();
  }
  
  /**
   * 检查Ollama连接状态
   */
  async checkConnection() {
    try {
      const startTime = Date.now();
      
      const response = await fetch(`${this.config.host}/api/tags`, {
        method: 'GET',
        signal: AbortSignal.timeout(8000)
      });
      
      const latency = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        const models = data.models || [];
        
        // 检查目标模型是否存在
        const modelExists = models.some(m => m.name === this.config.model);
        
        if (modelExists) {
          this.status = latency > 2000 ? ConnectionStatus.SLOW : ConnectionStatus.CONNECTED;
          
          // 获取模型详细信息
          try {
            const modelResponse = await fetch(`${this.config.host}/api/show`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ name: this.config.model }),
              signal: AbortSignal.timeout(5000)
            });
            
            if (modelResponse.ok) {
              this.modelInfo = await modelResponse.json();
            }
          } catch (e) {
            console.warn('获取模型信息失败:', e);
          }
          
          console.log(`[LLM] ✓ 服务已连接 (${latency}ms) | 模型: ${this.config.model}`);
          return {
            status: this.status,
            message: `✓ 服务正常 (延迟: ${latency}ms)`,
            latency,
            availableModels: models.map(m => m.name)
          };
          
        } else {
          this.status = ConnectionStatus.ERROR;
          const available = models.map(m => m.name).join(', ') || '无';
          return {
            status: this.status,
            message: `✗ 模型 '${this.config.model}' 未安装\n可用: ${available}`,
            availableModels: models.map(m => m.name)
          };
        }
        
      } else {
        this.status = ConnectionStatus.ERROR;
        return {
          status: this.status,
          message: `✗ 服务异常 (HTTP ${response.status})`
        };
      }
      
    } catch (error) {
      console.error('[LLM] 连接检查失败:', error);
      this.lastError = error;
      
      if (error.name === 'AbortError') {
        this.status = ConnectionStatus.SLOW;
        return { status: this.status, message: '⚠ 连接超时' };
      } else if (error.message.includes('fetch')) {
        this.status = ConnectionStatus.DISCONNECTED;
        return { status: this.status, message: '✗ 无法连接到Ollama服务' };
      } else {
        this.status = ConnectionStatus.ERROR;
        return { status: this.status, message: `✗ 错误: ${error.message}` };
      }
    }
  }
  
  /**
   * 核心生成方法（带重试和缓存）
   */
  async generate(prompt, options = {}) {
    const {
      systemPrompt = '',
      temperature = this.config.temperature.judgment,
      maxRetries = this.config.maxRetries,
      useCache = this.config.enableCache
    } = options;
    
    // 检查缓存
    if (useCache) {
      const cacheKey = this.cache.generateKey(prompt, systemPrompt, temperature);
      const cached = this.cache.get(cacheKey);
      if (cached) {
        this.performance.cacheHits++;
        this.performance.record(true, 0, 0);
        console.log('[LLM] ✓ 命中缓存');
        return { success: true, data: cached, fromCache: true };
      }
    }
    
    let lastError = null;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const result = await this._callAPI(prompt, systemPrompt, temperature);
        
        // 成功后缓存结果
        if (useCache && result.success) {
          const cacheKey = this.cache.generateKey(prompt, systemPrompt, temperature);
          this.cache.set(cacheKey, result.data);
        }
        
        return result;
        
      } catch (error) {
        lastError = error;
        console.warn(`[LLM] 第${attempt}次尝试失败:`, error.message);
        
        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, this.config.retryDelay * attempt));
        }
      }
    }
    
    // 所有重试都失败
    this.performance.record(false, 0, 0, lastError);
    return {
      success: false,
      error: lastError?.message || '未知错误',
      suggestion: this._getFallbackSuggestion()
    };
  }
  
  /**
   * 实际调用Ollama API
   */
  async _callAPI(prompt, systemPrompt, temperature) {
    const startTime = Date.now();
    
    const payload = {
      model: this.config.model,
      prompt: prompt,
      stream: false,
      options: {
        temperature: temperature,
        top_p: 0.9,
        top_k: 40,
        repeat_penalty: 1.1,
        num_predict: 2048
      }
    };
    
    if (systemPrompt) {
      payload.system = systemPrompt;
    }
    
    console.log(`[LLM] 调用模型: ${this.config.model} | 温度: ${temperature}`);
    
    const response = await fetch(`${this.config.host}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(this.config.timeout)
    });
    
    const latency = Date.now() - startTime;
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }
    
    const result = await response.json();
    const text = result.response?.trim() || '';
    
    if (!text) {
      throw new Error('模型返回空内容');
    }
    
    // 记录性能指标
    const tokens = (result.eval_count || 0) + (result.prompt_eval_count || 0);
    this.performance.record(true, latency, tokens);
    
    console.log(`[LLM] ✓ 完成 (${latency}ms | Token: ${tokens} | 长度: ${text.length})`);
    
    return {
      success: true,
      data: text,
      metadata: {
        latency,
        tokens,
        model: this.config.model,
        createdAt: new Date().toISOString()
      }
    };
  }
  
  /**
   * 专用：判断玩家问题
   */
  async judgeQuestion(question, situation, truth, history = []) {
    const prompt = this._buildJudgmentPrompt(question, situation, truth, history);
    const systemPrompt = this._getSystemPrompt();
    
    const result = await this.generate(prompt, {
      systemPrompt,
      temperature: this.config.temperature.judgment
    });
    
    if (!result.success) {
      return {
        answer: '无关',
        reason: 'AI判断服务暂不可用，使用本地算法',
        confidence: 0.1,
        fallback: true
      };
    }
    
    // 解析JSON响应
    const judgment = this._parseJudgmentJSON(result.data);
    
    return judgment || {
      answer: '无关',
      reason: '无法解析AI响应',
      confidence: 0.2,
      raw: result.data
    };
  }
  
  /**
   * 专用：评估答案
   */
  async evaluateAnswer(userAnswer, truth, situation) {
    const prompt = this._buildEvaluationPrompt(userAnswer, truth, situation);
    const systemPrompt = this._getSystemPrompt();
    
    const result = await this.generate(prompt, {
      systemPrompt,
      temperature: this.config.temperature.evaluation
    });
    
    if (!result.success) {
      return this._fallbackEvaluation(userAnswer, truth);
    }
    
    const evaluation = this._parseEvaluationJSON(result.data);
    
    return evaluation || this._fallbackEvaluation(userAnswer, truth);
  }
  
  /**
   * 专用：生成新题目
   */
  async generatePuzzle(difficulty = 'medium') {
    const prompt = this._buildPuzzleGenerationPrompt(difficulty);
    const systemPrompt = this._getSystemPrompt();
    
    const result = await this.generate(prompt, {
      systemPrompt,
      temperature: this.config.temperature.generation
    });
    
    if (!result.success) {
      return null;
    }
    
    const puzzle = this._parsePuzzleJSON(result.data);
    
    if (puzzle) {
      puzzle._meta = {
        generatedAt: new Date().toISOString(),
        model: this.config.model,
        difficulty,
        ...result.metadata
      };
    }
    
    return puzzle;
  }
  
  // ==================== Prompt构建器 ====================
  
  _getSystemPrompt() {
    return `你是一位经验丰富的海龟汤（情境推理）游戏裁判。你的职责是严格、准确、一致地判断玩家的问题。

核心原则：
1. 准确性优先：基于真相内容进行事实性判断
2. 逻辑连贯：同一局游戏中保持回答一致
3. 二元约束：只能回答"是"、"否"或"无关"
4. 相关性检测：只有与核心要素直接相关的问题才值得回答`;
  }
  
  _buildJudgmentPrompt(question, situation, truth, history) {
    const historyText = history.length > 0
      ? '\n近期问答记录：\n' + history.slice(-5).map((h, i) =>
          `Q${i+1}: ${h.question} → ${h.answer}`
        ).join('\n')
      : '\n（暂无历史记录）';
    
    return `【海龟汤判断任务】

当前情境：
${situation}

完整真相：
${truth}

玩家问题：
"${question}"
${historyText}

请严格按照规则进行判断。

输出格式（严格JSON）：
{
    "answer": "是"/"否"/"无关",
    "reason": "简短依据（15-30字）",
    "confidence": 0.7-1.0,
    "reasoning_steps": ["步骤1", "步骤2", "步骤3"]
}`;
  }
  
  _buildEvaluationPrompt(userAnswer, truth, situation) {
    return `【答案评估任务】

情境描述：
${situation}

正确真相：
${truth}

玩家的答案：
${userAnswer}

请从以下维度评估：

1. 核心要素覆盖率 (40%): 人物、事件、原因、结果
2. 逻辑连贯性 (30%): 因果关系是否合理
3. 表述精确度 (20%): 关键事实准确性
4. 完整性 (10%): 是否遗漏重要情节

判定阈值：
- accuracy >= 0.85 → 正确（优秀）
- accuracy >= 0.70 → 正确（良好）
- accuracy < 0.70 → 不正确

输出格式（严格JSON）：
{
    "is_correct": true/false,
    "accuracy": 0.0-1.0,
    "dimension_scores": {...},
    "matched_facts": [...],
    "missing_facts": [...],
    "feedback": "详细反馈（50-150字）"
}`;
  }
  
  _buildPuzzleGenerationPrompt(difficulty) {
    const diffMap = {
      easy: '简单（5-8题可解，贴近生活）',
      medium: '中等（10-15题，需要联想）',
      hard: '困难（15-25题，复杂推理）'
    };
    
    return `作为海龟汤出题专家，请生成一个${diffMap[difficulty] || '中等'}难度的中文题目。

要求：
1. 情境描述（30-60字）：制造认知冲突或悬念
2. 完整真相（150-250字）：逻辑严密，有反转
3. 提示信息：3条渐进式提示
4. 关键词：5-8个用于匹配

质量标准：
✅ 真实可信（非科幻奇幻）
✅ 真相可推导
✅ 适合全年龄段

输出格式（严格JSON）：
{
    "title": "题目标题",
    "situation": "情境",
    "truth": "真相",
    "hints": ["提示1", "提示2", "提示3"],
    "keywords": ["关键词1", "关键词2"]
}`;
  }
  
  // ==================== JSON解析器 ====================
  
  _parseJudgmentJSON(text) {
    try {
      // 清理markdown代码块
      let cleaned = text.replace(/```json\s*/g, '').replace(/```\s*/g, '');
      
      // 提取JSON对象
      const jsonMatch = cleaned.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const data = JSON.parse(jsonMatch[0]);
        
        const validAnswers = ['是', '否', '无关'];
        let answer = String(data.answer || '').trim();
        
        // 标准化答案
        if (!validAnswers.includes(answer)) {
          for (const valid of validAnswers) {
            if (answer.includes(valid)) {
              answer = valid;
              break;
            }
          }
        }
        
        return {
          answer: answer || '无关',
          reason: String(data.reason || '').substring(0, 50),
          confidence: Math.min(1, Math.max(0, data.confidence || 0.7)),
          reasoningSteps: data.reasoning_steps || []
        };
      }
    } catch (e) {
      console.warn('[LLM] JSON解析失败:', e);
    }
    
    // 降级：纯文本解析
    if (text.includes('是') && !text.includes('否')) {
      return { answer: '是', reason: '', confidence: 0.6 };
    } else if (text.includes('否') && !text.includes('是')) {
      return { answer: '否', reason: '', confidence: 0.6 };
    } else if (text.includes('无关')) {
      return { answer: '无关', reason: '', confidence: 0.9 };
    }
    
    return null;
  }
  
  _parseEvaluationJSON(text) {
    try {
      let cleaned = text.replace(/```json\s*/g, '').replace(/```\s*/g, '');
      const jsonMatch = cleaned.match(/\{[\s\S]*\}/);
      
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch (e) {
      console.warn('[LLM] 评估JSON解析失败:', e);
    }
    
    return null;
  }
  
  _parsePuzzleJSON(text) {
    try {
      let cleaned = text.replace(/```json\s*/g, '').replace(/```\s*/g, '');
      const jsonMatch = cleaned.match(/\{[\s\S]*\}/);
      
      if (jsonMatch) {
        const data = JSON.parse(jsonMatch[0]);
        
        // 验证必要字段
        if (data.situation && data.truth) {
          return {
            title: data.title || '未命名题目',
            situation: data.situation,
            truth: data.truth,
            hints: data.hints || [],
            keywords: data.keywords || [],
            difficulty: data.difficulty || 'medium'
          };
        }
      }
    } catch (e) {
      console.warn('[LLM] 题目JSON解析失败:', e);
    }
    
    return null;
  }
  
  // ==================== 降级方案 ====================
  
  _fallbackEvaluation(userAnswer, truth) {
    const userWords = this._extractWords(userAnswer.toLowerCase());
    const truthWords = this._extractWords(truth.toLowerCase());
    
    const overlap = userWords.filter(w => truthWords.includes(w)).length;
    const coverage = overlap / Math.max(truthWords.length, 1);
    
    return {
      is_correct: coverage >= 0.6,
      accuracy: Math.min(coverage, 1),
      dimension_scores: {
        core_elements: coverage,
        logic_coherence: 0.7,
        precision: coverage,
        completeness: 0.6
      },
      feedback: coverage >= 0.6
        ? '方向正确！继续完善细节。'
        : '还需要更多关键信息，继续推理！',
      matchedFacts: [],
      missingFacts: [],
      fallback: true
    };
  }
  
  _extractWords(text) {
    return text.match(/[\u4e00-\u9fa5a-zA-Z]+/g) || [];
  }
  
  _getFallbackSuggestion() {
    switch (this.status) {
      case ConnectionStatus.DISCONNECTED:
        return '请确保Ollama服务正在运行 (ollama serve)';
      case ConnectionStatus.ERROR:
        return '请检查模型是否已安装: ollama pull qwen3.5:4b';
      case ConnectionStatus.SLOW:
        return '网络较慢，建议稍后重试';
      default:
        return '建议使用本地算法作为备选方案';
    }
  }
  
  /**
   * 获取性能报告
   */
  getPerformanceReport() {
    const stats = this.performance.getSummary();
    const connectionInfo = {
      status: this.status,
      model: this.config.model,
      host: this.config.host,
      cacheSize: this.cache.size(),
      lastError: this.lastError?.message || null
    };
    
    return {
      ...connectionInfo,
      performance: stats,
      timestamp: new Date().toISOString()
    };
  }
  
  /**
   * 清理资源
   */
  cleanup() {
    this.cache.clear();
    console.log('[LLM] 资源已清理');
  }
}

// 导出单例实例
export const llmClient = new TurtleSoupLLMClient();

// 导出类（允许自定义配置）
export { TurtleSoupLLMClient, ConnectionStatus, PerformanceTracker, ResponseCache };

export default llmClient;
