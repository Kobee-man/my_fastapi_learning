# 🐢 海龟汤游戏系统 - Ollama 本地版 完整指南

## 📋 系统概述

这是一个完全本地运行的海龟汤（情境猜谜）游戏系统，使用 Ollama 作为大语言模型后端，无需任何云服务或 API Key。

### ✨ 核心特性

- **完全离线运行**：所有计算在本地完成，保护隐私
- **多模型支持**：兼容 Llama 3, Mistral, Qwen 等主流开源模型
- **智能AI主持人**：结构化提示确保一致的判断逻辑
- **完整游戏管理**：状态跟踪、进度记录、统计功能
- **CLI交互界面**：简单易用的命令行操作

---

## 🔧 环境要求与安装

### 1. 安装 Ollama

#### Windows 系统：

```powershell
# 方法1：使用 winget 安装（推荐）
winget install Ollama.Ollama

# 方法2：手动下载安装
# 访问 https://ollama.ai/download 下载 Windows 版本
# 运行安装程序，按向导完成安装
```

#### macOS 系统：

```bash
# 使用 Homebrew 安装
brew install ollama

# 或手动下载 DMG 文件
```

#### Linux 系统：

```bash
# 一行命令安装
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. 启动 Ollama 服务

```powershell
# Windows PowerShell
ollama serve

# 或者在系统托盘找到 Ollama 图标，右键启动
```

```bash
# macOS / Linux
ollama serve
```

**验证服务状态**：
```powershell
# 检查Ollama是否正常运行
curl http://localhost:11434/api/tags

# 或在浏览器访问
# http://localhost:11434
```

### 3. 安装 Python 依赖

```powershell
# 进入项目目录
cd d:\my_fastapi

# 安装requests库（如果尚未安装）
pip install requests
```

**Python版本要求**：>= 3.8

---

## 🤖 模型安装与管理

### 推荐模型列表

| 模型 | 大小 | 特点 | 适用场景 |
|------|------|------|---------|
| `llama3` | ~4.7GB | Meta最新，中文优秀 | **首选推荐** |
| `llama3:8b` | ~4.7GB | Llama 3 轻量版 | 内存有限时 |
| `mistral` | ~4.1GB | 多语言能力强 | 英文为主 |
| `qwen` | ~4.5GB | 阿里通义千问 | 中文优化 |
| `phi3` | ~2.2GB | 微型模型 | 快速响应 |

### 安装命令

```powershell
# 安装 Llama 3（推荐）
ollama pull llama3

# 安装 Mistral
ollama pull mistral

# 安装 Qwen（中文优化）
ollama pull qwen

# 查看已安装的模型列表
ollama list

# 删除不需要的模型
ollama rm <model_name>
```

### 自定义模型配置

创建/编辑 `Modelfile` 来自定义模型行为：

```powershell
# 创建自定义 Modelfile
notepad Modelfile
```

**示例内容**：
```
FROM llama3

PARAMETER temperature 0.7
PARAMETER num_ctx 4096

SYSTEM """你是一位专业的海龟汤游戏主持人..."""
```

**使用自定义模型**：
```powershell
ollama create my-turtle-soup-host ./Modelfile
```

---

## 🚀 启动与运行

### 基本启动命令

```powershell
# 进入项目目录
cd d:\my_fastapi

# 运行海龟汤游戏
python turtle_soup_ollama.py
```

### 命令行参数选项

```powershell
# 指定模型
python turtle_soup_ollama.py --model=mistral

# 设置难度
python turtle_soup_ollama.py --difficulty=hard

# 指定Ollama服务地址（远程服务器）
python turtle_soup_ollama.py --host=http://192.168.1.100:11434

# 组合使用
python turtle_soup_ollama.py --model=qwen --difficulty=easy --host=http://localhost:11434

# 显示帮助信息
python turtle_soup_ollama.py --help
python turtle_soup_ollama.py -h
```

### 参数说明

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--model` | Ollama模型名称 | `llama3` | `--model=mistral` |
| `--difficulty` | 游戏难度 | `medium` | `--difficulty=hard` |
| `--host` | Ollama服务地址 | `http://localhost:11434` | `--host=http://192.168.1.50:11434` |
| `--help`, `-h` | 显示帮助 | - | `-h` |

---

## 🎮 游戏操作指南

### 主菜单选项

```
┌─────────────────────────────────────┐
│           🎮 主菜单                  │
├─────────────────────────────────────┤
│  1. 🆕 开始新游戏                    │
│  2. ⚙️  设置/配置                    │
│  3. 📋 查看可用模型                  │
│  4. ❓ 游戏帮助                      │
│  5. 🚪 退出                          │
└─────────────────────────────────────┘
```

### 游戏内命令

| 命令 | 说明 | 用法示例 |
|------|------|---------|
| `hint` | 获取提示 | 输入 `hint` |
| `answer` | 提交答案 | 输入 `answer` |
| `status` | 查看进度 | 输入 `status` |
| `help` | 显示帮助 | 输入 `help` 或 `?` |
| `quit` | 退出游戏 | 输入 `quit` 或 `q` |

### 提问技巧

✅ **推荐做法**：
- 从"为什么"开始提问
- 关注时间、地点、人物关系
- 分解复杂问题为多个小问题
- 利用排除法缩小范围

❌ **避免做法**：
- 直接问"真相是什么"
- 一次问多个问题
- 问需要长篇回答的问题
- 重复问类似的问题

---

## ⚙️ 配置详解

### 代码中的默认配置

可以在 `turtle_soup_ollama.py` 文件中修改以下默认值：

```python
# Ollama 配置 (第~80行)
ollama_config = OllamaConfig(
    host="http://localhost:11434",    # Ollama服务地址
    model="llama3",                     # 默认模型
    temperature=0.7,                   # 创造性参数(0-2)
    max_tokens=2048,                   # 最大输出长度
    timeout=120                        # 超时时间(秒)
)

# 游戏配置 (第~90行)
game_config = GameConfig(
    difficulty="medium",              # 难度: easy/medium/hard
    max_questions=20,                 # 最大提问数
    max_hints=3,                      # 最大提示次数
    language="zh"                     # 语言: zh/en
)
```

### 参数调优建议

**Temperature（温度）参数**：
- `0.3-0.5`：更保守、一致的答案（适合严格规则）
- `0.6-0.8`：平衡创造性和一致性（**推荐**）
- `0.9-1.2`：更有创意但可能不稳定

**Max Tokens（最大token）**：
- 题目生成：建议 >= 2048
- 问题判断：建议 >= 512

---

## 🛠️ 故障排查

### 常见问题及解决方案

#### 问题1：无法连接到Ollama服务

**症状**：
```
[错误] 无法连接到Ollama服务！
```

**解决方案**：
```powershell
# 1. 检查Ollama是否运行
ollama --version

# 2. 手动启动服务
ollama serve

# 3. 检查端口是否被占用
netstat -an | findstr 11434

# 4. 如果端口被占用，修改配置
python turtle_soup_ollama.py --host=http://localhost:11435
```

#### 问题2：模型未找到

**症状**：
```
[错误] API调用失败: 404 - model not found
```

**解决方案**：
```powershell
# 1. 列出已安装模型
ollama list

# 2. 安装所需模型
ollama pull llama3

# 3. 使用已有模型启动
python turtle_soup_ollama.py --model=<已安装的模型名>
```

#### 问题3：响应太慢或超时

**症状**：
```
[错误] 请求超时 (120秒)
```

**解决方案**：
```powershell
# 1. 检查硬件资源（CPU/GPU/内存）
tasklist | findstr ollama

# 2. 使用更小的模型
ollama pull llama3:8b
python turtle_soup_ollama.py --model=llama3:8b

# 3. 增加超时时间（需修改代码中的timeout参数）

# 4. 关闭其他占用资源的程序
```

#### 问题4：JSON解析失败

**症状**：
```
[警告] JSON解析失败，尝试修复...
```

**原因**：模型输出的格式不符合预期

**解决方案**：
```powershell
# 1. 尝试不同的模型（某些模型格式更好）
python turtle_soup_ollama.py --model=mistral

# 2. 降低temperature参数（使输出更稳定）
# 修改代码中 temperature 为 0.3-0.5

# 3. 使用更大的模型
ollama pull llama3:70b
python turtle_soup_ollama.py --model=llama3:70b
```

#### 问题5：内存不足

**症状**：
```
OOM (Out of Memory) 错误
```

**解决方案**：
```powershell
# 1. 使用量化版本的小模型
ollama pull llama3:8b-q4_K_M

# 2. 关闭其他应用释放内存

# 3. 增加虚拟内存（Windows）
# 系统属性 → 高级 → 性能设置 → 高级 → 虚拟内存 → 自定义大小
# 建议：设置为物理内存的1.5-2倍
```

---

## 📊 性能优化建议

### 硬件要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 4核 | 8核+ |
| RAM | 8GB | 16GB+ |
| GPU | 无（CPU推理） | NVIDIA GPU 8GB+ VRAM |
| 存储 | 10GB可用空间 | SSD 推荐 |

### 加速方案

**使用GPU加速**：
```powershell
# 检查NVIDIA GPU
nvidia-smi

# Ollama会自动检测并使用GPU
# 如未自动启用，设置环境变量
$env:OLLAMA_GPU="cuda"
ollama serve
```

**减少模型加载时间**：
```powershell
# 将常用模型保持在内存中
ollama run llama3 ""  # 预加载模型

# 或者设置环境变量保持模型常驻
$env:OLLAMA_KEEP_ALIVE="-1"
```

---

## 🔒 安全与隐私

### 本地运行的优点

✅ **数据不离开设备**  
✅ **无网络依赖（除首次下载模型）**  
✅ **无API费用**  
✅ **完全控制模型行为**

### 注意事项

⚠️ 确保Ollama仅监听本地接口（默认）  
⚠️ 不要将Ollama暴露到公网  
⚠️ 定期更新Ollama以获取安全补丁  

---

## 🔄 更新与维护

### 更新Ollama

```powershell
# Windows
winget upgrade Ollama.Ollama

# macOS
brew upgrade ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

### 清理缓存和旧模型

```powershell
# 清理Ollama缓存
ollama prune

# 删除不再使用的模型
ollama rm <old_model>

# 查看磁盘使用情况
du -sh ~/.ollama/models/
```

---

## 📚 扩展开发

### 自定义提示模板

编辑 `turtle_soup_ollama.py` 中的 `PromptTemplates` 类：

```python
class PromptTemplates:
    # 修改系统提示以改变AI性格
    SYSTEM_PROMPT_ZH = """你的自定义系统提示..."""
    
    # 修改题目生成模板
    PUZZLE_GENERATION_PROMPT_ZH = """你的自定义生成提示..."""
```

### 添加新功能

可以扩展的功能点：
- 多玩家模式（网络对战）
- 题目评分系统
- 历史记录持久化存储
- 成就/徽章系统
- 自定义主题包

---

## 🆘 技术支持

### 日志查看

```powershell
# Ollama日志位置
# Windows: %APPDATA%\Ollama\logs\
# macOS/Linux: ~/.ollama/logs/

# 查看实时日志
Get-Content "$env:APPDATA\Ollama\logs\server.log" -Tail -f
```

### 社区资源

- **官方文档**: https://github.com/ollama/ollama
- **模型库**: https://ollama.com/library
- **Discord社区**: https://discord.gg/ollama

---

## 📝 版本历史

### v1.0.0 (2026-05-03)
- ✅ 初始版本发布
- ✅ Ollama集成完成
- ✅ CLI交互界面
- ✅ 中英文支持
- ✅ 完整游戏流程
- ✅ 错误处理机制

---

## 📄 许可证

MIT License - 可自由使用、修改和分发

---

**祝您游戏愉快！🐢**
