# Roadmap

> avicenna 下一步开发计划

## Phase 1 — 知识库构建（当前重点）

### 1.1 向量化入库

- [ ] 将 `knowledge/` 下处理好的 Markdown 切分为语义 chunk（按标题/段落）
- [ ] 使用 embedding 模型（如 `text-embedding-3-small` 或 `bge-m3`）生成向量
- [ ] 存入向量数据库（Milvus / Chroma / Qdrant），附带 frontmatter 元数据作为过滤字段
- [ ] 图片描述文本一并入库，支持以文搜图

### 1.2 RAG 检索接口

- [ ] 封装检索 API：输入自然语言问题，返回最相关的 Markdown 片段 + 来源信息
- [ ] 支持按 `organization`、`language`、`tags` 等元数据过滤
- [ ] 实现 rerank（如 Cohere rerank 或 cross-encoder）提升精度

### 1.3 问答 / 对话

- [ ] 接入 LLM（Qwen / GPT-4o）构建 RAG 问答链
- [ ] 支持多轮对话，自动携带上下文
- [ ] 回答附带引用来源（PDF 名称 + 章节）

## Phase 2 — 数据质量提升

### 2.1 提取质量

- [ ] 对比 VLM-transformer 和 Pipeline 后端在各 PDF 上的提取效果，建立评估基准
- [ ] 处理表格提取：当前 Markdown 中的表格可能丢失结构，考虑保留为 HTML table 或 JSON
- [ ] 公式提取优化：确认 LaTeX 公式在 Markdown 中正确渲染

### 2.2 图片处理

- [ ] 对重复 / 近似图片去重（perceptual hash）
- [ ] 图片 OCR：提取图片内嵌文字（如流程图、标注图），补充到描述中
- [ ] 支持更多 VLM 模型选择（GPT-4o-mini、Gemini Flash 等）

### 2.3 多语言

- [ ] 改进语言检测：从 PDF 内容而非文件名推断语言
- [ ] 中英文内容对齐：同一教材的中英版本建立对应关系

## Phase 3 — 工程化

### 3.1 批处理 & 增量更新

- [ ] 增量处理：仅处理新增 / 修改的 PDF，跳过未变化的文件（基于文件 hash）
- [ ] 并行处理：多 PDF 并发提取（`asyncio` / `multiprocessing`）
- [ ] 处理进度持久化：中断后可恢复

### 3.2 可观测性

- [ ] 处理报告：每次批处理后生成 summary（成功/失败/跳过，耗时统计）
- [ ] 结构化日志输出到文件，方便排查

### 3.3 部署

- [ ] Docker 镜像：打包 avicenna + MinerU + 依赖，一键运行
- [ ] CI：GitHub Actions 跑 lint + 单元测试
- [ ] GPU 云环境配置文档（如 AutoDL / RunPod）

## Phase 4 — 应用层（远期）

- [ ] Web UI：上传 PDF → 预览提取结果 → 入库
- [ ] 滑雪教学助手 Chatbot：面向教练 / 学员的问答界面
- [ ] 知识图谱：从教材中提取技术动作、教学进阶关系，构建结构化图谱
