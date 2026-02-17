# Avicenna

PDF to Markdown preprocessing pipeline for ski/snowboard instruction manuals. Converts PDF books into enriched Markdown with intelligent image filtering and VLM-powered descriptions.

## Architecture

```
bookshelf/*.pdf
    │
    ▼
┌──────────────────────────────────────────┐
│  Stage 1 — MinerU PDF Extraction         │
│  (VLM-transformer on GPU / Pipeline CPU) │
└──────────────┬───────────────────────────┘
               ▼
┌──────────────────────────────────────────┐
│  Stage 2 — Size-Based Image Filtering    │
│  (min 10 KB, 100 px, aspect ratio < 10)  │
└──────────────┬───────────────────────────┘
               ▼
┌──────────────────────────────────────────┐
│  Stage 3 — VLM Semantic Filtering        │
│  (Qwen VL: MEANINGFUL / NOT_MEANINGFUL)  │
└──────────────┬───────────────────────────┘
               ▼
┌──────────────────────────────────────────┐
│  Stage 4 — VLM Description + Assembly    │
│  (2-4 sentence image descriptions,       │
│   YAML frontmatter, final Markdown)      │
└──────────────┬───────────────────────────┘
               ▼
knowledge/{pdf_stem}/
  ├── content.md
  └── images/
```

## Quick Start

### 1. Install

```bash
pip install -e .
```

### 2. Configure

Copy the example env file and fill in your VLM API key:

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run

```bash
# Process a single PDF (auto-detects backend: GPU → VLM, CPU → Pipeline)
avicenna process --pdf bookshelf/CASI_GUIDE/simple_en.pdf

# Explicit backend selection
avicenna process --pdf bookshelf/CASI_GUIDE/simple_en.pdf --backend pipeline

# Process all PDFs in bookshelf/
avicenna process

# Force re-process (ignore cached results)
avicenna process --pdf bookshelf/CASI_GUIDE/simple_en.pdf --force
```

### CLI Options

```
avicenna process [OPTIONS]

  --pdf PATH          Single PDF to process (relative or absolute)
  --backend BACKEND   MinerU backend: auto | vlm-transformers | pipeline
                      (default: auto — VLM if GPU detected, else Pipeline)
  --force             Force regeneration even if output already exists
  --bookshelf DIR     Override bookshelf directory
  --output DIR        Override output directory
```

## Project Structure

```
avicenna/
├── avicenna/
│   ├── __init__.py        # Package init, version
│   ├── __main__.py        # python -m avicenna.cli entry
│   ├── cli.py             # Argument parsing, command dispatch
│   ├── config.py          # Dataclass configs, .env loading
│   ├── pipeline.py        # 4-stage orchestration
│   ├── extractor.py       # MinerU PDF extraction (VLM / Pipeline)
│   ├── filter.py          # Size + VLM semantic image filtering
│   ├── describer.py       # VLM image description generation
│   ├── vlm_client.py      # Qwen VL API wrapper (LangChain)
│   └── processor.py       # Markdown post-processing utilities
├── prompts/
│   ├── filter_image.txt   # Image classification prompt
│   └── describe_image.txt # Image description prompt
├── docs/
│   ├── CHANGELOG.md       # 工作记录
│   └── ROADMAP.md         # 开发计划
├── bookshelf/             # Input PDFs (git-ignored)
├── knowledge/             # Output Markdown + images (git-ignored)
├── .env                   # VLM API credentials (git-ignored)
├── .env.example           # Env template
└── pyproject.toml
```

## MinerU Backends

| Backend | Requires | Speed | Quality |
|---|---|---|---|
| `vlm-transformers` | CUDA GPU + torch | Fast | Higher (VLM-based layout understanding) |
| `pipeline` | CPU only | Slower | Good (traditional CV + OCR pipeline) |
| `auto` (default) | Either | — | Picks `vlm-transformers` if GPU available, else `pipeline` |

## Output Format

Each processed PDF produces `knowledge/{org}/{pdf_stem}/content.md`:

```markdown
---
name: LEVEL_2
source_pdf: LEVEL_2.pdf
organization: CASI
language: en
tags:
  - ski-instruction
  - certification
---

# Chapter Title

Body text extracted from PDF...

![Skier demonstrating wedge turn on gentle slope](images/img_001.jpg)

> **[Image: img_001.jpg]**
> A skier demonstrates a basic wedge turn on a gentle green slope,
> with arms forward and knees bent into a snowplow position.
```

## Dependencies

- **mineru** >= 2.7 — PDF extraction engine
- **langchain-openai** >= 1.1 — OpenAI-compatible VLM API client
- **langchain-core** >= 1.2 — LangChain messaging primitives
- **python-dotenv** >= 1.0 — Environment variable loading
- **loguru** >= 0.7 — Structured logging
- **Pillow** >= 10.0 — Image processing

## License

MIT
