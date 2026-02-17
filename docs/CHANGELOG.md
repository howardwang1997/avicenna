# Changelog

## 2026-02-17 — 可配置 MinerU 后端 + 本地 .env

### 背景

avicenna 原先硬编码使用 `vlm-transformers` 后端，要求 CUDA GPU 环境；同时依赖 `../sciminer/.env` 读取 VLM API Key，耦合了外部项目。本次改动解除这两个限制。

### 变更内容

#### 1. 新建 `.env`（项目根目录）

- 在 avicenna 项目内创建独立的 `.env` 文件，包含 `VLM_MODEL_NAME`、`VLM_BASE_URL`、`VLM_API_KEY`
- 新建 `.env.example` 作为模板，方便新用户配置

#### 2. `avicenna/config.py` — 移除 sciminer 依赖

- 删除 `_SCIMINER_ENV` 路径及其 `load_dotenv` 调用
- 仅保留本地 `.env` 加载
- `MinerUConfig.backend` 默认值从 `"vlm-transformers"` 改为 `"auto"`
- `MinerUConfig` 新增 `language` 字段，默认 `"en"`

#### 3. `avicenna/extractor.py` — 双后端支持

- 新增 `_has_gpu()`: 通过 `torch.cuda.is_available()` 检测 GPU，torch 未安装时返回 `False`
- 新增 `_extract_vlm()`: 原有 VLM-transformer 提取路径，抽取为独立函数
- 新增 `_extract_pipeline()`: CPU 友好的 pipeline 后端，使用 `pipeline_doc_analyze` → `pipeline_result_to_middle_json` → `pipeline_union_make`
- `extract_pdf()` 根据 backend 配置自动分发:
  - `"auto"` → 检测 GPU → 选择 `vlm-transformers` 或 `pipeline`
  - `"vlm-transformers"` / `"pipeline"` → 直接使用指定后端

#### 4. `avicenna/cli.py` — 新增 `--backend` 参数

- 新增 `--backend` 命令行参数，可选值 `auto | vlm-transformers | pipeline`，默认 `auto`
- 参数值传递至 `config.mineru.backend`

### 涉及文件

| 文件 | 类型 |
|---|---|
| `.env` | 新建 |
| `.env.example` | 新建 |
| `avicenna/config.py` | 修改 |
| `avicenna/extractor.py` | 修改 |
| `avicenna/cli.py` | 修改 |

### 验证方式

```bash
# 自动检测无 GPU → 使用 pipeline 后端
avicenna process --pdf bookshelf/CASI_GUIDE/simple_en.pdf

# 显式指定后端
avicenna process --pdf bookshelf/CASI_GUIDE/simple_en.pdf --backend pipeline
```
