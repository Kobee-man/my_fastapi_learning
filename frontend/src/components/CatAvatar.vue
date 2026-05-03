<template>
  <div class="cat-avatar-container">
    <div 
      class="cat-avatar-wrapper" 
      :class="{ 'happy': isHappy }"
      ref="avatarWrapperRef"
    >
      <svg
        class="cat-svg cat-avatar"
        :class="{ blinking: isBlinking }"
        ref="catAvatarRef"
        viewBox="0 0 200 200"
        xmlns="http://www.w3.org/2000/svg"
      >
        <g class="cat-body">
          <!-- 脸部 -->
          <ellipse cx="100" cy="110" rx="70" ry="65" fill="#FBBF24"/>
          
          <!-- 内部脸部 -->
          <ellipse cx="100" cy="115" rx="58" ry="52" fill="#FEF3C7"/>
          
          <!-- 左耳 -->
          <path d="M 35 75 L 25 25 Q 35 20 50 55 Z" fill="#FBBF24"/>
          <path d="M 38 70 L 32 35 Q 38 33 47 56 Z" fill="#FDE68A"/>
          
          <!-- 右耳 -->
          <path d="M 165 75 L 175 25 Q 165 20 150 55 Z" fill="#FBBF24"/>
          <path d="M 162 70 L 168 35 Q 162 33 153 56 Z" fill="#FDE68A"/>
          
          <!-- 左眼睛 -->
          <g class="eye-container" transform="translate(72, 105)">
            <ellipse class="eyeball-white" cx="0" cy="0" rx="18" ry="20" fill="white"/>
            
            <g class="pupil-group" :style="{ transform: `translate(${leftPupilPos.x}px, ${leftPupilPos.y}px)` }">
              <ellipse class="pupil" cx="2" cy="2" rx="10" ry="11" fill="#1a202c"/>
              <ellipse cx="2" cy="2" rx="6" ry="7" fill="#2d3748"/>
              <circle class="highlight-main" cx="6" cy="-2" r="4.5" fill="white"/>
              <circle class="highlight-sub" cx="-1" cy="4" r="2" fill="white" opacity="0.7"/>
            </g>
            
            <ellipse class="eyelid eyelid-top" cx="0" cy="-10" rx="19" ry="12" fill="#FBBF24"/>
            <ellipse class="eyelid eyelid-bottom" cx="0" cy="10" rx="19" ry="12" fill="#FBBF24"/>
            
            <path class="eye-outline" d="M -17 -6 Q 0 -22 17 -6" stroke="#D97706" stroke-width="1.5" fill="none" opacity="0.3"/>
          </g>
          
          <!-- 右眼睛 -->
          <g class="eye-container" transform="translate(128, 105)">
            <ellipse class="eyeball-white" cx="0" cy="0" rx="18" ry="20" fill="white"/>
            
            <g class="pupil-group" :style="{ transform: `translate(${rightPupilPos.x}px, ${rightPupilPos.y}px)` }">
              <ellipse class="pupil" cx="-2" cy="2" rx="10" ry="11" fill="#1a202c"/>
              <ellipse cx="-2" cy="2" rx="6" ry="7" fill="#2d3748"/>
              <circle class="highlight-main" cx="2" cy="-2" r="4.5" fill="white"/>
              <circle class="highlight-sub" cx="-5" cy="4" r="2" fill="white" opacity="0.7"/>
            </g>
            
            <ellipse class="eyelid eyelid-top" cx="0" cy="-10" rx="19" ry="12" fill="#FBBF24"/>
            <ellipse class="eyelid eyelid-bottom" cx="0" cy="10" rx="19" ry="12" fill="#FBBF24"/>
            
            <path class="eye-outline" d="M -17 -6 Q 0 -22 17 -6" stroke="#D97706" stroke-width="1.5" fill="none" opacity="0.3"/>
          </g>
          
          <!-- 鼻子 -->
          <ellipse cx="100" cy="130" rx="8" ry="6" fill="#FB7185"/>
          
          <!-- 嘴巴 -->
          <path d="M 88 138 Q 100 148 112 138" stroke="#92400E" stroke-width="2.5" fill="none" stroke-linecap="round"/>
          <path d="M 100 138 L 100 144" stroke="#92400E" stroke-width="2" stroke-linecap="round"/>
          
          <!-- 胡须 -->
          <g stroke="#92400E" stroke-width="1.5" stroke-linecap="round" opacity="0.6">
            <line x1="45" y1="125" x2="20" y2="120"/>
            <line x1="43" y1="133" x2="18" y2="134"/>
            <line x1="45" y1="141" x2="22" y2="148"/>
            
            <line x1="155" y1="125" x2="180" y2="120"/>
            <line x1="157" y1="133" x2="182" y2="134"/>
            <line x1="155" y1="141" x2="178" y2="148"/>
          </g>
          
          <!-- 腮红 -->
          <ellipse cx="55" cy="125" rx="12" ry="8" fill="#FCA5A5" opacity="0.4"/>
          <ellipse cx="145" cy="125" rx="12" ry="8" fill="#FCA5A5" opacity="0.4"/>
        </g>
        
        <!-- 尾巴 -->
        <g class="cat-tail">
          <path d="M 160 160 Q 185 155 190 140 Q 195 125 188 115" 
                stroke="#FBBF24" stroke-width="12" fill="none" stroke-linecap="round"/>
          <path d="M 188 115 Q 192 108 188 102" 
                stroke="#FDE68A" stroke-width="8" fill="none" stroke-linecap="round"/>
        </g>
      </svg>
    </div>
    <h1 class="logo-title">{{ title }}</h1>
    <p class="logo-subtitle">{{ subtitle }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useEyeTracking } from '../composables/useEyeTracking'

const props = defineProps({
  title: {
    type: String,
    default: '欢迎回来'
  },
  subtitle: {
    type: String,
    default: '登录以继续您的旅程 🐱'
  }
})

const emit = defineEmits(['happy'])

const catAvatarRef = ref(null)
const avatarWrapperRef = ref(null)
const isHappy = ref(false)

const { leftPupilPos, rightPupilPos, isBlinking, startShyMode, stopShyMode } = useEyeTracking(catAvatarRef)

function triggerHappy() {
  isHappy.value = true
  emit('happy')
  
  setTimeout(() => {
    isHappy.value = false
  }, 600)
}

defineExpose({ isBlinking, startShyMode, stopShyMode, triggerHappy })
</script>

<style scoped>
.cat-avatar-container {
  text-align: center;
  margin-bottom: 32px;
  position: relative;
}

.cat-avatar-wrapper {
  position: relative;
  display: inline-block;
  cursor: pointer;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.cat-avatar-wrapper:hover {
  transform: scale(1.05) rotate(-3deg);
}

.cat-avatar-wrapper.happy {
  animation: catHappyJump 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes catHappyJump {
  0%, 100% { transform: scale(1) rotate(0deg); }
  25% { transform: scale(1.15) rotate(-5deg) translateY(-10px); }
  50% { transform: scale(1.1) rotate(5deg) translateY(-5px); }
  75% { transform: scale(1.15) rotate(-3deg) translateY(-8px); }
}

.cat-svg {
  width: 120px;
  height: 120px;
  filter: drop-shadow(0 8px 20px rgba(99,102,241,0.25));
  transition: filter 0.3s ease;
}

.cat-avatar-wrapper:hover .cat-svg {
  filter: drop-shadow(0 12px 28px rgba(99,102,241,0.35));
}

.eye-container {
  overflow: visible;
}

.eyeball-white {
  transition: all 0.3s ease;
}

.pupil-group {
  transition: transform 0.08s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  will-change: transform;
}

.pupil {
  transition: fill 0.2s ease;
}

.highlight-main, .highlight-sub {
  transition: opacity 0.2s ease;
}

.eyelid {
  opacity: 0;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
}

.eyelid-top {
  transform: translateY(-8px);
}

.eyelid-bottom {
  transform: translateY(8px);
}

.cat-svg.blinking .eyelid-top {
  opacity: 1;
  transform: translateY(6px);
}

.cat-svg.blinking .eyelid-bottom {
  opacity: 1;
  transform: translateY(-6px);
}

.cat-svg.blinking .pupil-group {
  opacity: 0.15;
  transform: scale(0.7);
}

.cat-svg.blinking .highlight-main,
.cat-svg.blinking .highlight-sub {
  opacity: 0;
}

.logo-title {
  font-size: 26px;
  font-weight: 700;
  color: #1a202c;
  letter-spacing: 0.5px;
  margin-top: 14px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-subtitle {
  font-size: 13px;
  color: #718096;
  margin-top: 6px;
  font-weight: 400;
}

/* 呼吸动画 */
@keyframes catBreathe {
  0%, 100% { transform: scaleY(1); }
  50% { transform: scaleY(1.02); }
}

.cat-body {
  transform-origin: bottom center;
  animation: catBreathe 3s ease-in-out infinite;
}

/* 尾巴摇摆 */
@keyframes tailWag {
  0%, 100% { transform: rotate(-10deg); }
  50% { transform: rotate(10deg); }
}

.cat-tail {
  transform-origin: left center;
  animation: tailWag 2s ease-in-out infinite;
}
</style>
