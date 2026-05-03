import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SliderVerify from '../src/components/SliderVerify.vue'

describe('SliderVerify Component', () => {
  it('renders correctly with default props', () => {
    const wrapper = mount(SliderVerify)
    expect(wrapper.find('.slider-verify').exists()).toBe(true)
    expect(wrapper.text()).toContain('向右拖动滑块完成验证')
  })

  it('shows custom text when provided', () => {
    const wrapper = mount(SliderVerify, {
      props: {
        text: '自定义文本'
      }
    })
    expect(wrapper.text()).toContain('自定义文本')
  })

  it('starts as unverified', () => {
    const wrapper = mount(SliderVerify)
    expect(wrapper.vm.isVerified).toBe(false)
  })

  it('emits success event when verification completes', async () => {
    const wrapper = mount(SliderVerify)
    
    // Simulate drag to completion
    const sliderEl = wrapper.find('.slider-verify').element
    const btnEl = wrapper.find('.slider-verify-btn').element
    
    // Get max offset
    const maxOffset = sliderEl.offsetWidth - btnEl.offsetWidth - 8
    const targetX = maxOffset * 0.95 // More than 90%
    
    // Simulate mousedown
    await wrapper.trigger('mousedown')
    
    // Update currentX to simulate drag
    wrapper.vm.currentX = targetX
    
    // Trigger mouseup
    document.dispatchEvent(new MouseEvent('mouseup'))
    
    await wrapper.vm.$nextTick()
    
    expect(wrapper.emitted()).toHaveProperty('success')
    expect(wrapper.vm.isVerified).toBe(true)
  })

  it('resets correctly when reset method is called', async () => {
    const wrapper = mount(SliderVerify)
    
    // First verify it
    wrapper.vm.verifySuccess()
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.isVerified).toBe(true)
    
    // Then reset
    wrapper.vm.reset()
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.isVerified).toBe(false)
    expect(wrapper.vm.currentX).toBe(0)
  })
})
