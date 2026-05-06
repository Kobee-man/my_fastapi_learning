<template>
  <div class="turtle-soup-modal" @click.self="handleClose">
    <div
      class="turtle-soup-container"
      :class="{ 'full-screen': currentView !== 'menu' }"
      :style="containerStyle"
      ref="containerRef"
    >
      <!-- 拖拽手柄 -->
      <div class="drag-handle" @mousedown.prevent="startDrag" title="拖拽移动">
        <span>⠿</span>
      </div>

      <!-- 关闭按钮 -->
      <button class="close-btn" @click="handleClose">✕</button>

      <!-- 主菜单 -->
      <div v-if="currentView === 'menu'" class="menu-view">
        <div class="game-header">
          <h1>🐢 海龟汤游戏</h1>
          <p class="subtitle">AI 驱动 · 智能推理</p>
          <div class="llm-status" :class="llmAvailable ? 'available' : 'unavailable'">
            <span class="status-dot"></span>
            <span>{{ llmAvailable ? 'AI 就绪' : 'AI 未连接' }}</span>
          </div>
        </div>

        <div class="quick-actions">
          <button class="action-btn primary" @click="startNewSingleGame">
            🎮 开始新游戏
          </button>
          <button class="action-btn secondary" @click="showRules = true">
            📖 游戏规则
          </button>
          <button class="action-btn secondary" @click="loadHistory">
            📜 历史记录
          </button>
        </div>

        <!-- 未完成的游戏 -->
        <div v-if="hasSavedProgress" class="saved-progress-card">
          <div class="progress-icon">💾</div>
          <div class="progress-info">
            <h4>发现未完成的游戏</h4>
            <p>题目：{{ savedGameProgress.puzzle?.title || '未知' }}</p>
            <p>已提问 {{ savedGameProgress.questions?.length || 0 }} 次</p>
          </div>
          <button class="btn success" @click="continueSavedGame">继续</button>
        </div>

        <!-- 历史记录 -->
        <div v-if="showHistoryPanel" class="history-panel">
          <h3>📜 游戏历史</h3>
          <div v-if="gameHistory.length === 0" class="empty-state">暂无记录</div>
          <div v-else class="history-list">
            <div v-for="(record, i) in gameHistory" :key="i" class="history-item">
              <div class="history-main">
                <span class="puzzle-title">{{ record.puzzle_title }}</span>
                <span class="winner">🏆 {{ record.winner }}</span>
              </div>
              <div class="history-meta">
                <span>{{ record.duration || '-' }}</span>
                <span>{{ formatDate(record.finished_at) }}</span>
              </div>
            </div>
          </div>
          <button class="btn secondary" @click="showHistoryPanel = false">关闭</button>
        </div>

        <!-- 规则 -->
        <div v-if="showRules" class="rules-panel">
          <h3>📖 海龟汤游戏规则</h3>
          <div class="rules-content">
            <p>通过提问"是/否/无关"问题，逐步推理出故事的完整真相。</p>
            <ul>
              <li>问题必须能用"是"、"否"、"无关"回答</li>
              <li>不能直接问"真相是什么"</li>
              <li>有提问次数限制</li>
              <li>第一个正确说出真相的玩家获胜</li>
            </ul>
          </div>
          <div class="tips-section">
            <h4>💡 技巧</h4>
            <ul>
              <li>从"为什么"开始提问往往更有效</li>
              <li>注意时间、地点、人物关系等关键要素</li>
              <li>如果卡住了，可以使用提示功能</li>
              <li>真相往往比想象的更简单</li>
            </ul>
          </div>
          <button class="btn secondary" @click="showRules = false">我知道了</button>
        </div>
      </div>

      <!-- 单人游戏进行界面 -->
      <div v-if="currentView === 'playing'" class="playing-view">
        <!-- 头部 -->
        <div class="playing-header">
          <button class="back-btn" @click="handleExitClick">← 返回</button>
          <div class="game-status-bar">
            <span class="status-item">📝 {{ game.questions.length }}/{{ game.settings.max_questions }}</span>
            <span class="status-item">💡 {{ game.settings.total_hints - game.hintsUsed }}</span>
            <span class="status-item difficulty-badge" :class="game.puzzle.difficulty">
              {{ getDifficultyText(game.puzzle.difficulty) }}
            </span>
          </div>
        </div>

        <!-- 情境 -->
        <div class="situation-panel">
          <div class="panel-label">📋 情境描述</div>
          <div class="situation-text">{{ game.puzzle.situation }}</div>
          <div class="puzzle-title-badge" v-if="game.puzzle.title">🎯 {{ game.puzzle.title }}</div>
        </div>

        <!-- 未开始 -->
        <div v-if="!game.started" class="single-qa-panel">
          <div class="waiting-state">
            <div class="waiting-icon">🤔</div>
            <h3>准备好开始推理了吗？</h3>
            <p>通过提问"是/否"问题来揭开真相</p>
            <button class="btn primary large" @click="game.started = true">🎮 开始！</button>
          </div>
        </div>

        <!-- 进行中 -->
        <div v-else-if="game.status !== 'finished'" class="single-qa-panel">
          <div class="active-game">
            <!-- 提问输入 -->
            <div class="question-input-area">
              <div class="panel-label">❓ 你的问题</div>
              <div class="input-row">
                <input
                  type="text"
                  v-model="currentQuestion"
                  placeholder="例如：这个人是男性吗？"
                  @keypress.enter="submitQuestion"
                  :disabled="submittingQuestion || game.questions.length >= game.settings.max_questions"
                  class="question-input"
                >
                <button
                  class="btn primary"
                  @click="submitQuestion"
                  :disabled="submittingQuestion || !currentQuestion.trim() || game.questions.length >= game.settings.max_questions"
                >
                  {{ submittingQuestion ? '判断中...' : '提问' }}
                </button>
              </div>
              <div class="input-hint" v-if="game.questions.length >= game.settings.max_questions">
                ⚠️ 已达最大提问次数，请尝试提交答案
              </div>
            </div>

            <!-- 问题记录 -->
            <div class="questions-history">
              <div class="panel-label">💬 问答记录 ({{ game.questions.length }})</div>
              <div class="questions-list" ref="questionsListRef">
                <div v-for="(q, index) in game.questions" :key="index" class="question-item mine">
                  <div class="q-player">🧑 你</div>
                  <div class="q-content">{{ q.question }}</div>
                  <div class="q-answer" :class="q.answer">{{ q.answer }}</div>
                  <div class="q-reason" v-if="q.reason">{{ q.reason }}</div>
                </div>
                <div v-if="game.questions.length === 0" class="empty-questions">开始你的第一个提问吧！</div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="action-buttons">
              <button
                class="btn warning"
                @click="getHint"
                :disabled="game.hintsUsed >= game.settings.total_hints"
              >
                💡 提示 ({{ game.settings.total_hints - game.hintsUsed }})
              </button>
              <button class="btn success" @click="showAnswerInput = true">🎯 我知道答案了！</button>
              <button class="btn info" @click="saveProgress" :disabled="saving">💾 保存</button>
              <button class="btn danger" @click="handleExitClick">🚪 退出</button>
            </div>

            <!-- 答案输入 -->
            <div v-if="showAnswerInput" class="answer-input-area">
              <div class="panel-label">✍️ 输入你推断的完整真相</div>
              <textarea
                v-model="myAnswer"
                placeholder="根据所有线索，写出完整的故事真相..."
                rows="4"
                class="answer-textarea"
              ></textarea>
              <div class="answer-actions">
                <button class="btn secondary" @click="showAnswerInput = false">取消</button>
                <button
                  class="btn success"
                  @click="submitAnswer"
                  :disabled="!myAnswer.trim() || submittingAnswer"
                >
                  {{ submittingAnswer ? '验证中...' : '提交验证' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 游戏结束 -->
        <div v-else class="single-qa-panel finished-state">
          <div class="winner-announcement" :class="game.result">
            <template v-if="game.result === 'correct'">🎉 恭喜！成功破解真相！</template>
            <template v-else>🏁 游戏结束</template>
          </div>

          <div class="truth-reveal">
            <div class="panel-label">🔍 完整真相</div>
            <div class="truth-text">{{ game.puzzle.truth }}</div>
          </div>

          <div class="result-analysis" v-if="game.feedback">
            <div class="panel-label">📊 反馈</div>
            <div class="feedback-text">{{ game.feedback }}</div>
          </div>

          <div class="game-stats">
            <div class="stat-item">
              <span class="stat-label">提问</span>
              <span class="stat-value">{{ game.questions.length }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">提示</span>
              <span class="stat-value">{{ game.hintsUsed }}次</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">用时</span>
              <span class="stat-value">{{ calcDuration() }}</span>
            </div>
          </div>

          <div class="finished-actions">
            <button class="btn primary" @click="startNewSingleGame">🔄 再来一局</button>
            <button class="btn secondary" @click="currentView = 'menu'">🏠 返回</button>
          </div>
        </div>
      </div>

      <!-- 退出确认 -->
      <transition name="dialog-fade">
        <div v-if="showExitDialog" class="confirm-dialog-overlay" @click.self="showExitDialog = false">
          <div class="confirm-dialog">
            <h3>确认退出？</h3>
            <p>当前游戏尚未结束，退出后可以下次继续。</p>
            <div class="dialog-footer">
              <button class="btn secondary" @click="showExitDialog = false">继续游戏</button>
              <button class="btn danger" @click="confirmExit">确认退出</button>
            </div>
          </div>
        </div>
      </transition>

      <!-- 加载 -->
      <div v-if="loading" class="loading-overlay">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>

      <!-- 提示 -->
      <div v-if="errorMsg" class="error-toast" @click="errorMsg = ''">⚠️ {{ errorMsg }}</div>
      <div v-if="successMsg" class="success-toast" @click="successMsg = ''">✅ {{ successMsg }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import api from '../utils/api'

const props = defineProps({
  username: { type: String, required: true },
  token: { type: String, required: true }
})
const emit = defineEmits(['close'])

// ===== 视图 =====
const currentView = ref('menu') // menu | playing

// ===== UI 状态 =====
const showRules = ref(false)
const showHistoryPanel = ref(false)
const showAnswerInput = ref(false)
const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const showExitDialog = ref(false)
const llmAvailable = ref(false)
const gameHistory = ref([])

// ===== 输入 =====
const currentQuestion = ref('')
const myAnswer = ref('')
const submittingQuestion = ref(false)
const submittingAnswer = ref(false)

// ===== 保存进度 =====
const savedGameProgress = ref(null)
const hasSavedProgress = computed(() => savedGameProgress.value?.status === 'playing')

// ===== 游戏数据 =====
const game = reactive({
  gameId: '',
  puzzle: {},
  settings: { difficulty: 'medium', max_questions: 20, total_hints: 3 },
  questions: [],
  hintsUsed: 0,
  started: false,
  status: 'playing',
  result: '',
  feedback: '',
  startTime: null,
  endTime: null
})

const questionsListRef = ref(null)

// ===== 拖拽 =====
const containerRef = ref(null)
const dragState = reactive({ dragging: false, offsetX: 0, offsetY: 0 })
const pos = reactive({ x: null, y: null })

const containerStyle = computed(() => {
  if (pos.x === null) return {}
  return { left: pos.x + 'px', top: pos.y + 'px', transform: 'none' }
})

function startDrag(e) {
  const el = containerRef.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  dragState.dragging = true
  dragState.offsetX = e.clientX - rect.left
  dragState.offsetY = e.clientY - rect.top
  // 如果还没设过位置，用当前渲染位置
  if (pos.x === null) {
    pos.x = rect.left
    pos.y = rect.top
  }
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

function onDrag(e) {
  if (!dragState.dragging) return
  pos.x = e.clientX - dragState.offsetX
  pos.y = e.clientY - dragState.offsetY
}

function stopDrag() {
  dragState.dragging = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
})

// ===== 初始化 =====
onMounted(async () => {
  checkStatus()
  loadSaved()
})

async function checkStatus() {
  try {
    const s = await api.checkTurtleSoupStatus()
    llmAvailable.value = s.llm_available || false
  } catch {
    llmAvailable.value = false
  }
}

function loadSaved() {
  try {
    const raw = localStorage.getItem('turtle_soup_single_progress')
    if (!raw) return
    const p = JSON.parse(raw)
    const days = (Date.now() - new Date(p.timestamp)) / 86400000
    if (days <= 7 && p.status === 'playing') {
      savedGameProgress.value = p
    } else {
      localStorage.removeItem('turtle_soup_single_progress')
    }
  } catch { /* ignore */ }
}

// ===== 新游戏 =====
function startNewSingleGame() {
  localStorage.removeItem('turtle_soup_single_progress')
  savedGameProgress.value = null
  resetGame()
  currentView.value = 'playing'
}

function continueSavedGame() {
  if (!savedGameProgress.value) return
  const p = savedGameProgress.value
  Object.assign(game, {
    puzzle: p.puzzle,
    settings: p.settings,
    questions: p.questions || [],
    hintsUsed: p.hintsUsed || 0,
    started: true,
    status: 'playing',
    result: '',
    feedback: '',
    startTime: p.startTime,
    endTime: null
  })
  currentView.value = 'playing'
  savedGameProgress.value = null
}

function resetGame() {
  Object.assign(game, {
    gameId: '',
    puzzle: {},
    settings: { difficulty: 'medium', max_questions: 20, total_hints: 3 },
    questions: [],
    hintsUsed: 0,
    started: false,
    status: 'playing',
    result: '',
    feedback: '',
    startTime: null,
    endTime: null
  })
  currentQuestion.value = ''
  myAnswer.value = ''
  showAnswerInput.value = false
}

// ===== 提问 =====
async function submitQuestion() {
  if (!currentQuestion.value.trim()) return
  if (game.questions.length >= game.settings.max_questions) return

  // 首次提问时，如果还没题目则先生成
  if (!game.puzzle.situation) {
    await generatePuzzle()
    if (!game.puzzle.situation) return
  }

  submittingQuestion.value = true
  try {
    const history = game.questions.map(q => q.question)
    const data = await api.judgeQuestion({
      question: currentQuestion.value,
      truth: game.puzzle.truth,
      situation: game.puzzle.situation,
      keywords: [],
      hints: [],
      question_history: history,
      game_id: game.gameId
    })

    game.questions.push({
      question: currentQuestion.value,
      answer: data.judgment.answer,
      reason: data.judgment.reason,
      timestamp: new Date().toISOString()
    })
    currentQuestion.value = ''
    scrollBottom()
  } catch (e) {
    errorMsg.value = e.detail || 'LLM 服务不可用'
  } finally {
    submittingQuestion.value = false
  }
}

// ===== 生成题目 =====
async function generatePuzzle() {
  loading.value = true
  try {
    const data = await api.createGame({
      difficulty: game.settings.difficulty,
      max_questions: game.settings.max_questions,
      max_players: 1
    })
    game.puzzle = data.puzzle_preview
    game.gameId = data.game_id
    game.startTime = new Date().toISOString()
    successMsg.value = `🎯 ${data.puzzle_preview.title || '题目已就绪'}`
    setTimeout(() => successMsg.value = '', 3000)
  } catch (e) {
    errorMsg.value = e.detail || 'LLM 服务不可用，无法生成题目'
    throw e
  } finally {
    loading.value = false
  }
}

// ===== 提示 =====
async function getHint() {
  if (game.hintsUsed >= game.settings.total_hints) return
  const hints = game.puzzle.hints || []
  if (game.hintsUsed < hints.length) {
    successMsg.value = `💡 提示 ${game.hintsUsed + 1}: ${hints[game.hintsUsed]}`
    game.hintsUsed++
    setTimeout(() => successMsg.value = '', 5000)
  } else {
    errorMsg.value = '没有更多提示了'
  }
}

// ===== 提交答案 =====
async function submitAnswer() {
  if (!myAnswer.value.trim()) return
  submittingAnswer.value = true
  try {
    const story = `情境：${game.puzzle.situation}\n真相：${game.puzzle.truth}`
    const data = await api.semanticJudge(story, `玩家答案：${myAnswer.value.trim()}。这个答案是否正确揭示了真相？`)

    const j = data.judgment
    const correct = j.answer === 'Yes' && j.confidence >= 0.7

    game.result = correct ? 'correct' : 'wrong'
    game.feedback = j.reason || (correct ? '正确！' : '答案不正确')
    game.status = 'finished'
    game.endTime = new Date().toISOString()
    showAnswerInput.value = false

    if (correct) localStorage.removeItem('turtle_soup_single_progress')
  } catch (e) {
    errorMsg.value = e.detail || '验证答案失败'
  } finally {
    submittingAnswer.value = false
  }
}

// ===== 保存进度 =====
function saveProgress() {
  if (game.status !== 'playing' || !game.started) return
  saving.value = true
  try {
    localStorage.setItem('turtle_soup_single_progress', JSON.stringify({
      puzzle: game.puzzle,
      settings: game.settings,
      questions: game.questions,
      hintsUsed: game.hintsUsed,
      status: game.status,
      startTime: game.startTime,
      timestamp: new Date().toISOString()
    }))
    successMsg.value = '💾 已保存'
    setTimeout(() => successMsg.value = '', 2000)
  } catch {
    errorMsg.value = '保存失败'
  } finally {
    saving.value = false
  }
}

// ===== 退出 =====
function handleExitClick() {
  if (game.started && game.status === 'playing') {
    showExitDialog.value = true
  } else {
    exitToMenu()
  }
}

function confirmExit() {
  showExitDialog.value = false
  exitToMenu()
}

function exitToMenu() {
  game.status = 'finished'
  currentView.value = 'menu'
}

// ===== 历史 =====
async function loadHistory() {
  loading.value = true
  try {
    const data = await api.getHistory()
    gameHistory.value = data.history || []
    showHistoryPanel.value = true
  } catch {
    errorMsg.value = '加载历史失败'
  } finally {
    loading.value = false
  }
}

// ===== 工具函数 =====
function handleClose() { emit('close') }

function getDifficultyText(d) {
  return { easy: '简单', medium: '中等', hard: '困难' }[d] || d
}

function formatDate(s) {
  return s ? new Date(s).toLocaleDateString('zh-CN') : '-'
}

function calcDuration() {
  if (!game.startTime) return '-'
  const ms = (game.endTime ? new Date(game.endTime) : new Date()) - new Date(game.startTime)
  const m = Math.floor(ms / 60000)
  const s = Math.floor((ms % 60000) / 1000)
  return m > 0 ? `${m}分${s}秒` : `${s}秒`
}

function scrollBottom() {
  nextTick(() => {
    if (questionsListRef.value) questionsListRef.value.scrollTop = questionsListRef.value.scrollHeight
  })
}
</script>

<style scoped>
.turtle-soup-modal {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  background: rgba(0,0,0,0.85);
  backdrop-filter: blur(12px);
  z-index: 9999;
  padding: 20px;
}

.turtle-soup-container {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  border-radius: 24px;
  box-shadow: 0 25px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.1) inset;
  overflow-y: auto;
  position: fixed;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  max-height: 90vh;
  max-width: 700px;
  width: 90vw;
  transition: box-shadow 0.3s;
}

.turtle-soup-container.full-screen {
  max-width: 1200px;
  width: 95vw;
  max-height: 95vh;
}

/* ===== 拖拽手柄 ===== */
.drag-handle {
  position: sticky;
  top: 0;
  z-index: 15;
  text-align: center;
  padding: 8px 0 4px;
  cursor: grab;
  user-select: none;
  font-size: 20px;
  color: rgba(255,255,255,0.3);
  letter-spacing: 4px;
  transition: color 0.2s;
}

.drag-handle:hover {
  color: rgba(255,255,255,0.7);
}

.drag-handle:active {
  cursor: grabbing;
}

/* ===== 关闭按钮 ===== */
.close-btn {
  position: absolute;
  top: 12px; right: 16px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  color: white;
  font-size: 20px;
  width: 36px; height: 36px;
  border-radius: 50%;
  cursor: pointer;
  z-index: 10;
  transition: all 0.2s;
}
.close-btn:hover {
  background: rgba(239,68,68,0.2);
  transform: rotate(90deg);
}

/* ===== 菜单 ===== */
.menu-view {
  padding: 20px 40px 40px;
  max-width: 700px;
  margin: 0 auto;
}

.game-header {
  text-align: center;
  margin-bottom: 30px;
}
.game-header h1 {
  font-size: 34px;
  font-weight: 800;
  background: linear-gradient(135deg, #22c55e, #4ade80);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}
.subtitle {
  font-size: 15px;
  color: rgba(255,255,255,0.45);
}

.llm-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  margin-top: 12px;
}
.llm-status.available {
  background: rgba(34,197,94,0.15);
  border: 1px solid rgba(34,197,94,0.3);
  color: #4ade80;
}
.llm-status.unavailable {
  background: rgba(239,68,68,0.15);
  border: 1px solid rgba(239,68,68,0.3);
  color: #f87171;
}
.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}
.llm-status.available .status-dot { background: #22c55e; box-shadow: 0 0 8px rgba(34,197,94,0.5); }
.llm-status.unavailable .status-dot { background: #ef4444; box-shadow: 0 0 8px rgba(239,68,68,0.5); }

@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }

/* ===== 按钮组 ===== */
.quick-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 25px;
}

.action-btn {
  padding: 14px 28px;
  border: none;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
}
.action-btn.primary {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: white;
  box-shadow: 0 8px 25px rgba(34,197,94,0.3);
}
.action-btn.primary:hover { transform: translateY(-3px); box-shadow: 0 12px 35px rgba(34,197,94,0.45); }
.action-btn.secondary {
  background: rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.75);
  border: 1px solid rgba(255,255,255,0.12);
}
.action-btn.secondary:hover { background: rgba(255,255,255,0.12); color: white; transform: translateY(-2px); }

/* ===== 保存进度卡片 ===== */
.saved-progress-card {
  background: linear-gradient(135deg, rgba(34,197,94,0.1), rgba(16,185,129,0.1));
  border: 1px solid rgba(34,197,94,0.25);
  border-radius: 14px;
  padding: 18px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
}
.progress-icon { font-size: 32px; flex-shrink: 0; }
.progress-info { flex: 1; }
.progress-info h4 { color: #4ade80; font-size: 14px; margin-bottom: 4px; }
.progress-info p { color: rgba(255,255,255,0.6); font-size: 12px; margin: 2px 0; }

/* ===== 历史 & 规则 ===== */
.history-panel, .rules-panel {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  padding: 22px;
  margin-top: 20px;
}
.history-panel h3, .rules-panel h3 { color: white; font-size: 17px; margin-bottom: 14px; }
.history-list { max-height: 260px; overflow-y: auto; margin-bottom: 12px; }
.history-item {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 8px;
}
.history-main { display: flex; justify-content: space-between; margin-bottom: 6px; }
.puzzle-title { font-weight: 600; color: #60a5fa; font-size: 14px; }
.winner { color: #fbbf24; font-weight: 600; font-size: 13px; }
.history-meta { display: flex; gap: 14px; font-size: 11px; color: rgba(255,255,255,0.35); }
.empty-state { text-align: center; padding: 25px; color: rgba(255,255,255,0.35); }

.rules-content { color: rgba(255,255,255,0.75); line-height: 1.7; font-size: 14px; margin-bottom: 16px; }
.rules-content ul { padding-left: 20px; }
.rules-content li { margin-bottom: 6px; }

.tips-section {
  background: rgba(99,102,241,0.08);
  border: 1px solid rgba(99,102,241,0.15);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}
.tips-section h4 { color: #a5b4fc; font-size: 14px; margin-bottom: 10px; }
.tips-section ul { list-style: none; padding: 0; }
.tips-section li { padding: 4px 0 4px 18px; position: relative; color: rgba(255,255,255,0.7); font-size: 13px; }
.tips-section li::before { content: '•'; position: absolute; left: 0; color: #818cf8; }

/* ===== 游戏界面 ===== */
.playing-view {
  padding: 16px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 80vh;
}

.playing-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.back-btn {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.7);
  padding: 7px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}
.back-btn:hover { background: rgba(255,255,255,0.1); color: white; }

.game-status-bar { display: flex; gap: 16px; flex-wrap: wrap; }
.status-item { color: rgba(255,255,255,0.6); font-size: 13px; font-weight: 500; }

.difficulty-badge { padding: 3px 10px; border-radius: 8px; font-size: 12px; font-weight: 600; }
.difficulty-badge.easy { background: rgba(34,197,94,0.2); color: #4ade80; }
.difficulty-badge.medium { background: rgba(245,158,11,0.2); color: #fbbf24; }
.difficulty-badge.hard { background: rgba(239,68,68,0.2); color: #f87171; }

/* 情境 */
.situation-panel {
  background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(139,92,246,0.12));
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 14px;
  padding: 20px;
}
.panel-label { color: #a5b4fc; font-size: 13px; font-weight: 600; margin-bottom: 10px; letter-spacing: 0.5px; }
.situation-text {
  color: white; font-size: 16px; line-height: 1.7; font-weight: 500;
  text-align: center; padding: 14px; background: rgba(0,0,0,0.2); border-radius: 10px;
}
.puzzle-title-badge {
  display: inline-block;
  background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.2));
  border: 1px solid rgba(99,102,241,0.3);
  color: #a5b4fc;
  padding: 5px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  margin-top: 10px;
}

/* QA 面板 */
.single-qa-panel {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  padding: 18px;
  min-height: 350px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.waiting-state { text-align: center; padding: 50px 20px; color: rgba(255,255,255,0.5); }
.waiting-icon { font-size: 48px; margin-bottom: 12px; }

.active-game { flex: 1; display: flex; flex-direction: column; }

/* 提问输入 */
.question-input-area { margin-bottom: 16px; }
.input-row { display: flex; gap: 10px; }
.question-input {
  flex: 1;
  padding: 12px 16px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 10px;
  color: white; font-size: 14px; outline: none;
  transition: border-color 0.2s;
}
.question-input:focus { border-color: #22c55e; box-shadow: 0 0 0 3px rgba(34,197,94,0.15); }
.question-input::placeholder { color: rgba(255,255,255,0.3); }
.input-hint { color: rgba(255,255,255,0.3); font-size: 12px; margin-top: 6px; font-style: italic; }

/* 问答记录 */
.questions-history { flex: 1; margin-bottom: 14px; overflow: hidden; display: flex; flex-direction: column; }
.questions-list { flex: 1; overflow-y: auto; padding-right: 6px; max-height: 220px; }
.question-item {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 6px;
}
.question-item.mine { border-color: rgba(99,102,241,0.3); background: rgba(99,102,241,0.05); }
.q-player { font-size: 11px; color: #818cf8; font-weight: 600; margin-bottom: 4px; }
.q-content { color: rgba(255,255,255,0.85); font-size: 14px; margin-bottom: 5px; line-height: 1.4; }
.q-answer { display: inline-block; padding: 2px 10px; border-radius: 6px; font-size: 13px; font-weight: 600; }
.q-answer.是, .q-answer.Yes { background: rgba(34,197,94,0.2); color: #4ade80; }
.q-answer.否, .q-answer.No { background: rgba(239,68,68,0.2); color: #f87171; }
.q-answer.无关, .q-answer.Unknown { background: rgba(156,163,175,0.2); color: #94a3b8; }
.q-reason { color: rgba(255,255,255,0.35); font-size: 11px; font-style: italic; margin-top: 3px; }
.empty-questions { text-align: center; padding: 25px; color: rgba(255,255,255,0.25); font-style: italic; }

/* 操作按钮 */
.action-buttons { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }

/* 答案输入 */
.answer-input-area {
  background: rgba(0,0,0,0.2);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 16px;
  margin-top: 12px;
}
.answer-textarea {
  width: 100%;
  padding: 10px 14px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 8px;
  color: white; font-size: 14px; outline: none; resize: vertical;
  font-family: inherit; margin-bottom: 10px;
}
.answer-textarea::placeholder { color: rgba(255,255,255,0.3); }
.answer-actions { display: flex; gap: 8px; justify-content: flex-end; }

/* 通用按钮 */
.btn {
  padding: 10px 20px;
  border: none; border-radius: 10px;
  font-size: 13px; font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
}
.btn.primary { background: linear-gradient(135deg, #22c55e, #16a34a); color: white; }
.btn.secondary { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.7); border: 1px solid rgba(255,255,255,0.1); }
.btn.success { background: linear-gradient(135deg, #22c55e, #16a34a); color: white; }
.btn.warning { background: linear-gradient(135deg, #f59e0b, #d97706); color: white; }
.btn.danger { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; }
.btn.info { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; }
.btn.large { padding: 14px 28px; font-size: 15px; }
.btn:hover:not(:disabled) { transform: translateY(-2px); filter: brightness(1.1); }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* 结束状态 */
.finished-state { text-align: center; padding: 24px 16px; }
.winner-announcement { font-size: 22px; font-weight: 700; color: #fbbf24; margin-bottom: 20px; text-shadow: 0 0 20px rgba(251,191,36,0.3); }
.winner-announcement.correct { color: #4ade80; text-shadow: 0 0 20px rgba(74,222,128,0.3); }
.truth-reveal {
  background: linear-gradient(135deg, rgba(34,197,94,0.1), rgba(16,185,129,0.1));
  border: 1px solid rgba(34,197,94,0.2);
  border-radius: 12px;
  padding: 18px;
  margin: 16px 0;
}
.truth-text { color: #4ade80; font-size: 15px; line-height: 1.7; text-align: left; }
.result-analysis {
  background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(37,99,235,0.1));
  border: 1px solid rgba(59,130,246,0.2);
  border-radius: 10px;
  padding: 14px;
  margin: 14px 0;
}
.feedback-text { color: rgba(255,255,255,0.75); line-height: 1.6; font-size: 13px; }
.game-stats { display: flex; justify-content: center; gap: 28px; margin: 16px 0; flex-wrap: wrap; }
.stat-item { text-align: center; }
.stat-label { display: block; color: rgba(255,255,255,0.4); font-size: 11px; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
.stat-value { font-size: 22px; font-weight: 700; color: white; }
.finished-actions { display: flex; gap: 10px; justify-content: center; margin-top: 20px; }

/* 退出确认对话框 */
.confirm-dialog-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.75);
  backdrop-filter: blur(8px);
  z-index: 10001;
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.confirm-dialog {
  background: linear-gradient(135deg, #1e293b, #0f172a);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 18px;
  padding: 28px;
  max-width: 420px;
  width: 95vw;
  box-shadow: 0 25px 80px rgba(0,0,0,0.6);
  animation: dialogIn 0.3s cubic-bezier(0.34,1.56,0.64,1);
}
@keyframes dialogIn {
  from { opacity: 0; transform: scale(0.9) translateY(-20px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.confirm-dialog h3 { color: white; font-size: 18px; margin-bottom: 12px; }
.confirm-dialog p { color: rgba(255,255,255,0.7); font-size: 14px; line-height: 1.5; margin-bottom: 20px; }
.dialog-footer { display: flex; gap: 10px; justify-content: flex-end; }

.dialog-fade-enter-active, .dialog-fade-leave-active { transition: opacity 0.25s ease; }
.dialog-fade-enter-from, .dialog-fade-leave-to { opacity: 0; }

/* 加载 & 提示 */
.loading-overlay {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.8);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  z-index: 200; border-radius: 24px;
}
.spinner {
  width: 40px; height: 40px;
  border: 3px solid rgba(255,255,255,0.1);
  border-top-color: #22c55e;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}
@keyframes spin { to { transform: rotate(360deg); } }

.error-toast, .success-toast {
  position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
  padding: 12px 24px; border-radius: 10px;
  z-index: 10000; font-size: 13px; font-weight: 600;
  animation: slideDown 0.3s ease both;
  backdrop-filter: blur(12px);
  max-width: 90vw; text-align: center;
}
.error-toast { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.25); }
.success-toast { background: rgba(34,197,94,0.15); color: #86efac; border: 1px solid rgba(34,197,94,0.25); }
@keyframes slideDown {
  from { opacity: 0; transform: translateX(-50%) translateY(-20px); }
  to { opacity: 1; transform: translateX(-50%) translateY(0); }
}

/* 滚动条 */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); border-radius: 3px; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

/* 响应式 */
@media screen and (max-width: 767px) {
  .turtle-soup-container {
    width: 98vw;
    max-height: 96vh;
    border-radius: 16px;
  }
  .menu-view { padding: 20px 16px 30px; }
  .quick-actions { flex-direction: column; gap: 10px; }
  .action-btn { width: 100%; padding: 14px 20px; font-size: 15px; }
  .playing-view { padding: 12px 10px; gap: 12px; }
  .playing-header { flex-direction: column; gap: 10px; }
  .input-row { flex-direction: column; }
  .action-buttons { flex-direction: column; }
  .action-buttons .btn { width: 100%; padding: 12px 16px; }
  .question-input { font-size: 16px; }
  .answer-textarea { font-size: 16px; }
  .saved-progress-card { flex-direction: column; text-align: center; }
  .confirm-dialog-overlay { padding: 10px; align-items: flex-end; }
  .confirm-dialog { max-width: 100%; width: 100%; border-radius: 16px 16px 0 0; }
  .dialog-footer { flex-direction: column-reverse; }
  .dialog-footer .btn { width: 100%; }
}

@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
</style>
