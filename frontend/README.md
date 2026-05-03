# FastAPI Vue Frontend

基于 Vue 3 + Vite 的现代化前端项目，完全重构自原有的 HTML 界面。

## ✨ 特性

- ⚡ **Vue 3 Composition API** - 使用最新的组合式API
- 🎨 **组件化设计** - 高度模块化，易于维护
- 🐱 **可爱的猫咪头像** - 带眼睛跟踪和闭眼动画
- 🔒 **滑块验证** - 用户友好的安全验证方式
- 💬 **实时聊天** - WebSocket 支持的公共/私聊功能
- 📱 **响应式设计** - 适配各种屏幕尺寸
- 🧪 **单元测试** - Vitest 测试框架

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/          # 可复用组件
│   │   ├── CatAvatar.vue    # 猫咪头像组件（带眼睛跟踪）
│   │   └── SliderVerify.vue # 滑块验证组件
│   ├── views/              # 页面视图
│   │   ├── LoginView.vue   # 登录/注册页面
│   │   └── ChatView.vue    # 聊天室页面
│   ├── composables/        # 组合式函数
│   │   └── useEyeTracking.js # 眼睛跟踪逻辑
│   ├── utils/              # 工具函数
│   │   └── api.js          # API 封装
│   ├── router/             # 路由配置
│   │   └── index.js
│   ├── App.vue             # 根组件
│   └── main.js             # 入口文件
├── tests/
│   └── unit/               # 单元测试
│       └── SliderVerify.spec.js
├── package.json
├── vite.config.js
└── vitest.config.js
```

## 🚀 快速开始

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

### 运行测试

```bash
npm run test:unit
```

## 🎯 核心功能

### 1. 登录系统 (LoginView)
- ✅ 登录表单
- ✅ 注册表单  
- ✅ 找回密码
- ✅ 滑块安全验证
- ✅ 猫咪头像交互
- ✅ 密码输入时猫咪闭眼

### 2. 聊天室 (ChatView)
- ✅ 公共聊天室
- ✅ 私聊功能
- ✅ 实时消息（WebSocket）
- ✅ 在线用户列表
- ✅ 个人中心
- ✅ 头像上传
- ✅ 昵称修改

### 3. 组件说明

#### CatAvatar 组件
```vue
<CatAvatar 
  ref="catAvatarRef"
  :title="欢迎回来"
  :subtitle="登录以继续您的旅程 🐱"
  @happy="handleCatHappy"
/>
```

**特性：**
- SVG 绘制的可爱猫咪
- 眼睛跟随鼠标移动
- 密码框聚焦时闭眼
- 验证成功时跳跃动画

#### SliderVerify 组件
```vue
<SliderVerify 
  v-model="isVerified"
  text="向右拖动滑块完成验证"
  @success="handleSuccess"
/>
```

**Props：**
- `modelValue` (Boolean) - 验证状态
- `text` (String) - 提示文本

**Events：**
- `update:modelValue` - 状态更新
- `success` - 验证成功

**Methods：**
- `reset()` - 重置状态

### 4. Composables

#### useEyeTracking
```javascript
import { useEyeTracking } from '../composables/useEyeTracking'

const { leftPupilPos, rightPupilPos, isBlinking, startShyMode, stopShyMode } = useEyeTracking(catAvatarRef)
```

**响应式数据：**
- `leftPupilPos` - 左眼瞳孔位置
- `rightPupilPos` - 右眼瞳孔位置
- `isBlinking` - 是否正在眨眼

**方法：**
- `startShyMode()` - 开始害羞模式（闭眼）
- `stopShyMode()` - 停止害羞模式

## 🔧 技术栈

- **框架**: Vue 3.4+
- **构建工具**: Vite 5.x
- **路由**: Vue Router 4.x
- **状态管理**: Pinia 2.x
- **测试**: Vitest + Vue Test Utils
- **样式**: Scoped CSS

## 📝 开发规范

### 组件命名
- PascalCase (如: CatAvatar.vue)

### 函数命名
- camelCase (如: handleLogin)

### 响应式变量
- 使用 `ref()` 或 `reactive()`
- 优先使用 Composition API

### 样式规范
- 使用 scoped CSS
- 保持与原HTML一致的像素级还原

## 🎨 设计原则

1. **像素级一致** - 与原HTML界面保持100%视觉一致性
2. **组件化** - 高度解耦，易于复用和测试
3. **响应式** - 充分利用Vue的响应式系统
4. **性能优化** - 合理使用computed、watch等
5. **可维护性** - 清晰的代码结构和注释

## 🧪 测试

运行所有测试：
```bash
npm run test:unit
```

运行测试并监听文件变化：
```bash
npm run test:watch
```

## 📦 部署

构建后的文件在 `dist/` 目录，可以部署到任何静态服务器。

### Nginx 配置示例
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /path/to/dist;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://127.0.0.1:8000;
    }
    
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT
