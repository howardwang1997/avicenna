"""Configuration management — loads VLM keys from local .env."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# ---------------------------------------------------------------------------
# .env loading: local .env  →  environment
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOCAL_ENV = _PROJECT_ROOT / ".env"

if _LOCAL_ENV.exists():
    load_dotenv(_LOCAL_ENV, override=False)
    logger.info("Loaded local .env: {}", _LOCAL_ENV)


# ---------------------------------------------------------------------------
# Data-classes
# ---------------------------------------------------------------------------

@dataclass
class VLMConfig:
    model_name: str = field(default_factory=lambda: os.getenv("VLM_MODEL_NAME", "qwen-vl-plus"))
    base_url: str = field(default_factory=lambda: os.getenv("VLM_BASE_URL", ""))
    api_key: str = field(default_factory=lambda: os.getenv("VLM_API_KEY", os.getenv("QWEN_API_KEY", "")))
    temperature: float = 0.1
    max_retries: int = 3


@dataclass
class MinerUConfig:
    backend: str = "auto"
    language: str = "en"


@dataclass
class FilterConfig:
    min_file_size_kb: int = 10
    min_dimension: int = 100
    max_aspect_ratio: float = 10.0


@dataclass
class AppConfig:
    vlm: VLMConfig = field(default_factory=VLMConfig)
    mineru: MinerUConfig = field(default_factory=MinerUConfig)
    filter: FilterConfig = field(default_factory=FilterConfig)
    bookshelf_dir: Path = field(default_factory=lambda: _PROJECT_ROOT / "bookshelf")
    output_dir: Path = field(default_factory=lambda: _PROJECT_ROOT / "knowledge")
    prompts_dir: Path = field(default_factory=lambda: _PROJECT_ROOT / "prompts")
    force_regenerate: bool = False
