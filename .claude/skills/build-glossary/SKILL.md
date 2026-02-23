---
name: build-glossary
description: 从 notes/ 中提取单板滑雪教学术语，生成中英双语术语表
---

# Build Bilingual Glossary

扫描所有 notes/ 目录，提取单板滑雪教学术语，生成分类中英双语术语表。

**核心原则：优先使用文档中已有的中文翻译，AI 补充翻译需标记来源以供人工审核。**

---

## 0. 执行参数

接受一个可选的目录路径参数：
- 无参数 → 处理所有 `notes/`
- 有参数（如 `notes/SBINZ*`） → 仅处理匹配的目录

**输出路径**: `knowledge/glossary/`

如果 `knowledge/glossary/` 已存在，用 AskUserQuestion 询问用户是否覆盖。

---

## 1. 扫描 — 识别术语来源

### 1a. 英文术语来源（按优先级）

**优先级 1 — 已有术语表**:
```
Glob "knowledge/*/glossary/*.md"
```
这些文件（如 SBINZ 的 snowboard-jargon.md ~760 术语，tricktionary.md ~60 术语）是最完整的术语来源。

**优先级 2 — 知识主题文件**:
```
Glob "knowledge/**/*.md"
```
排除 glossary/ 目录和 `.index.*` 文件。从 H1 标题提取关键术语。

**优先级 3 — 原始 content.md**:
仅当该目录没有对应 `knowledge/` 输出时才回退到 `content.md`。

### 1b. 中文文档来源（用于翻译匹配）

扫描以下中文文档：
```
notes/NZSBI_GUIDE/SBINZ Mandarin Level One*/content.md
notes/CASI_GUIDE/*Chinese*/content.md
notes/CASI_GUIDE/*chinese*/content.md
```

也检查 knowledge/ 目录中 language 为 zh 的文件：
```
Grep "language: zh" knowledge/**/*.md
```

将所有中文文档内容读入内存，作为翻译查找的语料库。

---

## 2. 提取英文术语

### 2a. 从术语表文件提取

术语表文件格式：每个 `# Term` 后跟定义段落。

```markdown
# Absorption

Flexion or extension of the joints (e.g. ankles, knees and hips) to aid pressure management.
```

解析规则：
1. 每个 H1 标题（`# ...`）= 一个术语候选
2. 跳过单字母标题（`# A`, `# B` 等）— 这些是字母分隔符
3. 跳过文件首个标题如果是文件总标题（如 `# SNOWBOARD JARGON`, `# TRICKTIONARY`）
4. 术语名 = H1 文本，定义 = H1 后到下一个 H1 之间的所有文本
5. 记录来源组织（从 YAML frontmatter 的 `source_organization` 字段获取）

### 2b. 从知识文件提取

知识文件的 H1 标题代表子主题名称，有些是术语性质的。

提取规则：
1. 读取文件 YAML frontmatter 获取 `tags` 和 `source_organization`
2. 提取所有 H1 标题
3. 仅保留术语性质的标题（名词/名词短语/技术术语），跳过描述性标题（如 "How to Teach Beginners"、"Day 1 第一天"）
4. 定义 = H1 后的前 2-3 句话（不超过 200 字）作为摘要
5. 记录来源组织

### 2c. 去重

以规范化 key 合并术语：
```
key = lowercase(term).replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-').trim('-')
```

合并规则：
- 保留最完整的定义（字数最多的）
- 合并来源组织列表（如 `["SBINZ", "CASI"]`）
- 如果同一术语在 glossary 和 knowledge 文件中都出现，优先用 glossary 的定义

---

## 3. 匹配中文翻译

中文文档通常采用**英中对照格式**：一段英文后紧跟对应中文翻译。

### 3a. 读取中文语料库

读取所有 §1b 中识别的中文文档。将内容按段落分割，建立英中对照对：

识别模式：
- **逐段对照**: 英文段落后紧跟中文段落（检测 CJK 字符 `[\u4e00-\u9fff]`）
- **行内对照**: 同一标题中包含英中两种语言（如 `# Pre-Requisites 课前必备条件`）
- **术语对照**: 英文术语后括号内有中文（如 `basic stance（基础站姿）`）

### 3b. 术语匹配

对每个英文术语：
1. 在中文文档中搜索该英文术语的出现位置
2. 检查该位置附近（前后 5 行）是否有中文文本
3. 如果找到包含该英文术语的英中对照段落，提取中文翻译
4. 记录来源文档路径

匹配结果标记为 `source: document`。

### 3c. 常见术语快速匹配表

以下常见术语对可以直接使用，加速匹配：

| English | 中文 |
|---------|------|
| basic stance | 基础站姿 |
| snowboard | 单板滑雪 / 雪板 |
| edge | 边刃 / 刃 |
| turn | 转弯 |
| traverse | 横切 |
| skidded turn | 搓雪转弯 |
| carving | 刻滑 |
| ollie | Ollie跳 |
| switch | 反脚 |
| toe edge / heel edge | 前刃 / 后刃 |
| fall line | 滚落线 |
| terrain park | 地形公园 |
| halfpipe | 半管/U型池 |
| freestyle | 自由式 |
| freeriding | 自由滑行 |
| instructor | 教练 |
| examiner | 考官 |
| certification | 认证 |
| progression | 渐进教学步骤 |
| lesson format | 课堂形式 |

这些仅在文档中未找到翻译时作为回退使用，且标记为 `source: document`（因为来自已知文档）。

---

## 4. AI 翻译补充

对于没有文档来源中文翻译的术语：

1. 根据英文定义和单板滑雪教学语境，生成中文翻译
2. 翻译要求：
   - 使用中国大陆单板滑雪教学常用术语
   - 优先使用已有的行业标准译法
   - 术语翻译简洁（通常 2-6 个中文字）
   - 定义翻译准确完整
3. 标记为 `source: ai-generated`

---

## 5. 分类

将每个术语分配到以下 9 个类别之一（与 structurize-knowledge 技能一致）：

| 类别 slug | 中文名 | 典型术语示例 |
|-----------|--------|-------------|
| `safety` | 安全与风险管理 | Alpine Snow Code, hazard, avalanche |
| `teaching-theory` | 教学理论与方法 | AAA cycle, VAK, lesson format, feedback |
| `technique` | 技术动作与技能 | stance, edge, turn, carving, angulation |
| `equipment` | 装备相关 | binding, boot, board flex, sidecut |
| `assessment` | 评估与认证 | certification, exam, rider analysis |
| `progression` | 进阶与发展 | beginner, intermediate, advanced, levels |
| `freestyle` | 自由式/公园 | ollie, 180, rail, halfpipe, ATTL |
| `children` | 儿童教学 | CAP model, profiling children, creative lessons |
| `general` | 通用/概述 | general jargon, organization names |

分类依据：
- 如果术语来自 glossary 文件的 `tags` 字段，优先使用已有标签
- 如果术语来自 knowledge 文件，使用该文件所在 section 目录名推断
- 否则根据术语定义内容判断最匹配的类别

---

## 6. 输出

### 6a. 目录结构

```
knowledge/glossary/
├── .index.json          # 机器可读索引
├── .index.md            # 人类可浏览索引
├── safety.md
├── teaching-theory.md
├── technique.md
├── equipment.md
├── assessment.md
├── progression.md
├── freestyle.md
├── children.md
└── general.md
```

### 6b. 分类文件格式

每个分类文件的结构：

```markdown
---
title: "Technique — 技术动作与技能"
category: technique
generated_at: "2026-02-19T..."
term_count: 320
---

# Technique — 技术动作与技能

术语按英文字母顺序排列。

---

### Absorption / 吸收
- **English**: Flexion or extension of the joints (e.g. ankles, knees and hips) to aid pressure management.
- **中文**: 关节（如踝、膝、髋）的屈伸，用于辅助压力管理。
- **Translation**: 📄 document — SBINZ Mandarin Level One
- **Organizations**: SBINZ, CASI

---

### Angulation / 角度调整
- **English**: Forming of angles between bones through flexing and extending joints.
- **中文**: 通过屈伸关节在骨骼之间形成角度。
- **Translation**: 🤖 ai-generated — needs review
- **Organizations**: SBINZ

---
```

关键格式规则：
- Frontmatter 所有值必须为单行格式，不使用多行 YAML 语法（兼容下游上下文数据库的 frontmatter 解析器）
- 术语条目使用 H3（`###`）
- 格式：`### {English Term} / {中文翻译}`
- 定义使用粗体标签前缀的列表项
- 翻译来源用 emoji 标记：`📄` = 文档来源，`🤖` = AI 生成
- 文档来源标注具体文档名称
- 条目之间用 `---` 分隔
- 术语按英文字母排序

### 6c. `.index.json`

```json
{
  "title": "Snowboard Instruction Bilingual Glossary",
  "description": "中英双语单板滑雪教学术语表",
  "generated_at": "2026-02-19T...",
  "total_terms": 820,
  "translation_stats": {
    "document_sourced": 150,
    "ai_generated": 670
  },
  "categories": {
    "technique": {
      "title": "Technique — 技术动作与技能",
      "count": 320,
      "file": "technique.md"
    }
  },
  "terms": {
    "absorption": {
      "en": "Absorption",
      "zh": "吸收",
      "category": "technique",
      "translation_source": "document",
      "source_doc": "SBINZ Mandarin Level One",
      "organizations": ["SBINZ", "CASI"]
    }
  }
}
```

### 6d. `.index.md`

```markdown
# Snowboard Instruction Bilingual Glossary
# 单板滑雪教学双语术语表

**Generated:** {date}
**Total Terms:** {N}
**Document-sourced translations:** {N} 📄
**AI-generated translations:** {N} 🤖 (needs review)

## How to Use

**Search:** `Grep "keyword" knowledge/glossary/`
**Browse:** Check category files below
**Review:** Search for `🤖 ai-generated` to find translations needing human review

---

## Categories

### [Technique — 技术动作与技能](technique.md)
{N} terms

### [Safety — 安全与风险管理](safety.md)
{N} terms

...
```

---

## 7. 大文件处理策略

术语量可能超过 800 个，需要分批处理。

### 7a. 术语提取分批

按来源文件逐个处理，避免一次性加载所有内容：
1. 先处理 glossary 文件（术语最密集，格式最规整）
2. 再处理 knowledge 文件（逐个 section 目录处理）
3. 最后处理 content.md 回退来源

### 7b. 中文匹配分批

中文文档逐个读取和匹配：
1. 每读一个中文文档，对所有待匹配术语扫描一遍
2. 已匹配的术语标记完成，减少后续搜索量

### 7c. 输出分批写入

按类别文件逐个写入：
1. 所有术语提取和翻译完成后
2. 按类别分组
3. 每个类别内按字母排序
4. 逐个写入分类文件
5. 最后生成 `.index.json` 和 `.index.md`

### 7d. 并行处理

可以使用 Task agents 并行处理独立的步骤：
- 多个中文文档可以并行读取和匹配
- 多个分类文件可以并行写入

---

## 8. 执行流程总结

```
1. 检查输出目录 → 如已存在，询问用户
2. 扫描术语来源 → Glob 查找 knowledge/ 下的 glossary/、topic 文件，以及 notes/ 下的 content.md（§1）
3. 扫描中文文档 → Glob 查找中文文档（§1b）
4. 提取英文术语 → 解析 glossary 和 knowledge 文件（§2）
5. 去重合并 → 规范化 key 去重，保留最完整定义（§2c）
6. 读取中文语料 → 加载所有中文文档内容（§3a）
7. 匹配中文翻译 → 搜索术语在中文文档中的翻译（§3b）
8. AI 补充翻译 → 为未匹配术语生成中文翻译，标记来源（§4）
9. 分类 → 将每个术语分配到 9 个类别之一（§5）
10. 写入分类文件 → 按类别按字母排序输出（§6b）
11. 生成 .index.json → 机器可读索引（§6c）
12. 生成 .index.md → 人类可浏览索引（§6d）
13. 输出统计 → 报告术语总数、翻译来源分布、各类别术语数
```

---

## 9. 边界情况处理

### 数字/符号开头的术语
如 `180/360/540 (etc)`, `50-50` — 保留原始格式，排序时排在字母术语之前。

### 同一术语多个翻译
如果不同中文文档对同一术语有不同翻译，全部记录，用 `/` 分隔。

### 纯中文术语
中文文档中出现的无英文对应的中文术语（极少见），放入 `general.md`，英文字段标注 `N/A`。

### 跨类别术语
如果一个术语明显属于多个类别，放入最相关的一个类别。不重复放置。

### 术语中包含特殊格式
部分术语包含 `**粗体**` 或括号说明 — 提取时清除格式标记，保留纯文本。
