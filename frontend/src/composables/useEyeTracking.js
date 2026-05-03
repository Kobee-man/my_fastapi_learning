import { ref, onMounted, onUnmounted } from 'vue'

export function useEyeTracking(catAvatarRef) {
  const leftPupilPos = ref({ x: 0, y: 0 })
  const rightPupilPos = ref({ x: 0, y: 0 })
  const isBlinking = ref(false)

  const EYE_CONFIG = {
    leftEye: { x: 72, y: 105 },
    rightEye: { x: 128, y: 105 },
    maxPupilOffset: 7,
    sensitivity: 25,
    smoothing: 0.15
  }

  let animationFrameId = null
  let targetLeftPos = { x: 0, y: 0 }
  let targetRightPos = { x: 0, y: 0 }
  let currentLeftPos = { x: 0, y: 0 }
  let currentRightPos = { x: 0, y: 0 }

  function calculatePupilPosition(mouseX, mouseY, eyeCenter) {
    const dx = mouseX - eyeCenter.x
    const dy = mouseY - eyeCenter.y
    const distance = Math.sqrt(dx * dx + dy * dy)
    
    if (distance === 0) return { x: 0, y: 0 }

    const dirX = dx / distance
    const dirY = dy / distance
    
    const rawOffset = Math.min(distance / EYE_CONFIG.sensitivity, 1)
    const easedOffset = easeOutCubic(rawOffset)
    const finalOffset = easedOffset * EYE_CONFIG.maxPupilOffset

    return {
      x: dirX * finalOffset,
      y: dirY * finalOffset
    }
  }

  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3)
  }

  function animateEyes() {
    currentLeftPos.x += (targetLeftPos.x - currentLeftPos.x) * EYE_CONFIG.smoothing
    currentLeftPos.y += (targetLeftPos.y - currentLeftPos.y) * EYE_CONFIG.smoothing
    currentRightPos.x += (targetRightPos.x - currentRightPos.x) * EYE_CONFIG.smoothing
    currentRightPos.y += (targetRightPos.y - currentRightPos.y) * EYE_CONFIG.smoothing

    leftPupilPos.value = { ...currentLeftPos }
    rightPupilPos.value = { ...currentRightPos }

    const leftDiff = Math.abs(targetLeftPos.x - currentLeftPos.x) + Math.abs(targetLeftPos.y - currentLeftPos.y)
    const rightDiff = Math.abs(targetRightPos.x - currentRightPos.x) + Math.abs(targetRightPos.y - currentRightPos.y)

    if (leftDiff > 0.01 || rightDiff > 0.01) {
      animationFrameId = requestAnimationFrame(animateEyes)
    } else {
      animationFrameId = null
    }
  }

  function updateEyePosition(clientX, clientY) {
    if (isBlinking.value || !catAvatarRef.value) return

    const rect = catAvatarRef.value.getBoundingClientRect()
    const svgWidth = 200
    const scale = rect.width / svgWidth

    const mouseXInSVG = (clientX - rect.left) / scale
    const mouseYInSVG = (clientY - rect.top) / scale

    targetLeftPos = calculatePupilPosition(mouseXInSVG, mouseYInSVG, EYE_CONFIG.leftEye)
    targetRightPos = calculatePupilPosition(mouseXInSVG, mouseYInSVG, EYE_CONFIG.rightEye)

    if (!animationFrameId) {
      animateEyes()
    }
  }

  function startShyMode() {
    isBlinking.value = true
  }

  function stopShyMode() {
    isBlinking.value = false
  }

  function handleMouseMove(e) {
    updateEyePosition(e.clientX, e.clientY)
  }

  function handleTouchMove(e) {
    if (e.touches.length > 0) {
      updateEyePosition(e.touches[0].clientX, e.touches[0].clientY)
    }
  }

  function handleMouseLeave() {
    targetLeftPos = { x: 0, y: 0 }
    targetRightPos = { x: 0, y: 0 }
    if (!animationFrameId) {
      animateEyes()
    }
  }

  onMounted(() => {
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('touchmove', handleTouchMove, { passive: true })
    document.addEventListener('mouseleave', handleMouseLeave)
  })

  onUnmounted(() => {
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('touchmove', handleTouchMove)
    document.removeEventListener('mouseleave', handleMouseLeave)
    
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId)
    }
  })

  return {
    leftPupilPos,
    rightPupilPos,
    isBlinking,
    startShyMode,
    stopShyMode
  }
}
