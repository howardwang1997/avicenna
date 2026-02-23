# 环境配置指南

本目录记录 avicenna 项目所需的开发环境配置。

## 文件索引

| 文件 | 内容 |
|---|---|
| [miniconda.md](miniconda.md) | Miniconda 安装 & conda 环境管理 |
| [opencode.md](opencode.md) | OpenCode AI 编程助手安装 & 使用 |

## 快速开始

```bash
# 1. 安装 Miniconda（见 miniconda.md）
# 2. 创建项目环境
conda create -n avicenna python=3.10 -y
conda activate avicenna

# 3. 安装项目依赖
pip install -e .

# 4. 配置 VLM API Key
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 5. 运行
avicenna process --pdf bookshelf/CASI_GUIDE/simple_en.pdf
```
