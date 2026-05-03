<template>
  <div class="turtle-soup-modal" @click.self="handleClose">
    <div class="turtle-soup-container" :class="{ 'full-screen': currentView !== 'menu' }">
      <!-- 关闭按钮 -->
      <button class="close-btn" @click="handleClose" v-if="currentView === 'menu'">✕</button>
      
      <!-- 主菜单 -->
      <div v-if="currentView === 'menu'" class="menu-view">
        <!-- 标题区域 -->
        <div class="game-header">
          <h1>🐢 海龟汤游戏</h1>
          <p class="subtitle">推理谜题 · 智慧对决</p>
          
          <!-- LLM状态和模式指示器（权限感知） -->
          <div class="mode-indicator" :class="systemMode">
            <div class="mode-badge">
              <span class="mode-icon">{{ systemMode === 'full_ai' ? '🚀' : '🟢' }}</span>
              <span class="mode-text">{{ llmStatusMessage }}</span>
            </div>
            
            <!-- 模式详细说明 -->
            <div class="mode-details" v-if="modeDescription">
              <p class="mode-description">{{ modeDescription }}</p>
            </div>
            
            <!-- 系统保证信息 -->
            <div class="guarantees-info" v-if="Object.keys(guarantees).length > 0">
              <div class="guarantee-item" v-for="(value, key) in guarantees" :key="key">
                {{ value }}
              </div>
            </div>
          </div>
        </div>

        <!-- 快速操作按钮 -->
        <div class="quick-actions">
          <button 
            class="action-btn primary"
            @click="createNewGame"
          >
            🎮 {{ systemMode === 'full_ai' ? '开始新游戏 (AI增强)' : '开始新游戏' }}
          </button>
          
          <button 
            class="action-btn secondary"
            @click="showRules = true"
          >
            📖 游戏规则
          </button>
          
          <button 
            class="action-btn secondary"
            @click="loadHistory"
          >
            📜 历史记录
          </button>
        </div>

        <!-- 当前游戏状态 -->
        <div v-if="currentGame" class="current-game-card">
          <h3>🎯 进行中的游戏</h3>
          <div class="game-info">
            <div class="info-item">
              <span class="label">题目：</span>
              <span class="value">{{ currentGame.puzzle?.title || '未知' }}</span>
            </div>
            <div class="info-item">
              <span class="label">难度：</span>
              <span class="value difficulty-badge" :class="currentGame.puzzle?.difficulty">
                {{ getDifficultyText(currentGame.puzzle?.difficulty) }}
              </span>
            </div>
            <div class="info-item">
              <span class="label">玩家：</span>
              <span class="value">{{ currentGame.players?.length || 0 }} / {{ currentGame.settings?.max_players }}</span>
            </div>
            <div class="info-item">
              <span class="label">状态：</span>
              <span class="value status-badge" :class="currentGame.status">
                {{ getStatusText(currentGame.status) }}
              </span>
            </div>
          </div>
          
          <div class="game-actions">
            <button 
              v-if="currentGame.status === 'waiting'"
              class="btn primary"
              @click="joinCurrentGame"
            >
              加入游戏
            </button>
            <button 
              v-if="currentGame.status === 'waiting' && isHost"
              class="btn success"
              @click="startGame"
            >
              开始游戏
            </button>
            <button 
              v-if="currentGame.status === 'playing'"
              class="btn primary"
              @click="continueGame"
            >
              继续游戏
            </button>
            <button 
              class="btn danger"
              @click="leaveGame"
            >
              离开游戏
            </button>
          </div>
        </div>

        <!-- 历史记录 -->
        <div v-if="showHistoryPanel" class="history-panel">
          <h3>📜 游戏历史</h3>
          <div v-if="gameHistory.length === 0" class="empty-state">
            暂无游戏记录
          </div>
          <div v-else class="history-list">
            <div 
              v-for="(record, index) in gameHistory" 
              :key="index"
              class="history-item"
            >
              <div class="history-main">
                <span class="puzzle-title">{{ record.puzzle_title }}</span>
                <span class="winner">🏆 {{ record.winner }}</span>
              </div>
              <div class="history-meta">
                <span>玩家: {{ record.players?.join(', ') || '未知' }}</span>
                <span>时长: {{ record.duration || '-' }}</span>
                <span>{{ formatDate(record.finished_at) }}</span>
              </div>
            </div>
          </div>
          <button class="btn secondary" @click="showHistoryPanel = false">关闭</button>
        </div>

        <!-- 游戏规则 -->
        <div v-if="showRules" class="rules-panel">
          <h3>📖 海龟汤游戏规则</h3>
          <div class="rules-content" v-html="gameRules"></div>
          <div class="tips-section">
            <h4>💡 游戏技巧</h4>
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

      <!-- 游戏创建界面 -->
      <div v-if="currentView === 'create'" class="create-view">
        <h2>🎮 创建新游戏</h2>
        
        <div class="form-group">
          <label>游戏难度</label>
          <select v-model="newGameSettings.difficulty" class="form-select">
            <option value="easy">简单 - 适合新手</option>
            <option value="medium">中等 - 需要一定推理能力</option>
            <option value="hard">困难 - 高级玩家的挑战</option>
          </select>
        </div>

        <div class="form-group">
          <label>最大提问次数</label>
          <input 
            type="range" 
            v-model.number="newGameSettings.max_questions"
            min="10" 
            max="50" 
            step="5"
            class="range-slider"
          >
          <div class="range-value">{{ newGameSettings.max_questions }} 次</div>
        </div>

        <div class="form-group">
          <label>最大玩家数</label>
          <input 
            type="range" 
            v-model.number="newGameSettings.max_players"
            min="2" 
            max="8" 
            step="1"
            class="range-slider"
          >
          <div class="range-value">{{ newGameSettings.max_players }} 人</div>
        </div>

        <div class="create-actions">
          <button class="btn secondary" @click="currentView = 'menu'">返回</button>
          <button 
            class="btn primary" 
            @click="confirmCreateGame"
            :disabled="creating"
          >
            {{ creating ? '创建中...' : '确认创建' }}
          </button>
        </div>
      </div>

      <!-- 游戏进行界面 -->
      <div v-if="currentView === 'playing'" class="playing-view">
        <!-- 游戏信息栏 -->
        <div class="playing-header">
          <button class="back-btn" @click="exitToMenu">← 返回菜单</button>
          <div class="game-status-bar">
            <span class="status-item">
              📝 提问: {{ gameData.current_question_count }}/{{ gameData.settings?.max_questions }}
            </span>
            <span class="status-item">
              👥 玩家: {{ gameData.players?.length }}
            </span>
            <span class="status-item difficulty-badge" :class="gameData.puzzle?.difficulty">
              {{ getDifficultyText(gameData.puzzle?.difficulty) }}
            </span>
          </div>
        </div>

        <!-- 情境展示区 -->
        <div class="situation-panel">
          <div class="panel-label">📋 情境描述</div>
          <div class="situation-text">
            {{ gameData.puzzle?.situation || '加载中...' }}
          </div>
          <div class="situation-hint" v-if="!gameStarted">
            点击"开始游戏"后，所有玩家将看到这个情境并开始提问
          </div>
        </div>

        <!-- 玩家列表 -->
        <div class="players-panel">
          <div class="panel-label">👥 玩家列表 ({{ gameData.players?.length }}人)</div>
          <div class="players-list">
            <div 
              v-for="(player, index) in gameData.players" 
              :key="index"
              class="player-item"
              :class="{ host: player.username === gameData.host }"
            >
              <span class="player-avatar">👤</span>
              <span class="player-name">{{ player.username }}</span>
              <span class="player-role" v-if="player.username === gameData.host">房主</span>
              <span class="player-questions">{{ player.questions_asked }}问</span>
            </div>
          </div>
          
          <!-- 邀请玩家 -->
          <div v-if="gameData.status === 'waiting'" class="invite-section">
            <button class="btn small primary" @click="showInvitePanel = true">
              📨 邀请玩家
            </button>
          </div>
        </div>

        <!-- 问题与回答区 -->
        <div class="qa-panel">
          <!-- 未开始时的提示 -->
          <div v-if="!gameStarted && gameData.status === 'waiting'" class="waiting-state">
            <div class="waiting-icon">⏳</div>
            <p>等待房主开始游戏...</p>
            <button 
              v-if="isHost" 
              class="btn primary large"
              @click="startGamePlay"
            >
              🎮 开始游戏！
            </button>
          </div>

          <!-- 游戏进行中 -->
          <div v-if="gameStarted || gameData.status === 'playing'" class="active-game">
            <!-- 提问输入区 -->
            <div class="question-input-area">
              <div class="panel-label">❓ 你的问题（只能用是/否/无关回答）</div>
              <div class="input-row">
                <input 
                  type="text" 
                  v-model="currentQuestion"
                  placeholder="输入你的问题..."
                  @keypress.enter="submitQuestion"
                  :disabled="!isMyTurn || submittingQuestion"
                  class="question-input"
                >
                <button 
                  class="btn primary"
                  @click="submitQuestion"
                  :disabled="!isMyTurn || submittingQuestion || !currentQuestion.trim()"
                >
                  {{ submittingQuestion ? '提交中...' : '提问' }}
                </button>
              </div>
              <div class="input-hint" v-if="!isMyTurn && gameStarted">
                请等待其他玩家提问...
              </div>
            </div>

            <!-- 问题历史 -->
            <div class="questions-history">
              <div class="panel-label">💬 问题记录 ({{ gameData.questions?.length || 0 }})</div>
              <div class="questions-list" ref="questionsListRef">
                <div 
                  v-for="(q, index) in gameData.questions" 
                  :key="index"
                  class="question-item"
                  :class="{ mine: q.player === username }"
                >
                  <div class="q-player">{{ q.player }}</div>
                  <div class="q-content">{{ q.question }}</div>
                  <div class="q-answer" :class="q.answer?.toLowerCase()">
                    {{ q.answer || '...' }}
                  </div>
                  <div class="q-reason" v-if="q.reason">{{ q.reason }}</div>
                </div>
                
                <div v-if="(!gameData.questions || gameData.questions.length === 0)" class="empty-questions">
                  还没有问题，开始提问吧！
                </div>
              </div>
            </div>

            <!-- 操作按钮组 -->
            <div class="action-buttons">
              <button 
                class="btn warning"
                @click="getHint"
                :disabled="hintsUsed >= totalHints"
              >
                💡 获取提示 ({{ totalHints - hintsUsed }}次)
              </button>
              
              <button 
                class="btn success"
                @click="showAnswerInput = true"
              >
                🎯 我知道答案了！
              </button>
              
              <button 
                class="btn danger"
                @click="confirmExitGame"
              >
                🚪 退出游戏
              </button>
            </div>

            <!-- 答案输入框 -->
            <div v-if="showAnswerInput" class="answer-input-area">
              <div class="panel-label">✍️ 输入你的完整答案</div>
              <textarea 
                v-model="myAnswer"
                placeholder="根据你的推理，写出完整的故事真相..."
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
                  {{ submittingAnswer ? '判断中...' : '提交答案' }}
                </button>
              </div>
            </div>
          </div>

          <!-- 游戏结束 -->
          <div v-if="gameData.status === 'finished'" class="finished-state">
            <div class="winner-announcement" v-if="gameData.winner">
              🎉 恭喜！<strong>{{ gameData.winner }}</strong> 成功猜出了真相！
            </div>
            
            <div class="truth-reveal">
              <div class="panel-label">🔍 完整真相</div>
              <div class="truth-text">
                {{ gameData.puzzle?.truth }}
              </div>
            </div>

            <div class="game-stats">
              <div class="stat-item">
                <span class="stat-label">总提问数</span>
                <span class="stat-value">{{ gameData.current_question_count }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">使用提示</span>
                <span class="stat-value">{{ hintsUsed }}次</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">参与玩家</span>
                <span class="stat-value">{{ gameData.players?.length }}人</span>
              </div>
            </div>

            <div class="finished-actions">
              <button class="btn primary" @click="createNewGame">🔄 再来一局</button>
              <button class="btn secondary" @click="exitToMenu">🏠 返回菜单</button>
            </div>
          </div>
        </div>

        <!-- 邀请面板 -->
        <div v-if="showInvitePanel" class="invite-overlay">
          <div class="invite-panel">
            <h3>📨 邀请玩家加入</h3>
            
            <div class="online-users-list">
              <div 
                v-for="user in onlineUsers" 
                :key="user.uid || user.username"
                class="user-item"
              >
                <label class="user-checkbox">
                  <input 
                    type="checkbox" 
                    :value="user.username || user.nickname"
                    v-model="selectedInvitees"
                  >
                  <span class="user-info">
                    <img 
                      :src="user.avatar_url || 'https://via.placeholder.com/32'" 
                      class="user-avatar-sm"
                      alt=""
                    >
                    <span class="user-name">{{ user.nickname || user.username }}</span>
                  </span>
                </label>
              </div>
            </div>

            <div v-if="onlineUsers.length === 0" class="no-online-users">
              暂无在线用户可邀请
            </div>

            <div class="invite-actions">
              <button class="btn secondary" @click="showInvitePanel = false">取消</button>
              <button 
                class="btn primary"
                @click="sendInvites"
                :disabled="selectedInvitees.length === 0 || sendingInvites"
              >
                {{ sendingInvites ? '发送中...' : `发送邀请 (${selectedInvitees.length}人)` }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-overlay">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>

      <!-- 错误提示 -->
      <div v-if="errorMessage" class="error-toast" @click="errorMessage = ''">
        ⚠️ {{ errorMessage }}
      </div>

      <!-- 成功提示 -->
      <div v-if="successMessage" class="success-toast" @click="successMessage = ''">
        ✅ {{ successMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import api from '../utils/api'

const props = defineProps({
  username: {
    type: String,
    required: true
  },
  token: {
    type: String,
    required: true
  },
  onlineUsers: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close'])

// 视图状态
const currentView = ref('menu') // menu, create, playing

// 权限和模式状态（新增）
const systemMode = ref('preset_mode') // 'full_ai' 或 'preset_mode'
const modeDescription = ref('')
const guarantees = ref({})
const llmAvailable = ref(false)
const llmStatusMessage = ref('检查中...')
const canUsePreset = computed(() => true) // 总是可以使用预设题目

// 游戏数据
const currentGame = ref(null)
const gameData = ref({})
const gameHistory = ref([])
const gameRules = ref('')

// UI状态
const showRules = ref(false)
const showHistoryPanel = ref(false)
const showInvitePanel = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// 创建游戏设置
const newGameSettings = reactive({
  difficulty: 'medium',
  max_questions: 20,
  max_players: 4
})
const creating = ref(false)

// 游戏进行状态
const currentQuestion = ref('')
const myAnswer = ref('')
const showAnswerInput = ref(false)
const submittingQuestion = ref(false)
const submittingAnswer = ref(false)
const hintsUsed = ref(0)
const totalHints = ref(3)
const gameStarted = ref(false)

// 邀请相关
const selectedInvitees = ref([])
const sendingInvites = ref(false)

// Refs
const questionsListRef = ref(null)

// 计算属性
const isHost = computed(() => gameData.value.host === props.username)
const isMyTurn = computed(() => {
  // 简化：轮流提问或允许同时提问
  return gameData.value.status === 'playing'
})

// 初始化
onMounted(async () => {
  await checkSystemStatus()
  await loadRules()
})

// ==================== 系统状态检查（使用权限感知API）====================

async function checkSystemStatus() {
  try {
    const status = await api.checkTurtleSoupStatus()
    
    // 更新权限状态
    llmAvailable.value = status.llm_available || false
    systemMode.value = status.current_mode || 'preset_mode'
    modeDescription.value = status.mode_description || ''
    guarantees.value = status.guarantees || {}
    
    // 根据模式设置状态消息
    if (status.llm_available) {
      llmStatusMessage.value = '🚀 AI增强模式 - 智能题目生成'
    } else {
      llmStatusMessage.value = '✅ 基础模式 - 使用预设题目库'
      
      // 显示友好的降级提示（不是错误！）
      if (status.mode_description) {
        successMessage.value = status.mode_description
        setTimeout(() => successMessage.value = '', 4000)
      }
    }
  } catch (error) {
    console.warn('系统状态检查失败，使用基础模式')
    llmAvailable.value = false
    systemMode.value = 'preset_mode'
    modeDescription.value = '✅ 基础模式 - 所有功能正常运行'
    llmStatusMessage.value = '✅ 基础模式'
    guarantees.value = {
      system_stability: '✅ 游戏功能正常可用',
      feature_access: '✅ 可创建和进行游戏'
    }
  }
}

async function loadRules() {
  try {
    const data = await api.getRules()
    gameRules.value = data.rules || ''
  } catch (error) {
    console.warn('加载规则失败，使用默认规则')
    gameRules.value = getDefaultRules()
  }
}

function getDefaultRules() {
  return `
    <h3>🎯 游戏目标</h3>
    <p>通过提问"是/否"问题来推断出一个完整故事的真相。</p>
    
    <h3>📖 游戏流程</h3>
    <ol>
      <li><strong>出题</strong>：系统给出一个令人困惑的<strong>情境</strong></li>
      <li><strong>提问</strong>：玩家轮流提出只能用"是"、"否"、"无关"回答的问题</li>
      <li><strong>推理</strong>：根据问题的答案逐步还原真相</li>
      <li><strong>猜真相</strong>：当你认为已经知道真相时，可以提出你的完整解答</li>
    </ol>
    
    <h3>❓ 提问规则</h3>
    <ul>
      <li>问题必须能用"是"、"否"、"无关"来回答</li>
      <li>不能直接问"真相是什么"</li>
      <li>每个玩家每次只能问一个问题</li>
      <li>有提问次数限制</li>
    </ul>
    
    <h3>🏆 获胜条件</h3>
    <ul>
      <li>第一个正确说出完整真相的玩家获胜</li>
      <li>答案需要包含故事的关键要素</li>
    </ul>
  `
}

async function loadHistory() {
  try {
    loading.value = true
    const data = await api.getHistory()
    gameHistory.value = data.history || []
    showHistoryPanel.value = true
  } catch (error) {
    console.warn('加载历史记录失败')
    errorMessage.value = "无法加载历史记录，请稍后再试"
  } finally {
    loading.value = false
  }
}

// 游戏创建
function createNewGame() {
  currentView.value = 'create'
}

async function confirmCreateGame() {
  creating.value = true
  
  try {
    const data = await api.createGame(newGameSettings)
    
    currentGame.value = {
      id: data.game_id,
      puzzle: data.puzzle_preview,
      settings: newGameSettings,
      players: [],
      status: 'waiting'
    }
    
    successMessage.value = "游戏创建成功！等待玩家加入..."
    setTimeout(() => {
      currentView.value = 'playing'
      initializeGameData(data.game_id, data)
    }, 1000)
    
  } catch (error) {
    console.warn('创建游戏失败:', error)
    errorMessage.value = error.detail || "无法创建游戏，请稍后再试"
  } finally {
    creating.value = false
  }
}

function initializeGameData(gameId, initialData) {
  gameData.value = {
    id: gameId,
    puzzle: initialData.puzzle_preview,
    status: 'waiting',
    settings: newGameSettings,
    players: [],
    host: null,
    questions: [],
    current_question_count: 0,
    hints_used: 0,
    winner: null
  }
  
  // 自动加入游戏
  joinGame(gameId)
}

// 游戏加入和离开
async function joinGame(gameId) {
  try {
    const data = await api.joinGame(gameId, props.username)
    
    // 更新本地游戏数据
    if (!gameData.value.id) {
      await getGameStatus(gameId)
    }
    
    successMessage.value = `${props.username} 加入了游戏`
    
  } catch (error) {
    console.warn('加入游戏失败:', error)
    errorMessage.value = error.detail || "无法加入游戏，请稍后再试"
  }
}

async function joinCurrentGame() {
  if (currentGame.value?.id) {
    await joinGame(currentGame.value.id)
    currentView.value = 'playing'
  }
}

async function leaveGame() {
  if (currentGame.value?.id) {
    try {
      await api.deleteGame(currentGame.value.id)
      currentGame.value = null
      currentView.value = 'menu'
      successMessage.value = "已离开游戏"
    } catch (error) {
      console.warn('离开游戏失败:', error)
      errorMessage.value = "无法离开游戏，请稍后再试"
    }
  }
}

// 游戏控制
async function startGame() {
  if (!currentGame.value?.id) return
  
  try {
    loading.value = true
    const data = await api.startGame(currentGame.value.id, props.username)
    
    currentGame.value.status = 'playing'
    currentView.value = 'playing'
    
    // 更新游戏数据
    await getGameStatus(currentGame.value.id)
    gameStarted.value = true
    
    successMessage.value = "游戏开始！"
    
  } catch (error) {
    console.warn('开始游戏失败:', error)
    errorMessage.value = error.detail || "无法开始游戏，请稍后再试"
  } finally {
    loading.value = false
  }
}

async function startGamePlay() {
  if (!gameData.value.id) return
  
  try {
    loading.value = true
    const data = await api.startGame(gameData.value.id, props.username)
    
    gameData.value.status = 'playing'
    gameData.value.puzzle = data.puzzle
    gameStarted.value = true
    
    successMessage.value = "🎮 游戏正式开始！"
    
  } catch (error) {
    console.warn('开始游戏失败:', error)
    errorMessage.value = error.detail || "无法开始游戏，请稍后再试"
  } finally {
    loading.value = false
  }
}

function continueGame() {
  // 已经在游戏中，刷新状态即可
  gameStarted.value = true
}

// 提问功能
async function submitQuestion() {
  if (!currentQuestion.value.trim()) {
    errorMessage.value = "请输入问题"
    return
  }
  
  if (!gameData.value.id) {
    errorMessage.value = "不在游戏中"
    return
  }
  
  submittingQuestion.value = true
  
  try {
    const data = await api.askQuestion(gameData.value.id, currentQuestion.value, props.username)
    
    // 添加到本地问题列表
    if (!gameData.value.questions) {
      gameData.value.questions = []
    }
    
    gameData.value.questions.push({
      question: currentQuestion.value,
      answer: data.judgment?.answer,
      is_relevant: data.judgment?.is_relevant,
      reason: data.judgment?.reason,
      player: props.username,
      timestamp: new Date().toISOString()
    })
    
    gameData.value.current_question_count = data.total_questions
    
    currentQuestion.value = ''
    
    // 滚动到底部
    scrollToQuestionsBottom()
    
    // 显示判断结果
    if (data.judgment?.answer) {
      successMessage.value = `回答: ${data.judgment.answer}`
    }
    
  } catch (error) {
    console.warn('提问失败:', error)
    errorMessage.value = error.detail || "无法提交问题，请稍后再试"
  } finally {
    submittingQuestion.value = false
  }
}

// 提示功能
async function getHint() {
  if (!gameData.value.id) return
  
  try {
    const data = await api.getHint(gameData.value.id)
    
    if (data.success) {
      hintsUsed.value++
      successMessage.value = `💡 提示: ${data.hint}`
    } else {
      console.warn('获取提示失败:', data)
      errorMessage.value = data.message || "无法获取提示，请稍后再试"
    }
    
  } catch (error) {
    console.warn('获取提示失败:', error)
    errorMessage.value = "无法获取提示，请稍后再试"
  }
}

// 答案提交
async function submitAnswer() {
  if (!myAnswer.value.trim()) {
    errorMessage.value = "请输入答案"
    return
  }
  
  if (!gameData.value.id) {
    errorMessage.value = "不在游戏中"
    return
  }
  
  submittingAnswer.value = true
  
  try {
    const data = await api.submitAnswer(gameData.value.id, myAnswer.value, props.username)
    
    if (data.is_correct) {
      // 答案正确，游戏结束
      gameData.value.status = 'finished'
      gameData.value.winner = data.winner
      gameData.value.puzzle = {
        ...gameData.value.puzzle,
        truth: data.truth
      }
      
      successMessage.value = "🎉 恭喜！答案正确！"
      showAnswerInput.value = false
      
      // 刷新游戏状态
      await getGameStatus(gameData.value.id)
      
    } else {
      // 答案错误
      if (data.result?.hint) {
        hintsUsed.value++
        errorMessage.value = `❌ ${data.result.feedback}`
        
        // 如果有提示，也显示出来
        if (data.hint) {
          successMessage.value = `💡 提示: ${data.hint}`
        }
      } else {
        errorMessage.value = data.result?.feedback || "答案不对哦，再想想~"
      }
    }
    
    myAnswer.value = ''
    showAnswerInput.value = false
    
  } catch (error) {
    console.warn('提交答案失败:', error)
    errorMessage.value = error.detail || "无法提交答案，请稍后再试"
  } finally {
    submittingAnswer.value = false
  }
}

// 邀请功能
async function sendInvites() {
  if (!gameData.value.id || selectedInvitees.value.length === 0) {
    errorMessage.value = "请选择要邀请的玩家"
    return
  }
  
  sendingInvites.value = true
  
  try {
    const data = await api.sendInvite(gameData.value.id, selectedInvitees.value)
    
    successMessage.value = `已向 ${data.invites_sent} 位玩家发送邀请`
    showInvitePanel.value = false
    selectedInvitees.value = []
    
  } catch (error) {
    console.warn('发送邀请失败:', error)
    errorMessage.value = error.detail || "无法发送邀请，请稍后再试"
  } finally {
    sendingInvites.value = false
  }
}

// 获取游戏状态
async function getGameStatus(gameId) {
  try {
    const data = await api.getGameStatus(gameId)
    
    gameData.value = data
    
    // 更新提示数量
    if (data.puzzle?.hints) {
      totalHints.value = data.puzzle.hints.length
      hintsUsed.value = data.hints_used || 0
    }
    
    // 如果游戏已结束，显示结果
    if (data.status === 'finished') {
      gameStarted.value = false
    }
    
    return data
    
  } catch (error) {
    console.warn('获取游戏状态失败:', error)
    return null
  }
}

// UI辅助函数
function handleClose() {
  emit('close')
}

function exitToMenu() {
  currentView.value = 'menu'
  gameStarted.value = false
  currentQuestion.value = ''
  myAnswer.value = ''
  showAnswerInput.value = false
  showInvitePanel.value = false
}

function confirmExitGame() {
  if (confirm('确定要退出游戏吗？')) {
    exitToMenu()
    leaveGame()
  }
}

function getDifficultyText(difficulty) {
  const map = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return map[difficulty] || difficulty
}

function getStatusText(status) {
  const map = {
    waiting: '等待中',
    playing: '进行中',
    finished: '已结束'
  }
  return map[status] || status
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

function scrollToQuestionsBottom() {
  nextTick(() => {
    if (questionsListRef.value) {
      questionsListRef.value.scrollTop = questionsListRef.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.turtle-soup-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(12px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.turtle-soup-container {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  border-radius: 24px;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  overflow-y: auto;
  position: relative;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 90vh;
}

.turtle-soup-container.full-screen {
  max-width: 1200px;
  width: 95vw;
  max-height: 95vh;
}

.close-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 24px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
  z-index: 10;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  transform: rotate(90deg);
}

/* 菜单视图 */
.menu-view {
  padding: 40px;
  max-width: 700px;
  margin: 0 auto;
}

.game-header {
  text-align: center;
  margin-bottom: 35px;
}

.game-header h1 {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(135deg, #22c55e, #4ade80);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 10px;
}

.subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 500;
}

/* 权限模式指示器（新增） */
.mode-indicator {
  margin-top: 20px;
  padding: 18px;
  border-radius: 14px;
  transition: all 0.3s ease;
}

.mode-indicator.full_ai {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15));
  border: 1px solid rgba(99, 102, 241, 0.3);
}

.mode-indicator.preset_mode {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.12), rgba(16, 185, 129, 0.12));
  border: 1px solid rgba(34, 197, 94, 0.25);
}

.mode-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 12px;
}

.mode-icon {
  font-size: 24px;
}

.mode-text {
  font-size: 15px;
  font-weight: 600;
  color: white;
}

.mode-details {
  margin-bottom: 12px;
}

.mode-description {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
  text-align: center;
  line-height: 1.5;
  margin: 0;
}

.guarantees-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.guarantee-item {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.65);
  padding-left: 16px;
  position: relative;
}

.guarantee-item::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #4ade80;
  font-weight: bold;
}

.llm-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  margin-top: 15px;
  transition: all 0.3s;
}

.llm-status.available {
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #4ade80;
}

.llm-status.unavailable {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.llm-status.available .status-dot {
  background: #22c55e;
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.5);
}

.llm-status.unavailable .status-dot {
  background: #ef4444;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.quick-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 30px;
}

.action-btn {
  padding: 14px 28px;
  border: none;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.action-btn.primary {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: white;
  box-shadow: 0 8px 25px rgba(34, 197, 94, 0.3);
}

.action-btn.primary:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 12px 35px rgba(34, 197, 94, 0.45);
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.action-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.12);
  color: white;
  transform: translateY(-2px);
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none !important;
}

/* 游戏卡片 */
.current-game-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 18px;
  padding: 25px;
  margin-top: 25px;
}

.current-game-card h3 {
  color: white;
  font-size: 18px;
  margin-bottom: 18px;
  font-weight: 600;
}

.game-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.info-item .label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-item .value {
  font-size: 15px;
  color: white;
  font-weight: 600;
}

.difficulty-badge {
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
}

.difficulty-badge.easy {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
}

.difficulty-badge.medium {
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
}

.difficulty-badge.hard {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
}

.status-badge.waiting {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.status-badge.playing {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
}

.status-badge.finished {
  background: rgba(168, 85, 247, 0.2);
  color: #c084fc;
}

.game-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.btn {
  padding: 11px 22px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn.primary {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: white;
}

.btn.secondary {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.btn.success {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: white;
}

.btn.warning {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
}

.btn.danger {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
}

.btn.small {
  padding: 8px 16px;
  font-size: 13px;
}

.btn.large {
  padding: 16px 32px;
  font-size: 16px;
}

.btn:hover:not(:disabled) {
  transform: translateY(-2px);
  filter: brightness(1.1);
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 历史和规则面板 */
.history-panel, .rules-panel {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 25px;
  margin-top: 25px;
}

.history-panel h3, .rules-panel h3 {
  color: white;
  font-size: 18px;
  margin-bottom: 18px;
  font-weight: 600;
}

.history-list {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 15px;
}

.history-item {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 10px;
}

.history-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.puzzle-title {
  font-weight: 600;
  color: #60a5fa;
  font-size: 15px;
}

.winner {
  color: #fbbf24;
  font-weight: 600;
  font-size: 14px;
}

.history-meta {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  flex-wrap: wrap;
}

.empty-state {
  text-align: center;
  padding: 30px;
  color: rgba(255, 255, 255, 0.4);
}

.rules-content {
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.7;
  font-size: 14px;
  margin-bottom: 20px;
}

.rules-content h3 {
  color: #60a5fa;
  font-size: 16px;
  margin: 20px 0 10px 0;
}

.tips-section {
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.15);
  border-radius: 12px;
  padding: 18px;
  margin-bottom: 20px;
}

.tips-section h4 {
  color: #a5b4fc;
  font-size: 15px;
  margin-bottom: 12px;
}

.tips-section ul {
  list-style: none;
  padding-left: 0;
}

.tips-section li {
  padding: 6px 0;
  padding-left: 20px;
  position: relative;
  color: rgba(255, 255, 255, 0.75);
  font-size: 13px;
}

.tips-section li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #818cf8;
}

/* 创建视图 */
.create-view {
  padding: 40px;
  max-width: 550px;
  margin: 0 auto;
}

.create-view h2 {
  color: white;
  font-size: 28px;
  text-align: center;
  margin-bottom: 30px;
  font-weight: 700;
}

.form-group {
  margin-bottom: 25px;
}

.form-group label {
  display: block;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
}

.form-select {
  width: 100%;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  color: white;
  font-size: 15px;
  outline: none;
  cursor: pointer;
}

.range-slider {
  width: 100%;
  margin: 10px 0;
  accent-color: #22c55e;
}

.range-value {
  text-align: center;
  color: #4ade80;
  font-weight: 600;
  font-size: 15px;
  margin-top: 8px;
}

.create-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 30px;
}

/* 游戏进行视图 */
.playing-view {
  padding: 25px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  grid-template-rows: auto 1fr auto;
  min-height: 80vh;
}

.playing-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 20px;
}

.back-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.75);
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.game-status-bar {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.status-item {
  color: rgba(255, 255, 255, 0.65);
  font-size: 13px;
  font-weight: 500;
}

.situation-panel {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(139, 92, 246, 0.12));
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 16px;
  padding: 25px;
  margin-bottom: 20px;
}

.panel-label {
  color: #a5b4fc;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  letter-spacing: 0.5px;
}

.situation-text {
  color: white;
  font-size: 17px;
  line-height: 1.7;
  font-weight: 500;
  text-align: center;
  padding: 15px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
}

.situation-hint {
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
  margin-top: 12px;
  font-style: italic;
}

.players-panel {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  padding: 20px;
  margin-bottom: 20px;
}

.players-list {
  max-height: 150px;
  overflow-y: auto;
  margin-bottom: 12px;
}

.player-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  margin-bottom: 6px;
  transition: all 0.2s;
}

.player-item:last-child {
  margin-bottom: 0;
}

.player-item.host {
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.player-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.player-avatar {
  font-size: 20px;
}

.player-name {
  flex: 1;
  color: white;
  font-weight: 600;
  font-size: 14px;
}

.player-role {
  background: #f59e0b;
  color: #78350f;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
}

.player-questions {
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
}

.invite-section {
  text-align: center;
  padding-top: 10px;
}

.qa-panel {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 20px;
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

.waiting-state {
  text-align: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.5);
}

.waiting-icon {
  font-size: 48px;
  margin-bottom: 15px;
  animation: spin 2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.active-game {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.question-input-area {
  margin-bottom: 20px;
}

.input-row {
  display: flex;
  gap: 12px;
}

.question-input {
  flex: 1;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  color: white;
  font-size: 15px;
  outline: none;
  transition: all 0.2s;
}

.question-input:focus {
  border-color: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15);
}

.question-input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.input-hint {
  color: rgba(255, 255, 255, 0.35);
  font-size: 12px;
  margin-top: 8px;
  font-style: italic;
}

.questions-history {
  flex: 1;
  margin-bottom: 20px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.questions-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
  max-height: 250px;
}

.question-item {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 12px 15px;
  margin-bottom: 8px;
  transition: all 0.2s;
}

.question-item.mine {
  border-color: rgba(99, 102, 241, 0.3);
  background: rgba(99, 102, 241, 0.05);
}

.q-player {
  font-size: 12px;
  color: #818cf8;
  font-weight: 600;
  margin-bottom: 5px;
}

.q-content {
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  margin-bottom: 6px;
  line-height: 1.5;
}

.q-answer {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
}

.q-answer.是 {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
}

.q-answer.否 {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.q-answer.无关 {
  background: rgba(156, 163, 175, 0.2);
  color: #94a3b8;
}

.q-reason {
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
  font-style: italic;
}

.empty-questions {
  text-align: center;
  padding: 30px;
  color: rgba(255, 255, 255, 0.3);
  font-style: italic;
}

.action-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 15px;
}

.answer-input-area {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 20px;
  margin-top: 15px;
}

.answer-textarea {
  width: 100%;
  padding: 12px 15px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  color: white;
  font-size: 14px;
  outline: none;
  resize: vertical;
  font-family: inherit;
  margin-bottom: 12px;
}

.answer-textarea::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.answer-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

/* 游戏结束状态 */
.finished-state {
  text-align: center;
  padding: 30px 20px;
}

.winner-announcement {
  font-size: 22px;
  font-weight: 700;
  color: #fbbf24;
  margin-bottom: 25px;
  text-shadow: 0 0 20px rgba(251, 191, 36, 0.3);
}

.truth-reveal {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(16, 185, 129, 0.1));
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 14px;
  padding: 20px;
  margin: 20px 0;
}

.truth-text {
  color: #4ade80;
  font-size: 16px;
  line-height: 1.7;
  text-align: left;
}

.game-stats {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin: 20px 0;
  flex-wrap: wrap;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  color: rgba(255, 255, 255, 0.45);
  font-size: 12px;
  margin-bottom: 5px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: white;
}

.finished-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 25px;
}

/* 邀请面板 */
.invite-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  animation: fadeIn 0.2s ease;
}

.invite-panel {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 30px;
  max-width: 450px;
  width: 95vw;
  max-height: 80vh;
  overflow-y: auto;
}

.invite-panel h3 {
  color: white;
  font-size: 20px;
  margin-bottom: 20px;
  text-align: center;
}

.online-users-list {
  max-height: 350px;
  overflow-y: auto;
  margin-bottom: 20px;
}

.user-item {
  margin-bottom: 10px;
}

.user-checkbox {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 10px;
  border-radius: 10px;
  transition: all 0.2s;
}

.user-checkbox:hover {
  background: rgba(255, 255, 255, 0.05);
}

.user-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.user-avatar-sm {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.user-name {
  color: white;
  font-size: 14px;
  font-weight: 500;
}

.no-online-users {
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  padding: 20px;
}

.invite-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

/* 加载和提示 */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 200;
  border-radius: 24px;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-top-color: #22c55e;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 15px;
}

.error-toast, .success-toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 14px 28px;
  border-radius: 12px;
  z-index: 10000;
  font-size: 14px;
  font-weight: 600;
  animation: slideDown 0.3s ease both;
  backdrop-filter: blur(12px);
  max-width: 90vw;
  text-align: center;
}

.error-toast {
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.success-toast {
  background: rgba(34, 197, 94, 0.15);
  color: #86efac;
  border: 1px solid rgba(34, 197, 94, 0.25);
}

@keyframes slideDown {
  from { opacity: 0; transform: translateX(-50%) translateY(-20px); }
  to { opacity: 1; transform: translateX(-50%) translateY(0); }
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.25);
}
</style>
