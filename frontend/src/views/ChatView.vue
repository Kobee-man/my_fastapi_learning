<template>
  <div class="chat-page">
    <div class="glow-orb orb-1"></div>
    <div class="glow-orb orb-2"></div>

    <div class="chat-wrapper">
      <!-- Header -->
      <div class="chat-header-bar">
        <h3>💬 聊天室</h3>
        <div class="header-btns">
          <button 
            class="turtle-soup-btn" 
            @click="showTurtleSoup = true"
            title="🐢 海龟汤游戏 - 推理谜题游戏"
          >
            🐢 海龟汤
          </button>
          <button @click="toggleProfilePanel">个人中心</button>
          <button class="logout-btn" @click="handleLogout">🚪 退出登录</button>
        </div>
      </div>

      <!-- Turtle Soup Game Modal -->
      <TurtleSoupGame 
        v-if="showTurtleSoup" 
        @close="showTurtleSoup = false"
        :username="currentUsername"
        :token="token"
        :online-users="friends"
      />

      <!-- Chat Type Tabs -->
      <div class="chat-type-tabs">
        <button 
          :class="{ active: chatMode === 'public' }"
          @click="switchChatMode('public')"
        >
          公共聊天室
        </button>
        <button 
          :class="{ active: chatMode === 'private' }"
          @click="switchChatMode('private')"
        >
          私聊
        </button>
      </div>

      <!-- Profile Panel -->
      <div v-if="showProfile" class="profile-panel">
        <h4>👤 个人中心</h4>
        
        <button 
          @click="fetchProfile" 
          style="margin-bottom:14px;padding:8px 16px;border:none;border-radius:8px;
                 background:rgba(99,102,241,0.18);color:#a5b4fc;cursor:pointer;font-size:13px;"
        >
          刷新信息
        </button>

        <img :src="profile.avatar || 'https://via.placeholder.com/70'" alt="" class="avatar-display">
        
        <div class="profile-info-grid">
          <div><strong>UID</strong>{{ profile.uid }}</div>
          <div><strong>用户名</strong>{{ profile.username }}</div>
          <div><strong>昵称</strong>{{ profile.nickname }}</div>
        </div>

        <div class="pf-form-group">
          <label>修改昵称</label>
          <input type="text" v-model="newNickname" placeholder="新昵称">
          <button @click="handleUpdateNickname">保存</button>
        </div>

        <div class="pf-form-group">
          <label>上传头像</label>
          <input type="file" @change="handleAvatarFileChange" accept="image/*">
          <button @click="handleUploadAvatar">上传</button>
        </div>
      </div>

      <!-- Public Chat Area -->
      <div v-show="chatMode === 'public'" id="publicChatArea">
        <div class="section-row">
          <span class="section-title">公共聊天室</span>
          <span class="online-count-badge">在线: {{ onlineCount }}</span>
        </div>
        
        <div class="chat-box" ref="pubMsgBoxRef">
          <div 
            v-for="(msg, index) in publicMessages" 
            :key="index"
            class="msg-item"
            :class="getMsgClass(msg)"
          >
            <template v-if="msg.type === 'system'">
              <span>{{ msg.content }}</span>
            </template>
            <template v-else>
              <div class="msg-bubble">{{ msg.content }}</div>
              <div class="msg-meta">{{ msg.nickname || msg.username }} · {{ formatTime(msg.timestamp) }}</div>
            </template>
          </div>
        </div>

        <div class="chat-input-row">
          <input 
            type="text" 
            v-model="pubInput" 
            placeholder="输入消息..." 
            @keypress.enter="sendPublicMessage"
          >
          <button @click="sendPublicMessage">发送</button>
        </div>
      </div>

      <!-- Private Chat Area -->
      <div v-show="chatMode === 'private'" id="privateChatArea">
        <div class="friend-panel">
          <h5>选择聊天对象</h5>
          <div class="friend-list-scroll">
            <div 
              v-for="user in friends" 
              :key="user.uid"
              class="friend-item"
              @click="startPrivateChat(user.uid, user.nickname || user.username)"
            >
              <img class="friend-avatar-sm" :src="user.avatar_url || 'https://via.placeholder.com/32'" alt="">
              <span class="friend-name-text">{{ user.nickname || user.username }}</span>
              <span class="dot-status dot-on"></span>
            </div>
          </div>
        </div>

        <div class="section-row">
          <span class="status-label">{{ privateTargetName || '未选择' }}</span>
          <span class="online-count-badge">{{ privateTargetStatus }}</span>
        </div>

        <div class="chat-box" ref="priMsgBoxRef">
          <div 
            v-for="(msg, index) in privateMessages" 
            :key="index"
            class="msg-item"
            :class="getPrivateMsgClass(msg)"
          >
            <template v-if="msg.type === 'system'">
              <span>{{ msg.content }}</span>
            </template>
            <template v-else>
              <div class="msg-bubble">{{ msg.content }}</div>
              <div class="msg-meta">{{ msg.from_nickname || msg.from_username }} · {{ formatTime(msg.timestamp) }}</div>
            </template>
          </div>
        </div>

        <div class="chat-input-row">
          <input 
            type="text" 
            v-model="priInput" 
            placeholder="输入私信..." 
            @keypress.enter="sendPrivateMessage"
          >
          <button @click="sendPrivateMessage">发送</button>
        </div>
      </div>
    </div>

    <!-- Toast Notifications -->
    <div 
      v-if="toast.show" 
      class="alert-toast" 
      :class="toast.type"
    >
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api from '../utils/api'
import TurtleSoupGame from '../components/TurtleSoupGame.vue'

const router = useRouter()

// Refs
const pubMsgBoxRef = ref(null)
const priMsgBoxRef = ref(null)

// State
const token = localStorage.getItem('token') || ''
const currentUsername = localStorage.getItem('username') || ''
const currentUserUid = ref(null)

const chatMode = ref('public')
const showProfile = ref(false)
const showTurtleSoup = ref(false)
const onlineCount = ref(0)
const onlineTimer = ref(null)

// WebSocket instances
let publicWs = null
let privateWs = null

// Form data
const pubInput = ref('')
const priInput = ref('')
const newNickname = ref('')
const avatarFile = ref(null)

// Chat data
const publicMessages = ref([])
const privateMessages = ref([])
const friends = ref([])
const privateTargetUid = ref(null)
const privateTargetName = ref('')
const privateTargetStatus = ref('离线')

// Profile data
const profile = reactive({
  uid: '',
  username: '',
  nickname: '',
  avatar: ''
})

// Toast notification
const toast = reactive({
  show: false,
  message: '',
  type: 'success' // 'success' or 'error'
})

function showToast(message, isSuccess = true) {
  toast.show = true
  toast.message = message
  toast.type = isSuccess ? 'success' : 'error'
  
  setTimeout(() => {
    toast.show = false
  }, 3200)
}

function escHtml(s) {
  const div = document.createElement('div')
  div.textContent = s
  return div.innerHTML
}

function formatTime(timestamp) {
  return new Date(timestamp).toLocaleTimeString()
}

function getMsgClass(msg) {
  if (msg.type === 'system') return 'sys'
  return msg.username === currentUsername ? 'mine' : 'other'
}

function getPrivateMsgClass(msg) {
  if (msg.type === 'system') return 'sys'
  return msg.from_uid === currentUserUid.value ? 'mine' : 'other'
}

function scrollToBottom(ref) {
  nextTick(() => {
    if (ref.value) {
      ref.value.scrollTop = ref.value.scrollHeight
    }
  })
}

// Authentication
async function handleLogout() {
  if (publicWs) { publicWs.close(); publicWs = null; }
  if (privateWs) { privateWs.close(); privateWs = null; }
  if (onlineTimer.value) { clearInterval(onlineTimer.value); onlineTimer.value = null; }
  
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  router.push('/')
}

// Profile management
async function fetchProfile() {
  try {
    const data = await api.getProfile()
    const info = data.data
    
    currentUserUid.value = info.uid
    profile.uid = info.uid
    profile.username = info.username
    profile.nickname = info.nickname
    profile.avatar = info.avatar_access_url || ''
    
    return info
  } catch (error) {
    showToast('登录过期了，请重新登录', false)
    handleLogout()
    return null
  }
}

async function handleUpdateNickname() {
  const value = newNickname.value.trim()
  if (!value) return
  
  try {
    await api.updateNickname(value)
    showToast('昵称修改成功')
    newNickname.value = ''
    fetchProfile()
  } catch (error) {
    showToast(error.detail || '修改失败了，稍后再试', false)
  }
}

function handleAvatarFileChange(e) {
  avatarFile.value = e.target.files[0]
}

async function handleUploadAvatar() {
  if (!avatarFile.value) return
  
  try {
    await api.uploadAvatar(avatarFile.value)
    showToast('头像上传成功')
    fetchProfile()
  } catch (error) {
    showToast(error.detail || '上传失败了，稍后再试', false)
  }
}

function toggleProfilePanel() {
  showProfile.value = !showProfile.value
  if (showProfile.value) {
    fetchProfile()
  }
}

// Chat mode switching
function switchChatMode(mode) {
  chatMode.value = mode
  
  if (mode === 'public') {
    if (!publicWs) initPublicWebSocket()
  } else {
    loadFriends()
  }
}

// Public chat functions
function initPublicWebSocket() {
  if (!token) {
    showToast('请先登录哦', false)
    handleLogout()
    return
  }
  
  if (publicWs) { publicWs.close(); publicWs = null }
  if (onlineTimer.value) { clearInterval(onlineTimer.value); onlineTimer.value = null }

  const wsUrl = `ws://${window.location.hostname}:8000/ws/chat/${token}`
  publicWs = new WebSocket(wsUrl)

  publicWs.onopen = () => {
    showToast('聊天室连接成功')
    updateOnlineCount()
    onlineTimer.value = setInterval(updateOnlineCount, 5000)
  }

  publicWs.onmessage = (e) => {
    const message = JSON.parse(e.data)
    
    if (message.type === 'history' && message.messages) {
      publicMessages.value = [...message.messages]
    } else {
      publicMessages.value.push(message)
    }
    
    scrollToBottom(pubMsgBoxRef)
  }

  publicWs.onclose = (e) => {
    if (onlineTimer.value) { clearInterval(onlineTimer.value); onlineTimer.value = null }
    
    if (e.code !== 1000) {
      showToast('聊天室断开了，正在自动重连...', false)
      setTimeout(initPublicWebSocket, 3000)
    }
  }

  publicWs.onerror = () => {
    showToast('聊天室连不上，请检查网络', false)
  }
}

function sendPublicMessage() {
  const content = pubInput.value.trim()
  
  if (!content) {
    showToast('还没写内容呢', false)
    return
  }
  
  if (!publicWs || publicWs.readyState !== WebSocket.OPEN) {
    showToast('聊天室还没连上哦', false)
    return
  }
  
  publicWs.send(JSON.stringify({ content }))
  pubInput.value = ''
}

async function updateOnlineCount() {
  try {
    const data = await api.getOnlineUsers()
    onlineCount.value = (data.data || []).length
  } catch (error) {
    console.error('Failed to update online count:', error)
  }
}

// Private chat functions
async function loadFriends() {
  try {
    const data = await api.getOnlineUsers()
    friends.value = (data.data || []).filter(user => user.uid !== currentUserUid.value)
  } catch (error) {
    console.error('Failed to load friends:', error)
  }
}

function startPrivateChat(uid, name) {
  privateTargetUid.value = uid
  privateTargetName.value = `与 ${name} 私聊`
  privateTargetStatus.value = '在线'
  privateMessages.value = []
  
  initPrivateWebSocket(uid)
}

function initPrivateWebSocket(targetUid) {
  if (!token) return
  
  if (privateWs) { privateWs.close(); privateWs = null }
  
  const wsUrl = `ws://${window.location.hostname}:8000/ws/private-chat/${token}/${targetUid}`
  privateWs = new WebSocket(wsUrl)

  privateWs.onopen = () => {
    showToast('私聊连接成功')
  }

  privateWs.onmessage = (e) => {
    const message = JSON.parse(e.data)
    privateMessages.value.push(message)
    scrollToBottom(priMsgBoxRef)
  }

  privateWs.onclose = (e) => {
    if (e.code !== 1000) {
      showToast('私聊断开了，正在自动重连...', false)
      setTimeout(() => initPrivateWebSocket(targetUid), 3000)
    }
  }

  privateWs.onerror = () => {
    showToast('私聊连不上，请检查网络', false)
  }
}

function sendPrivateMessage() {
  if (!privateTargetUid.value) {
    showToast('请先在左边选一个聊天对象哦', false)
    return
  }
  
  const content = priInput.value.trim()
  if (!content) return
  
  if (!privateWs || privateWs.readyState !== WebSocket.OPEN) {
    showToast('私聊还没连上呢', false)
    return
  }
  
  privateWs.send(JSON.stringify({ content, to_uid: privateTargetUid.value }))
  priInput.value = ''
}

// Lifecycle hooks
onMounted(async () => {
  if (!token) {
    router.push('/')
    return
  }
  
  const info = await fetchProfile()
  if (!info) return
  
  initPublicWebSocket()
})

onUnmounted(() => {
  // Clean up
  if (publicWs) { publicWs.close(); publicWs = null }
  if (privateWs) { privateWs.close(); privateWs = null }
  if (onlineTimer.value) { clearInterval(onlineTimer.value); onlineTimer.value = null }
})
</script>

<style scoped>
.chat-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0c0e1a 0%, #1a1a3e 30%, #0d1b2a 60%, #1b263b 100%);
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  position: relative;
}

.glow-orb {
  position: fixed; border-radius: 50%; filter: blur(80px);
  animation: orbFloat ease-in-out infinite;
  pointer-events: none; z-index: 0;
}
.orb-1 { width: 400px; height: 400px; background: rgba(99,102,241,0.12); top: -100px; left: -100px; animation-duration: 8s; }
.orb-2 { width: 350px; height: 350px; background: rgba(236,72,153,0.10); bottom: -80px; right: -80px; animation-duration: 10s; animation-delay: -3s; }

@keyframes orbFloat {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(30px, -20px) scale(1.05); }
  50% { transform: translate(-20px, 30px) scale(0.95); }
  75% { transform: translate(20px, 20px) scale(1.02); }
}

.chat-wrapper {
  position: relative; z-index: 10;
  width: 760px; max-width: 95vw; margin: 24px auto;
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 22px;
  padding: 26px;
  box-shadow: 0 24px 48px rgba(0,0,0,0.35);
  animation: chatEntrance 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes chatEntrance {
  from { opacity: 0; transform: translateY(30px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.chat-header-bar {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 18px; padding-bottom: 16px;
  border-bottom: 1px solid rgba(255,255,255,0.07);
}
.chat-header-bar h3 { color: #fff; font-size: 19px; font-weight: 700; }
.header-btns button {
  padding: 8px 16px; border: 1px solid rgba(255,255,255,0.14);
  background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.7);
  border-radius: 9px; cursor: pointer; font-size: 13px; margin-left: 8px;
  transition: all 0.2s;
}
.header-btns button:hover { background: rgba(255,255,255,0.1); color: #fff; }
.header-btns .logout-btn:hover {
  background: rgba(239,68,68,0.15); color: #f87171;
  border-color: rgba(239,68,68,0.3);
}

.turtle-soup-btn {
  background: linear-gradient(135deg, rgba(34,197,94,0.2), rgba(16,185,129,0.2)) !important;
  border-color: rgba(34,197,94,0.4) !important;
  color: #4ade80 !important;
  font-weight: 600;
  animation: turtlePulse 2s ease-in-out infinite;
}
.turtle-soup-btn:hover {
  background: linear-gradient(135deg, rgba(34,197,94,0.3), rgba(16,185,129,0.3)) !important;
  box-shadow: 0 4px 20px rgba(34,197,94,0.3) !important;
  transform: translateY(-1px);
}
@keyframes turtlePulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.chat-type-tabs { display: flex; gap: 8px; margin-bottom: 16px; }
.chat-type-tabs button {
  padding: 9px 20px; border: none; border-radius: 10px;
  cursor: pointer; font-size: 13px; font-weight: 600; transition: all 0.2s;
}
.chat-type-tabs button.active {
  background: linear-gradient(135deg,#6366f1,#8b5cf6);
  color: #fff;
  box-shadow: 0 4px 14px rgba(99,102,241,0.3);
}
.chat-type-tabs button:not(.active) {
  background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.5);
}
.chat-type-tabs button:not(.active):hover {
  background: rgba(255,255,255,0.09); color: rgba(255,255,255,0.7);
}

.profile-panel {
  margin-bottom: 18px; padding: 22px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  animation: panelSlide 0.3s ease both;
}
@keyframes panelSlide {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
.profile-panel h4 { color: #fff; margin-bottom: 14px; font-size: 16px; font-weight: 700; }
.profile-info-grid { display: grid; gap: 8px; margin-bottom: 18px; }
.profile-info-grid div {
  padding: 9px 13px; background: rgba(255,255,255,0.03);
  border-radius: 9px; font-size: 13px; color: rgba(255,255,255,0.7);
}
.profile-info-grid strong { color: rgba(255,255,255,0.38); margin-right: 7px; }
.avatar-display {
  width: 72px; height: 72px; border-radius: 50%; object-fit: cover;
  border: 2px solid rgba(99,102,241,0.4); margin-bottom: 14px;
}
.pf-form-group { margin-bottom: 14px; }
.pf-form-group label {
  display: block; font-size: 12px; color: rgba(255,255,255,0.42); margin-bottom: 6px;
}
.pf-form-group input[type="text"], .pf-form-group input[type="file"] {
  width: 100%; padding: 10px 14px; border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05); color: #fff; font-size: 14px;
}
.pf-form-group input::placeholder { color: rgba(255,255,255,0.2); }
.pf-form-group button {
  padding: 10px 22px; border: none; border-radius: 10px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff; font-weight: 600; cursor: pointer; font-size: 13px;
  margin-top: 5px; transition: all 0.2s;
}
.pf-form-group button:hover { box-shadow: 0 4px 14px rgba(99,102,241,0.3); }

.friend-panel { margin-bottom: 14px; }
.friend-panel h5 { color: rgba(255,255,255,0.55); font-size: 13px; margin-bottom: 10px; font-weight: 600; }
.friend-list-scroll {
  max-height: 150px; overflow-y: auto;
  border: 1px solid rgba(255,255,255,0.06); border-radius: 11px;
  background: rgba(0,0,0,0.12);
}
.friend-list-scroll::-webkit-scrollbar { width: 4px; }
.friend-list-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 3px; }
.friend-item {
  padding: 11px 14px; display: flex; align-items: center;
  cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.03);
  transition: background 0.2s;
}
.friend-item:hover { background: rgba(255,255,255,0.05); }
.friend-item:last-child { border-bottom: none; }
.friend-avatar-sm {
  width: 34px; height: 34px; border-radius: 50%;
  object-fit: cover; margin-right: 11px;
}
.friend-name-text { flex: 1; font-size: 13px; color: rgba(255,255,255,0.82); }
.dot-status { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.dot-on { background: #22c55e; box-shadow: 0 0 7px rgba(34,197,94,0.5); }
.dot-off { background: rgba(255,255,255,0.18); }

.online-count-badge {
  font-size: 12px; color: rgba(255,255,255,0.36);
}
.status-label {
  font-size: 13px; color: rgba(255,255,255,0.72);
}

.chat-box {
  height: 420px; overflow-y: auto;
  background: rgba(0,0,0,0.18);
  border-radius: 14px; padding: 16px; margin-bottom: 12px;
  border: 1px solid rgba(255,255,255,0.05);
  scroll-behavior: smooth;
}
.chat-box::-webkit-scrollbar { width: 5px; }
.chat-box::-webkit-scrollbar-track { background: transparent; }
.chat-box::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }

.msg-item { margin-bottom: 14px; display: flex; flex-direction: column; }
.msg-item.sys { align-items: center; }
.msg-item.sys span {
  font-size: 12px; color: rgba(255,255,255,0.32);
  background: rgba(255,255,255,0.04);
  padding: 4px 14px; border-radius: 10px;
}
.msg-bubble {
  max-width: 70%; padding: 11px 17px; border-radius: 17px;
  font-size: 14px; line-height: 1.55; word-break: break-all;
}
.msg-item.mine { align-items: flex-start; }
.msg-item.mine .msg-bubble {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff; border-bottom-left-radius: 5px;
}
.msg-item.other { align-items: flex-end; }
.msg-item.other .msg-bubble {
  background: rgba(255,255,255,0.07); color: rgba(255,255,255,0.88);
  border: 1px solid rgba(255,255,255,0.06); border-bottom-right-radius: 5px;
}
.msg-meta {
  font-size: 11px; color: rgba(255,255,255,0.28);
  margin-top: 4px; padding: 0 4px;
}
.msg-item.mine .msg-meta { align-self: flex-start; }
.msg-item.other .msg-meta { align-self: flex-end; }

.chat-input-row { display: flex; gap: 10px; align-items: center; }
.chat-input-row input {
  flex: 1; padding: 13px 18px; border-radius: 13px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05); color: #fff;
  font-size: 14px; outline: none; transition: all 0.2s;
}
.chat-input-row input:focus {
  border-color: rgba(99,102,241,0.5);
  box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
}
.chat-input-row input::placeholder { color: rgba(255,255,255,0.22); }
.chat-input-row button {
  padding: 13px 24px; border: none; border-radius: 13px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff; font-weight: 600; cursor: pointer; font-size: 14px;
  transition: all 0.2s; white-space: nowrap;
}
.chat-input-row button:hover {
  transform: translateY(-1px);
  box-shadow: 0 5px 18px rgba(99,102,241,0.35);
}

.alert-toast {
  position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
  padding: 12px 24px; border-radius: 12px; z-index: 9999;
  font-size: 13px; font-weight: 500; animation: toastIn 0.3s ease both;
  backdrop-filter: blur(12px);
}
.alert-toast.success {
  background: rgba(34,197,94,0.15); color: #4ade80;
  border: 1px solid rgba(34,197,94,0.25);
}
.alert-toast.error {
  background: rgba(239,68,68,0.15); color: #f87171;
  border: 1px solid rgba(239,68,68,0.25);
}
@keyframes toastIn {
  from { opacity: 0; transform: translateX(-50%) translateY(-15px); }
  to { opacity: 1; transform: translateX(-50%) translateY(0); }
}

.section-row {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;
}
.section-title { font-size: 13px; color: rgba(255,255,255,0.38); font-weight: 500; }
</style>
