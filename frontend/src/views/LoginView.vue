<template>
  <div class="login-page">
    <div class="bg-pattern"></div>
    
    <div class="floating-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>

    <div class="auth-container">
      <div class="auth-card">
        <!-- Alert Message -->
        <div 
          v-if="alert.show" 
          class="alert-msg" 
          :class="alert.type"
        >
          {{ alert.message }}
        </div>

        <!-- Cat Avatar -->
        <CatAvatar
          ref="catAvatarRef"
          :title="tabTitles[currentTab].title"
          :subtitle="tabTitles[currentTab].subtitle"
          @happy="handleCatHappy"
        />

        <!-- Tab Switcher -->
        <div class="tab-switcher">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="tab-btn"
            :class="{ active: currentTab === tab.id }"
            @click="switchTab(tab.id)"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Login Form -->
        <div v-show="currentTab === 'login'" class="form-panel">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <input 
              type="text" 
              v-model="forms.login.username" 
              class="form-input" 
              placeholder="请输入用户名"
              autocomplete="username"
            >
            <div class="input-glow-line"></div>
          </div>
          
          <div class="form-group">
            <label class="form-label">密码</label>
            <input 
              type="password" 
              v-model="forms.login.password" 
              class="form-input password-input"
              placeholder="请输入密码"
              autocomplete="current-password"
              @focus="handlePasswordFocus"
              @blur="handlePasswordBlur"
              @mouseenter="handlePasswordMouseEnter"
              @mouseleave="handlePasswordMouseLeave"
            >
            <div class="input-glow-line"></div>
          </div>
          
          <div class="form-group">
            <label class="form-label">安全验证</label>
            <SliderVerify 
              ref="sliderLoginRef"
              v-model="sliders.login.verified"
              @success="handleSliderSuccess('login')"
            />
          </div>
          
          <div class="forgot-link">
            <a @click="switchTab('forgot')">忘记密码？</a>
          </div>
          
          <button class="submit-btn" @click="handleLogin" :disabled="loading">
            {{ loading ? '登录中...' : '登 录' }}
          </button>
        </div>

        <!-- Register Form -->
        <div v-show="currentTab === 'register'" class="form-panel">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <input 
              type="text" 
              v-model="forms.register.username" 
              class="form-input" 
              placeholder="3-20位字母或数字"
              autocomplete="new-username"
            >
            <div class="input-glow-line"></div>
          </div>
          
          <div class="form-group">
            <label class="form-label">密码</label>
            <input 
              type="password" 
              v-model="forms.register.password" 
              class="form-input password-input"
              placeholder="至少6位密码"
              autocomplete="new-password"
              @focus="handlePasswordFocus"
              @blur="handlePasswordBlur"
              @mouseenter="handlePasswordMouseEnter"
              @mouseleave="handlePasswordMouseLeave"
            >
            <div class="input-glow-line"></div>
          </div>
          
          <div class="form-group">
            <label class="form-label">昵称（可选）</label>
            <input 
              type="text" 
              v-model="forms.register.nickname" 
              class="form-input" 
              placeholder="给自己起个名字"
              autocomplete="off"
            >
            <div class="input-glow-line"></div>
          </div>
          
          <div class="form-group">
            <label class="form-label">安全验证</label>
            <SliderVerify 
              ref="sliderRegisterRef"
              v-model="sliders.register.verified"
              @success="handleSliderSuccess('register')"
            />
          </div>
          
          <button class="submit-btn" @click="handleRegister" :disabled="loading">
            {{ loading ? '注册中...' : '注 册' }}
          </button>
        </div>

        <!-- Forgot Password Form -->
        <div v-show="currentTab === 'forgot'" class="form-panel">
          <div class="form-group">
            <label class="form-label">账号（用户名）</label>
            <input 
              type="text" 
              v-model="forms.forgot.username" 
              class="form-input" 
              placeholder="请输入注册的用户名"
            >
            <div class="input-glow-line"></div>
          </div>
          
          <div class="form-group">
            <label class="form-label">新密码</label>
            <input 
              type="password" 
              v-model="forms.forgot.newPassword" 
              class="form-input password-input"
              placeholder="设置新密码（至少6位）"
              @focus="handlePasswordFocus"
              @blur="handlePasswordBlur"
              @mouseenter="handlePasswordMouseEnter"
              @mouseleave="handlePasswordMouseLeave"
            >
            <div class="input-glow-line"></div>
          </div>
          
          <div class="form-group">
            <label class="form-label">安全验证</label>
            <SliderVerify 
              ref="sliderForgotRef"
              v-model="sliders.forgot.verified"
              @success="handleSliderSuccess('forgot')"
            />
          </div>
          
          <button class="submit-btn" @click="handleForgotPassword" :disabled="loading">
            {{ loading ? '重置中...' : '重置密码' }}
          </button>
          
          <div class="back-login">
            <a @click="switchTab('login')">&larr; 返回登录</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import CatAvatar from '../components/CatAvatar.vue'
import SliderVerify from '../components/SliderVerify.vue'

const router = useRouter()

// Refs
const catAvatarRef = ref(null)
const sliderLoginRef = ref(null)
const sliderRegisterRef = ref(null)
const sliderForgotRef = ref(null)

// State
const currentTab = ref('login')
const loading = ref(false)

const alert = reactive({
  show: false,
  message: '',
  type: 'success' // 'success' or 'error'
})

const forms = reactive({
  login: {
    username: '',
    password: ''
  },
  register: {
    username: '',
    password: '',
    nickname: ''
  },
  forgot: {
    username: '',
    newPassword: ''
  }
})

const sliders = reactive({
  login: { verified: false },
  register: { verified: false },
  forgot: { verified: false }
})

const tabs = [
  { id: 'login', label: '登录' },
  { id: 'register', label: '注册' },
  { id: 'forgot', label: '找回密码' }
]

const tabTitles = {
  login: {
    title: '欢迎回来',
    subtitle: '登录以继续您的旅程 🐱'
  },
  register: {
    title: '创建账号',
    subtitle: '加入我们的大家庭 🎉'
  },
  forgot: {
    title: '找回密码',
    subtitle: '别担心，我来帮你 🔒'
  }
}

// Methods
function switchTab(tabName) {
  currentTab.value = tabName
  hideAlert()
}

function showAlert(message, isSuccess = true) {
  alert.show = true
  alert.message = message
  alert.type = isSuccess ? 'success' : 'error'
  
  setTimeout(() => {
    hideAlert()
  }, 4500)
}

function hideAlert() {
  alert.show = false
}

function translateError(raw) {
  const map = {
    '用户名或密码错误': '账号或密码不对哦，猫咪帮你看看？🐱',
    '用户名已存在': '这个用户名已经被注册啦，换一个试试',
    '用户不存在': '没找到这个账号，确认一下用户名是否正确',
    '验证码错误或已过期': '滑块验证未完成，拖动滑块试试',
    '用户名长度3-20位': '用户名需要3到20个字符（字母或数字）',
    '用户名只能包含字母和数字': '用户名只能用英文字母和数字哦',
    '密码至少6位': '密码太短了，至少要6个字符呢',
    '新密码至少6位': '新密码太短了，至少要6个字符哦',
    '昵称不能为空': '昵称不能留空，随便写一个吧',
    '无效凭证，重新登录': '登录过期了，请重新登录',
  }
  return map[raw] || (raw.length > 30 ? '操作失败了，请稍后再试' : raw)
}

async function handleLogin() {
  const { username, password } = forms.login
  
  if (!username || !password) {
    showAlert('用户名和密码都要填哦', false)
    return
  }
  
  if (!sliders.login.verified) {
    showAlert('请先完成滑块安全验证', false)
    return
  }

  loading.value = true
  
  try {
    // Import API dynamically to avoid circular dependency
    const api = (await import('../utils/api')).default
    const data = await api.login(username, password)
    
    showAlert('登录成功！猫咪很开心见到你 🐱✨')
    
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', username)
    
    router.push('/chat')
  } catch (error) {
    showAlert(translateError(error.detail) || '登录失败了，请稍后再试', false)
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  const { username, password, nickname } = forms.register
  
  if (!username || !password) {
    showAlert('用户名和密码都要填哦', false)
    return
  }
  
  if (!sliders.register.verified) {
    showAlert('请先完成滑块安全验证', false)
    return
  }

  loading.value = true
  
  try {
    const api = (await import('../utils/api')).default
    await api.register(username, password, nickname || undefined)
    
    showAlert('注册成功！欢迎加入我们 🎉🐱')
    
    // Reset form
    forms.register.username = ''
    forms.register.password = ''
    forms.register.nickname = ''
    
    switchTab('login')
  } catch (error) {
    showAlert(translateError(error.detail) || '注册失败了，请稍后再试', false)
  } finally {
    loading.value = false
  }
}

async function handleForgotPassword() {
  const { username, newPassword } = forms.forgot
  
  if (!username || !newPassword) {
    showAlert('账号和新密码都要填哦', false)
    return
  }
  
  if (!sliders.forgot.verified) {
    showAlert('请先完成滑块安全验证', false)
    return
  }

  loading.value = true
  
  try {
    const api = (await import('../utils/api')).default
    await api.forgotPassword(username, newPassword)
    
    showAlert('密码重置成功！猫咪帮你记住了 🔐')
    
    // Reset form
    forms.forgot.username = ''
    forms.forgot.newPassword = ''
    
    switchTab('login')
  } catch (error) {
    showAlert(translateError(error.detail) || '重置失败了，请稍后再试', false)
  } finally {
    loading.value = false
  }
}

function handleSliderSuccess(type) {
  if (catAvatarRef.value) {
    catAvatarRef.value.triggerHappy()
  }
}

function handlePasswordFocus() {
  if (catAvatarRef.value) {
    catAvatarRef.value.startShyMode()
  }
}

function handlePasswordBlur() {
  if (catAvatarRef.value) {
    catAvatarRef.value.stopShyMode()
  }
}

function handlePasswordMouseEnter() {
  if (catAvatarRef.value) {
    catAvatarRef.value.startShyMode()
  }
}

function handlePasswordMouseLeave(e) {
  // Only stop shy mode if the input is not focused
  if (e.target !== document.activeElement && catAvatarRef.value) {
    catAvatarRef.value.stopShyMode()
  }
}

function handleCatHappy() {
  // Cat happy animation triggered
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 50%, #dfe4ed 100%);
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  overflow-x: hidden;
  position: relative;
}

.bg-pattern {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  opacity: 0.03;
  background-image: 
    radial-gradient(circle at 25% 25%, #6366f1 2px, transparent 2px),
    radial-gradient(circle at 75% 75%, #8b5cf6 2px, transparent 2px);
  background-size: 60px 60px, 80px 80px;
  pointer-events: none; z-index: 0;
}

.floating-shapes {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  pointer-events: none; z-index: 0; overflow: hidden;
}

.shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  animation: floatShape ease-in-out infinite;
}
.shape-1 { 
  width: 300px; height: 300px; 
  background: rgba(99,102,241,0.08); 
  top: -100px; right: -50px; 
  animation-duration: 12s; 
}
.shape-2 { 
  width: 250px; height: 250px; 
  background: rgba(139,92,246,0.06); 
  bottom: -80px; left: -60px; 
  animation-duration: 15s; animation-delay: -3s; 
}
.shape-3 { 
  width: 200px; height: 200px; 
  background: rgba(236,72,153,0.05); 
  top: 40%; left: 30%; 
  animation-duration: 18s; animation-delay: -7s; 
}
@keyframes floatShape {
  0%, 100% { transform: translate(0, 0) scale(1) rotate(0deg); }
  33% { transform: translate(20px, -15px) scale(1.08) rotate(5deg); }
  66% { transform: translate(-15px, 10px) scale(0.95) rotate(-3deg); }
}

.auth-container {
  position: relative; z-index: 10;
  width: 420px; max-width: 90vw;
  perspective: 1200px;
}

.auth-card {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);
  border: 1px solid rgba(255,255,255,0.9);
  border-radius: 24px;
  padding: 48px 42px 40px;
  box-shadow:
    0 8px 32px rgba(99,102,241,0.12),
    0 2px 8px rgba(0,0,0,0.04),
    0 0 0 1px rgba(99,102,241,0.04) inset,
    0 1px 0 rgba(255,255,255,0.8) inset;
  animation: cardEntrance 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.auth-card:hover {
  box-shadow:
    0 12px 48px rgba(99,102,241,0.18),
    0 4px 16px rgba(0,0,0,0.06),
    0 0 0 1px rgba(99,102,241,0.06) inset,
    0 1px 0 rgba(255,255,255,0.9) inset;
  transform: translateY(-2px);
}
@keyframes cardEntrance {
  from { opacity: 0; transform: translateY(40px) rotateX(-10deg) scale(0.96); }
  to { opacity: 1; transform: translateY(0) rotateX(0) scale(1); }
}

.tab-switcher {
  display: flex; background: #f7fafc;
  border-radius: 12px; padding: 4px; margin-bottom: 28px;
  border: 1px solid #e2e8f0;
}
.tab-btn {
  flex: 1; padding: 11px; border: none; background: none;
  color: #718096; font-size: 14px; font-weight: 600;
  border-radius: 9px; cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}
.tab-btn.active {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  box-shadow: 0 4px 12px rgba(99,102,241,0.3);
  transform: translateY(-1px);
}
.tab-btn:not(.active):hover { 
  color: #4a5568; background: #edf2f7; 
}

.form-panel {
  animation: fadeSlideIn 0.4s ease both;
}
@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateX(12px); }
  to { opacity: 1; transform: translateX(0); }
}

.form-group { margin-bottom: 20px; position: relative; }
.form-label {
  display: block; font-size: 13px; font-weight: 600;
  color: #4a5568; margin-bottom: 8px;
  letter-spacing: 0.3px;
}
.form-input {
  width: 100%; padding: 14px 16px;
  background: #ffffff;
  border: 2px solid #e2e8f0;
  border-radius: 11px; color: #2d3748; font-size: 15px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); outline: none;
}
.form-input::placeholder { color: #a0aec0; }
.form-input:focus {
  border-color: #6366f1;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(99,102,241,0.08), 0 4px 12px rgba(99,102,241,0.1);
  transform: translateY(-1px);
}

.submit-btn {
  width: 100%; padding: 15px; margin-top: 8px;
  border: none; border-radius: 12px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white; font-size: 16px; font-weight: 700;
  cursor: pointer; letter-spacing: 1px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
  position: relative; overflow: hidden;
  box-shadow: 0 6px 24px rgba(99,102,241,0.35);
}
.submit-btn::before {
  content: ''; position: absolute; top: 0; left: -100%;
  width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.5s ease;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 10px 32px rgba(99,102,241,0.45);
}
.submit-btn:hover:not(:disabled)::before { left: 100%; }
.submit-btn:active:not(:disabled) { 
  transform: translateY(-1px); 
  box-shadow: 0 4px 16px rgba(99,102,241,0.35); 
}
.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.forgot-link {
  text-align: right; margin-top: 10px;
}
.forgot-link a {
  color: #6366f1; font-size: 13px;
  text-decoration: none; cursor: pointer; 
  font-weight: 500; transition: all 0.2s;
}
.forgot-link a:hover { 
  color: #4f46e5; 
  text-decoration: underline;
}

.back-login {
  text-align: center; margin-top: 20px;
}
.back-login a {
  color: #718096; font-size: 13px;
  text-decoration: none; cursor: pointer; 
  transition: all 0.2s; font-weight: 500;
}
.back-login a:hover { color: #4a5568; }

.alert-msg {
  padding: 14px 18px; border-radius: 11px; margin-bottom: 20px;
  font-size: 13px; font-weight: 500;
  animation: alertSlide 0.3s ease both;
  border: 1px solid;
}
@keyframes alertSlide {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
.alert-msg.success { 
  background: rgba(34,197,94,0.08); 
  color: #15803d; 
  border-color: rgba(34,197,94,0.2);
}
.alert-msg.error { 
  background: rgba(239,68,68,0.08); 
  color: #dc2626; 
  border-color: rgba(239,68,68,0.2);
}

.input-glow-line {
  position: absolute; bottom: 0; left: 50%;
  width: 0; height: 2px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899);
  border-radius: 1px; transition: width 0.4s ease, left 0.4s ease;
  pointer-events: none;
}
.form-group:focus-within .input-glow-line { width: 100%; left: 0; }
</style>
