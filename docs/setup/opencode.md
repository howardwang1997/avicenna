# OpenCode 安装 & 使用

> 官方文档: https://opencode.ai/docs/
> GitHub: https://github.com/opencode-ai/opencode

OpenCode 是一个开源的终端 AI 编程助手，支持 75+ 模型（Claude、OpenAI、Gemini、本地模型等），提供 TUI 界面。

## 安装

```bash
# 快速安装（推荐）
curl -fsSL https://opencode.ai/install | bash

# 或通过包管理器
brew install anomalyco/tap/opencode      # macOS Homebrew
npm install -g opencode-ai               # npm
```

验证：

```bash
opencode --version
```

---

## 初始配置

### 1. 连接 AI 提供商

```bash
opencode          # 启动 TUI
# 在 TUI 内执行:
/connect          # 选择提供商 → 认证 → 粘贴 API Key
```

支持的提供商：

| 提供商 | 说明 |
|---|---|
| OpenCode Zen | OpenCode 官方托管，精选模型 |
| Anthropic | Claude 系列 |
| OpenAI | GPT 系列 |
| Google | Gemini 系列 |
| GitHub Copilot | Copilot 订阅用户可直接认证 |
| Ollama | 本地模型（免费） |

### 2. 项目初始化

```bash
cd /path/to/your/project
opencode
/init             # 分析项目结构，生成 AGENTS.md
```

`/init` 会扫描项目生成 `AGENTS.md` 文件，记录项目结构和编码规范，供 AI 参考。

---

## 日常使用

### TUI 模式（交互式）

```bash
opencode                           # 启动 TUI
opencode -c                        # 继续上一次会话
opencode -m claude-sonnet-4-5      # 指定模型
opencode -s <session-id>           # 恢复特定会话
```

TUI 内快捷操作：

| 按键 / 命令 | 作用 |
|---|---|
| `Tab` | 切换 Plan 模式 ↔ Build 模式 |
| `/init` | 初始化项目 |
| `/connect` | 连接提供商 |
| `/undo` | 撤销最近更改 |
| `/redo` | 恢复撤销 |
| `/share` | 生成分享链接 |

**Plan 模式**：AI 只给出建议方案，不修改代码
**Build 模式**：AI 直接执行修改

### 非交互模式（单次执行）

```bash
# 直接提问
opencode run "解释这个函数的作用"

# 指定模型
opencode run -m claude-sonnet-4-5 "重构 config.py 中的配置加载逻辑"
```

### 远程 / 服务器模式

```bash
# 启动无头服务
opencode serve --port 4096

# 启动 Web 界面
opencode web

# 从另一台机器连接
opencode attach http://10.20.30.40:4096
```

---

## 管理命令

```bash
# 会话管理
opencode session list              # 查看所有会话
opencode export <session-id>       # 导出为 JSON

# 模型管理
opencode models                    # 列出可用模型
opencode models anthropic          # 列出特定提供商的模型

# 认证管理
opencode auth list                 # 查看已连接的提供商
opencode auth login                # 登录
opencode auth logout               # 登出

# MCP 服务器
opencode mcp list                  # 列出 MCP 服务器
opencode mcp add <name> <command>  # 添加 MCP 服务器

# 统计 & 维护
opencode stats                     # Token 用量和费用统计
opencode upgrade                   # 升级到最新版
opencode uninstall                 # 卸载
```

---

## 环境变量

```bash
# 可选配置
export OPENCODE_DISABLE_AUTOUPDATE=1   # 禁用自动更新
export OPENCODE_CONFIG=/path/to/config  # 自定义配置路径
```

---

## 在 avicenna 项目中使用

```bash
cd /path/to/avicenna
opencode
/init                              # 首次使用，生成 AGENTS.md
# 然后直接对话，例如：
# "帮我处理 extractor.py 中 pipeline 后端的错误处理"
# "给 filter.py 添加单元测试"
```
