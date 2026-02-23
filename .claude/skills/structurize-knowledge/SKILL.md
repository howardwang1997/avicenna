---
name: structurize-knowledge
description: 将 markdown notes 按语义切分为结构化知识库，生成子主题文件和索引
---

# Structurize Knowledge

将长篇 markdown 文档按语义切分为子主题级别的独立知识文件，生成结构化知识库。

**核心原则：保留完整原文内容，目标是「切分」不是「压缩」。**

---

## 1. 输入检测

接受一个**目录路径**参数，自动判断目录结构类型。

### 检测方法

```
Glob "{path}/**/content.md"
```

根据找到的 `content.md` 相对于输入目录的路径深度判断层级。

**输出路径**: 所有 knowledge 输出统一存放在项目根目录的 `knowledge/{org_name}/` 下（集中式知识库）。

`{org_name}` 的确定方式：
- 如果用户通过参数指定了输出名称，使用该名称
- 否则根据输入目录名和 `content.md` 中的 `source_organization` 推断（如 `SBINZ_manual`、`CASI_reference_guide`）
- 用 AskUserQuestion 让用户确认或自定义 `{org_name}`

| 输入类型 | 判断条件 | 输出路径 |
|---------|---------|---------|
| 叶子目录 | 目录直接包含 `content.md`（深度 0） | `knowledge/{org_name}/` |
| 一级子目录 | 子目录包含 `content.md`（深度 1） | `knowledge/{org_name}/` |
| 二级子目录 | 子目录的子目录包含 `content.md`（深度 2） | `knowledge/{org_name}/` |

如果输出路径 `knowledge/{org_name}/` 已存在，用 AskUserQuestion 提示用户确认是否覆盖。

---

## 2. 预处理规则

对每个 `content.md` 的内容，按顺序执行以下预处理：

### 2a. 提取 YAML frontmatter

解析以下字段供后续使用：
- `name` — 文档标识
- `source_pdf` — 来源 PDF 路径
- `source_organization` — 来源组织（如 CASI、SBINZ、NZSBI）
- `language` — 语言代码（en、zh 等）
- `tags` — 标签列表

### 2b. 移除图片链接（多行处理）

PDF 提取后的 image link 经常跨多行，例如：
```
![A snowboarder performing
a carved turn on groomed
terrain](images/abc123.jpg)
```

使用两阶段处理：
1. **多行合并 pass**：检测以 `![` 开头但当前行没有 `](` 闭合的行，持续拼接后续行直到找到 `](...)` 闭合
2. **单行移除 pass**：对合并后的行执行 `![...](images/...)` 移除

### 2c. 移除 VLM 生成内容

移除所有 VLM（Vision Language Model）生成的描述内容。使用以下逐行模式匹配规则：

**a. 图片文件名引用**
- `> **[Image: ...]**` 格式

**b. 所有 blockquote 行**
- `^>` 开头的行（VLM 描述的主要载体）

**c. 子级标题（H2/H3/H4）**
- `^#{2,4} ` 开头的行
- 原因：源文档只使用 H1，所有 H2+ 标题均为 VLM 生成

**d. VLM 结构化描述行**
- `^\d+\.\s+\*\*` — 编号+粗体项（如 `1. **Technique**: ...`）
- `^-\s+\*\*[^*]+\*\*\s*:` — 粗体键值对（如 `- **Stance Width**: narrow`）
- `^\s+-\s+\*\*[^*]+\*\*\s*:` — 缩进粗体键值对

**e. VLM 叙述性短语（行首匹配，不区分大小写）**
- "This image", "This instructional image", "The image"
- "Overall,", "In summary,"
- "The technique being demonstrated"
- "The snowboarder(s) is/are executing/performing/demonstrating"
- "no visible labels", "no arrows", "no diagrams"

**f. VLM 缩进描述行（无粗体格式）**
- `^\s+-\s+` 开头 + 包含 VLM 特征词（"image", "illustrates", "depicts", "shows a snowboarder", "visible in"）
- 注意：普通列表项（不含 VLM 特征词）必须保留

**g. 占位文本**
- "SCAN FOR VIDEOS" 或类似占位符行

### 2d. 删除 VLM 标记

删除所有 `<!-- VLM_PROCESSED -->` 标记。

### 2e. 格式清理

- 删除行尾空白（trailing whitespace）
- 删除孤立的 `---` 行（前后为空行的分隔线，来自 VLM 分段）
- 压缩连续空行：3 个或以上连续空行压缩为 2 行

---

## 3. 语义切分策略

**核心原则：不要摘要化。** 始终保留完整原文。切分的目的是将一个大文件拆成多个小文件，每个文件包含一个完整子主题的所有内容。

**关键背景**: 这些文档只使用 `#`（H1）标题，无 H2/H3 层级。因此需要基于语义分析切分，不能简单按标题级别切。文档可能有大量 H1 标题但只有少量实际 topic（如 SBINZ 手册有 1,570 个 H1 但只有 ~136 个实际 topic），因为许多 H1 是 topic 内部的子节标题。

### Step 3a: 结构分析

1. 读取文件开头部分，查找**目录（TOC）**。大多数大文档有 TOC，列出了所有子主题
2. 用 Grep 获取所有 H1 标题及行号：`Grep "^# " {file_path}` （使用 output_mode: "content"，带行号）
3. 构建 header map：每个标题的位置、文本、与下一个标题之间的行数

### Step 3b: LLM 语义分组

基于 header map 和 TOC（如有），对所有 H1 标题进行语义分组。

**输入**：完整的 H1 标题列表（带行号），以及 TOC 内容（如有）

**任务**：判断每个 H1 是「topic 标题」还是「子节标题」，并将子节标题归入其所属的 topic。

**判断原则**：
- **topic 标题** = 代表一个独立的知识主题或教学单元（如技能名称、教学方法名称、概念名称）
- **子节标题** = topic 内部的结构性分节（如 "WHAT, WHY, HOW"、"EXAMPLE"、"CORRECTIVE TEACHING" 这些是 topic 的组成部分，不是独立主题）

**具体做法**：
1. **如果有 TOC** → TOC 中的叶子条目即为 topic，其余为子节
2. **如果没有 TOC** → 阅读标题列表，识别哪些标题代表独立主题（通常出现 1-2 次），哪些标题是文档模板中反复出现的结构性标题（通常出现多次且含义通用）
3. 输出一个分组方案：每个 topic 包含其标题和所有子节标题的行号范围

**注意事项**：
- 不要依赖出现次数作为唯一判据，要综合语义理解
- 单字母/数字标题（如 `# A`, `# 1`）通常是索引/OCR 残留，跳过
- 一个 topic 的内容 = 从 topic 标题行到下一个 topic 标题行之前
- 标题页、版权声明、TOC 本身 → 合并为一个 `document-overview` 主题，或如果内容极少则跳过

### Step 3c: 分组方案验证

- 每个 topic 的内容量应在 10-300 行之间
  - < 10 行 → 可能需要与相邻 topic 合并
  - \> 300 行 → 检查是否可在子节标题处拆分
- 确保没有遗漏任何内容行

---

## 4. 大文件处理策略（> 2000 行）

有些文件非常大（10000+ 行），无法一次性读入处理。使用分块策略。

### 处理步骤

1. 获取文件总行数：`wc -l {file_path}`
2. 获取所有 H1 标题位置：`Grep "^# " {file_path}` （output_mode: "content"，带行号）
3. 读取前 2000 行（包含 frontmatter 和 TOC），建立完整主题地图
4. 按 2000 行/块、200 行重叠分块处理：
   - `Read {file_path}` offset=1, limit=2000 → 处理该块中的完整主题
   - `Read {file_path}` offset=1801, limit=2000 → 处理跨块主题
   - 循环至文件末尾
5. **边处理边写入文件**，不要在内存中累积所有主题内容
6. 用 header map 确保每个主题被完整读取，不会在块边界处截断

### 注意事项

- 利用 Step 3a 中建立的 header map 确定每个块中包含哪些完整主题
- 如果一个主题跨越块边界，在下一个块中完整处理它
- 处理完一个块的所有完整主题后，立即写入文件

---

## 5. 输出文件格式

### 5a. Topic 文件

每个子主题生成一个独立的 `.md` 文件。内容必须详尽完整，不做摘要。

```yaml
---
title: "{Topic Title}"
name: {org}-{section-slug}-{topic-slug}
source_document: {source_pdf}
source_organization: {org}
language: {lang}
description: "{从 topic 内容提取的 1-2 句核心教学摘要}"
tags: [{org-lower}, {section-slug}, {category}]
---

# {Topic Title}

{完整原文内容，不摘要，不压缩}
```

**Frontmatter 格式要求**：所有值必须为单行格式（如 `tags: [a, b, c]`），不使用多行 YAML 语法（如 `tags:\n  - a`）。这是为了兼容下游上下文数据库的 frontmatter 解析器。

**description 字段**：不要使用模板化描述（如 `"{Topic Title} - {org} snowboard instruction knowledge"`），而是从 topic 内容中提取 1-2 句有区分度的摘要。例如：`"The fundamental standing position on a snowboard, emphasizing balanced weight distribution and flexed joints"`。

**name 格式**:
- 有 section 层级时：`{org}-{section-slug}-{topic-slug}`，全小写，用连字符。其中 `{section-slug}` 来自输出目录名。例如：`sbinz-c-c-turns`
- 叶子目录输入（无 section 层级）：`{org}-{topic-slug}`。例如：`sbinz-safety-risk-management`

**category 标签**从以下列表选择最匹配的一个：
- `safety` — 安全与风险管理
- `teaching-theory` — 教学理论与方法
- `technique` — 技术动作与技能
- `equipment` — 装备相关
- `assessment` — 评估与认证
- `progression` — 进阶与发展
- `freestyle` — 自由式/公园
- `children` — 儿童教学
- `general` — 通用/概述

**文件名**: `{topic-slug}.md`，全小写，连字符分隔。例如：`safety-risk-management.md`

### 5d. 标题层级修正

写入 topic 文件时，保留第一个 H1（topic 标题），将后续所有 H1 降为 H2。

源文档只使用 H1，切分后每个 topic 文件可能包含多个原始 H1（topic 标题 + 子节标题如 WHAT/WHY/HOW、CORRECTIVE TEACHING 等）。为保持正确的标题层级树，需要将子节标题降级。

**Before**（topic 文件内部）:
```markdown
# Two-Footed Orientation
...
# WHAT, WHY, HOW
...
# CORRECTIVE TEACHING
```

**After**:
```markdown
# Two-Footed Orientation
...
## WHAT, WHY, HOW
...
## CORRECTIVE TEACHING
```

### 5b. `.index.json`

```json
{
  "title": "Knowledge Base Title",
  "source": "Source Organization / Document",
  "generated_at": "2026-02-19T...",
  "total_topics": 42,
  "sections": {
    "section-slug": {
      "title": "Section Title",
      "path": "section-slug/",
      "topic_count": 5,
      "topics": [
        {
          "slug": "topic-slug",
          "title": "Topic Title",
          "tags": ["org", "section-slug", "category"]
        }
      ]
    }
  }
}
```

对于叶子目录输入（只有一个 content.md，无 section 层级），使用文档的 TOC 结构或语义分组作为 sections。如果没有明显的 section 结构，将所有 topics 放在一个 section 下。

### 5c. `.index.md`

人类可浏览的索引文件：

```markdown
# {Title} - Knowledge Base

**Source:** {source_organization}
**Document:** {source_pdf}
**Generated:** {date}
**Total Topics:** {N}

## How to Use

**To search:** `Grep "keyword" knowledge/{org_name}/`
**To browse:** Check section indexes below

---

## {Section Title}

**Path:** `{section-slug}/`
**Topics:** {N}

- [{Topic Title}]({section-slug}/{topic-slug}.md)
- [{Topic Title}]({section-slug}/{topic-slug}.md)
...
```

---

## 6. 输出目录结构

根据输入类型决定目录结构：

### 叶子目录输入（目录直接包含 content.md）

```
knowledge/{org_name}/
├── .index.json
├── .index.md
├── topic-one.md
├── topic-two.md
└── topic-three.md
```

Topic 文件直接放在 `knowledge/{org_name}/` 下（无 section 子目录），除非文档本身有明确的多级 section 结构。

### 一级子目录输入（多 section）

```
knowledge/{org_name}/
├── .index.json
├── .index.md
├── a-learning-environment/
│   ├── topic-a.md
│   └── topic-b.md
├── b-technical/
│   └── topic-c.md
└── ...
```

每个 section 对应原始目录中的一个子目录（包含 `content.md` 的那个），section 子目录直接放在 `knowledge/{org_name}/` 下。

### 二级子目录输入

```
knowledge/{org_name}/
├── .index.json
├── .index.md
├── parent-dir-one/
│   ├── sub-dir-one/
│   │   └── *.md
│   └── sub-dir-two/
│       └── *.md
├── parent-dir-two/
│   └── sub-dir-three/
│       └── *.md
└── ...
```

保留两级目录结构，section 子目录直接放在 `knowledge/{org_name}/` 下。

---

## 7. 边界情况处理

### 极小文档（< 50 行）
生成单个 topic 文件，将整个文档内容作为一个主题。

### 中文文档
- 保留中文内容原文不变
- slug 使用拼音或英文翻译（如 `教学理论` → `teaching-theory`）
- `language` 字段设置为 `zh`

### 重复标题
用父章节名作为前缀消歧。例如两个 `# Introduction` 分别在 Section 2 和 Section 5 下：
- `safety-introduction.md`
- `skills-concept-introduction.md`

### 空内容主题
如果一个 H1 标题下完全没有内容（0 行），跳过不生成文件。

---

## 8. 执行流程总结

1. **检测输入** — 确定输入类型和输出路径
2. **检查输出路径** — 如已存在 `knowledge/{org_name}/` 目录，询问用户
3. **遍历每个 `content.md`**：
   a. 读取并预处理内容（§2）
   b. 分析结构，建立 header map（§3a）
   c. LLM 语义分组，确定 topic 边界（§3b），验证分组方案（§3c），大文件使用分块策略（§4）
   d. 为每个主题生成 topic 文件（§5a）
4. **生成 `.index.json`**（§5b）
5. **生成 `.index.md`**（§5c）
6. **输出统计** — 报告处理了多少文件、生成了多少 topic、总行数等
