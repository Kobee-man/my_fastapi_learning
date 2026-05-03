<template>
  <div 
    class="slider-verify"
    :class="{ success: isVerified, shake: isShaking }"
    ref="sliderRef"
  >
    <div class="slider-verify-bg" :style="{ width: progressWidth }"></div>
    <span class="slider-verify-text" :class="{ 'text-success': isVerified }">
      {{ isVerified ? '验证成功 ✓' : text }}
    </span>
    <button 
      type="button" 
      class="slider-verify-btn"
      :class="{ success: isVerified }"
      :style="{ transform: `translateX(${currentX}px)` }"
      @mousedown="handleDragStart"
      @touchstart.prevent="handleDragStart"
    >
      <template v-if="!isVerified">☰</template>
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  text: {
    type: String,
    default: '向右拖动滑块完成验证'
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const sliderRef = ref(null)
const isVerified = ref(false)
const isDragging = ref(false)
const isShaking = ref(false)
const startX = ref(0)
const currentX = ref(0)
const maxOffset = ref(0)

const progressWidth = computed(() => {
  if (!sliderRef.value) return '0%'
  const btnWidth = 42
  const percentage = ((currentX.value + btnWidth / 2) / sliderRef.value.offsetWidth) * 100
  return `${Math.min(percentage, 100)}%`
})

function handleDragStart(e) {
  if (isVerified.value) return
  
  isDragging.value = true
  startX.value = e.type.includes('mouse') ? e.clientX : e.touches[0].clientX
  
  if (sliderRef.value) {
    const btn = sliderRef.value.querySelector('.slider-verify-btn')
    maxOffset.value = sliderRef.value.offsetWidth - btn.offsetWidth - 8
  }
  
  document.addEventListener('mousemove', handleDragMove)
  document.addEventListener('touchmove', handleDragMove, { passive: false })
  document.addEventListener('mouseup', handleDragEnd)
  document.addEventListener('touchend', handleDragEnd)
}

function handleDragMove(e) {
  if (!isDragging.value || isVerified.value) return
  
  e.preventDefault()
  const clientX = e.type.includes('mouse') ? e.clientX : e.touches[0].clientX
  const deltaX = clientX - startX.value
  currentX.value = Math.max(0, Math.min(deltaX, maxOffset.value))
}

function handleDragEnd() {
  if (!isDragging.value || isVerified.value) return
  
  isDragging.value = false
  
  document.removeEventListener('mousemove', handleDragMove)
  document.removeEventListener('touchmove', handleDragMove)
  document.removeEventListener('mouseup', handleDragEnd)
  document.removeEventListener('touchend', handleDragEnd)
  
  if (currentX.value >= maxOffset.value * 0.9) {
    verifySuccess()
  } else {
    resetSlider()
  }
}

function verifySuccess() {
  isVerified.value = true
  currentX.value = maxOffset.value
  emit('update:modelValue', true)
  emit('success')
}

function resetSlider() {
  currentX.value = 0
  isShaking.value = true
  
  setTimeout(() => {
    isShaking.value = false
  }, 400)
}

function reset() {
  isVerified.value = false
  currentX.value = 0
  emit('update:modelValue', false)
}

defineExpose({ reset })

onMounted(() => {
  if (sliderRef.value) {
    const btn = sliderRef.value.querySelector('.slider-verify-btn')
    maxOffset.value = sliderRef.value.offsetWidth - btn.offsetWidth - 8
  }
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleDragMove)
  document.removeEventListener('touchmove', handleDragMove)
  document.removeEventListener('mouseup', handleDragEnd)
  document.removeEventListener('touchend', handleDragEnd)
})
</script>

<style scoped>
.slider-verify {
  position: relative;
  width: 100%;
  height: 50px;
  background: #f7fafc;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  user-select: none;
  margin-top: 4px;
  transition: border-color 0.3s ease;
}

.slider-verify:focus-within {
  border-color: #6366f1;
}

.slider-verify-bg {
  position: absolute;
  top: 0; left: 0; height: 100%;
  width: 0;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  transition: width 0.1s ease-out;
  border-radius: 10px 0 0 10px;
}

.slider-verify.success .slider-verify-bg {
  background: linear-gradient(90deg, #22c55e, #4ade80);
  border-radius: 10px;
}

.slider-verify-text {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  color: #a0aec0;
  font-size: 13px;
  font-weight: 500;
  pointer-events: none;
  white-space: nowrap;
  transition: all 0.3s ease;
  z-index: 1;
}

.slider-verify-text.text-success {
  color: white;
  font-weight: 600;
}

.slider-verify-btn {
  position: absolute;
  top: 4px; left: 4px;
  width: 42px; height: 42px;
  background: linear-gradient(135deg, #fff, #f7fafc);
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #6366f1;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08), 0 0 0 1px rgba(255,255,255,0.8) inset;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 2;
  touch-action: none;
}

.slider-verify-btn:hover:not(.success) {
  transform: scale(1.08);
  box-shadow: 0 4px 16px rgba(99,102,241,0.25), 0 0 0 1px rgba(255,255,255,0.9) inset;
  border-color: #c7d2fe;
}

.slider-verify-btn:active:not(.success) {
  cursor: grabbing;
  transform: scale(0.98);
}

.slider-verify-btn.success {
  background: linear-gradient(135deg, #22c55e, #4ade80);
  border-color: #22c55e;
  color: white;
  cursor: default;
}

@keyframes sliderShake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-6px); }
  40% { transform: translateX(6px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}

.slider-verify.shake .slider-verify-btn {
  animation: sliderShake 0.4s ease-in-out;
}
</style>
