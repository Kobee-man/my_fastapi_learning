const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

// 系统权限状态缓存
let systemStatusCache = null
let statusCacheTime = 0
const STATUS_CACHE_DURATION = 5 * 60 * 1000 // 5分钟

export const api = {
  async request(url, options = {}) {
    const token = localStorage.getItem('token')
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers
      },
      ...options
    }

    try {
      const response = await fetch(`${API_BASE}${url}`, config)

      // 检查响应头中的权限信息（后端中间件添加的）
      if (response.ok) {
        const llmAvailable = response.headers.get('X-LLM-Available')
        if (llmAvailable !== null) {
          // 更新本地缓存的状态
          if (systemStatusCache) {
            systemStatusCache.llm_available = llmAvailable === 'true'
          }
        }
      }

      let data
      try {
        data = await response.json()
      } catch {
        data = {}
      }

      if (!response.ok) {
        throw { status: response.status, detail: data.detail || `请求失败 (${response.status})` }
      }

      return data
    } catch (error) {
      console.error('API Error:', error)
      // 网络错误（连接拒绝等）没有 .detail，统一格式
      if (error.detail) throw error
      throw { status: 0, detail: error.message || '网络连接失败，请检查服务是否启动' }
    }
  },

  // ==================== 系统状态和权限检查 ====================
  
  /**
   * 获取系统完整状态（公开接口，无需登录）
   * 返回详细的权限分层信息和功能可用性
   */
  async getSystemStatus() {
    try {
      // 使用缓存避免频繁请求
      const now = Date.now()
      if (systemStatusCache && (now - statusCacheTime) < STATUS_CACHE_DURATION) {
        return systemStatusCache
      }
      
      const data = await this.request('/api/status')
      systemStatusCache = data
      statusCacheTime = now
      
      return data
    } catch (error) {
      console.warn('获取系统状态失败，使用默认值')
      return this.getDefaultSystemStatus()
    }
  },

  /**
   * 获取功能列表详情
   */
  async getFeaturesList() {
    try {
      return await this.request('/api/features')
    } catch (error) {
      console.warn('获取功能列表失败')
      return null
    }
  },

  /**
   * 检查特定功能的访问权限
   */
  async checkFeatureAccess(featureName) {
    const status = await this.getSystemStatus()
    const features = status?.features || {}
    
    // 基础功能检查逻辑
    switch(featureName) {
      case 'llm':
        return {
          accessible: features.premium?.access || false,
          requires_api_key: true,
          fallback_available: features.preset_puzzles?.available || false,
          message: features.llm_config?.note || ''
        }
        
      case 'preset_games':
        return {
          accessible: features.preset_puzzles?.available || false,
          requires_auth: true,
          requires_api_key: false,
          message: features.preset_puzzles?.note || ''
        }
        
      case 'chat':
        return {
          accessible: features.authenticated?.access || false,
          requires_auth: true,
          requires_api_key: false,
          message: '需要登录'
        }
        
      default:
        return {
          accessible: true,
          requires_auth: false,
          requires_api_key: false,
          message: ''
        }
    }
  },

  /**
   * 获取默认的系统状态（当API不可用时）
   */
  getDefaultSystemStatus() {
    return {
      status: 'degraded',
      version: '2.0.0',
      timestamp: new Date().toISOString(),
      features: {
        public: { access: true, endpoints: ['/', '/login.html'] },
        authenticated: { 
          access: true, 
          requires_login: true,
          note: '基础功能可用'
        },
        premium: {
          access: false,
          requires_api_key: true,
          fallback_behavior: '使用预设题目库'
        },
        llm_config: {
          available: false,
          configured: false,
          note: 'LLM未配置 - 使用基础模式'
        },
        preset_puzzles: {
          available: true,
          count: 3,
          note: '预设题目可用'
        },
        permissions: {
          system_stable_without_api_key: true
        }
      },
      guarantees: {
        system_stability: '✅ 系统稳定运行',
        feature_access: '✅ 核心功能可用',
        note: '无API Key时自动降级到基础模式'
      },
      current_mode: 'preset_mode',
      mode_description: '✅ 基础模式 - 所有核心功能正常运行'
    }
  },

  // ==================== 用户认证 API ====================

  login(username, password) {
    return this.request('/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    })
  },

  register(username, password, nickname) {
    return this.request('/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, nickname })
    })
  },

  forgotPassword(username, newPassword) {
    return this.request('/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ username, new_password: newPassword })
    })
  },

  // ==================== 用户资料 API ====================

  getProfile() {
    return this.request('/profile')
  },

  updateNickname(nickname) {
    return this.request('/user/nickname', {
      method: 'PUT',
      body: JSON.stringify({ nickname })
    })
  },

  uploadAvatar(file) {
    const formData = new FormData()
    formData.append('file', file)
    
    return this.request('/user/avatar', {
      method: 'POST',
      headers: {}, 
      body: formData
    })
  },

  getOnlineUsers() {
    return this.request('/chat/online-users')
  },

  // ==================== 海龟汤游戏 API ====================

  /**
   * 检查海龟汤游戏服务状态
   * 返回LLM可用性和降级方案
   */
  async checkTurtleSoupStatus() {
    try {
      return await this.request('/turtle-soup/check-status', {
        method: 'POST'
      })
    } catch (error) {
      const isNetworkError = error.status === 0
      return {
        llm_available: false,
        server_reachable: !isNetworkError,
        current_mode: 'degraded',
        mode_description: isNetworkError ? '服务器未启动' : 'LLM服务不可用'
      }
    }
  },

  createGame(gameSettings) {
    return this.request('/turtle-soup/create-game', {
      method: 'POST',
      body: JSON.stringify(gameSettings)
    })
  },

  joinGame(gameId, username) {
    return this.request('/turtle-soup/join-game', {
      method: 'POST',
      body: JSON.stringify({
        game_id: gameId,
        player_username: username
      })
    })
  },

  startGame(gameId, hostUsername) {
    return this.request('/turtle-soup/start-game', {
      method: 'POST',
      body: JSON.stringify({
        game_id: gameId,
        host_username: hostUsername
      })
    })
  },

  askQuestion(gameId, question, username) {
    return this.request('/turtle-soup/ask-question', {
      method: 'POST',
      body: JSON.stringify({
        game_id: gameId,
        question: question,
        player_username: username
      })
    })
  },

  submitAnswer(gameId, answer, username) {
    return this.request('/turtle-soup/submit-answer', {
      method: 'POST',
      body: JSON.stringify({
        game_id: gameId,
        answer: answer,
        player_username: username
      })
    })
  },

  getHint(gameId) {
    return this.request(`/turtle-soup/hint?game_id=${gameId}`)
  },

  getGameStatus(gameId) {
    return this.request(`/turtle-soup/game-status/${gameId}`)
  },

  sendInvite(gameId, usernames) {
    return this.request('/turtle-soup/invite', {
      method: 'POST',
      body: JSON.stringify({
        game_id: gameId,
        invitee_usernames: usernames
      })
    })
  },

  getHistory(limit = 10) {
    return this.request(`/turtle-soup/history?limit=${limit}`)
  },

  getRules() {
    return this.request('/turtle-soup/rules')
  },

  deleteGame(gameId) {
    return this.request(`/turtle-soup/game/${gameId}`, {
      method: 'DELETE'
    })
  },

  judgeQuestion(data) {
    return this.request('/turtle-soup/judge-question', {
      method: 'POST',
      body: JSON.stringify(data)
    })
  },

  checkSinglePlayerAnswer(gameId, answer) {
    return this.request('/turtle-soup/submit-answer', {
      method: 'POST',
      body: JSON.stringify({
        game_id: gameId,
        answer: answer,
        player_username: 'single_player'
      })
    })
  },

  semanticJudge(story, question) {
    return this.request('/turtle-soup/semantic-judge', {
      method: 'POST',
      body: JSON.stringify({ story, question })
    })
  }
}

export default api
