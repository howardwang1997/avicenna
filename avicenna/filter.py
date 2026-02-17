"""Two-stage image filtering: size/dimension then VLM semantic classification."""

from __future__ import annotations

import os
from pathlib import Path

from loguru import logger
from PIL import Image

from avicenna.config import FilterConfig
from avicenna.vlm_client import VLMClient


def filter_by_size(
    images_dir: Path,
    files: list[str],
    config: FilterConfig | None = None,
) -> list[str]:
    """Filter images by file size, pixel dimensions, and aspect ratio."""
    config = config or FilterConfig()
    kept: list[str] = []

    for img_file in files:
        img_path = images_dir / img_file
        if not img_path.exists():
            continue

        file_size_kb = img_path.stat().st_size / 1024
        if file_size_kb < config.min_file_size_kb:
            logger.debug("Skip {} — too small ({:.1f} KB)", img_file, file_size_kb)
            continue

        try:
            with Image.open(img_path) as img:
                w, h = img.size
                if w < config.min_dimension or h < config.min_dimension:
                    logger.debug("Skip {} — dimensions too small ({}x{})", img_file, w, h)
                    continue
                ratio = max(w, h) / max(min(w, h), 1)
                if ratio > config.max_aspect_ratio:
                    logger.debug("Skip {} — extreme aspect ratio ({:.1f})", img_file, ratio)
                    continue
        except Exception as e:
            logger.warning("Cannot read {}: {}", img_file, e)
            continue

        kept.append(img_file)

    logger.info("Size filter: {} → {} images", len(files), len(kept))
    return kept


def filter_by_vlm_semantics(
    images_dir: Path,
    files: list[str],
    vlm_client: VLMClient,
    prompts_dir: Path,
) -> tuple[list[str], list[str]]:
    """Use Qwen VL to classify images as MEANINGFUL or NOT_MEANINGFUL.

    Returns:
        (meaningful_files, removed_files)
    """
    prompt_path = prompts_dir / "filter_image.txt"
    prompt = prompt_path.read_text(encoding="utf-8").strip()

    meaningful: list[str] = []
    removed: list[str] = []

    for img_file in files:
        img_path = images_dir / img_file
        if not img_path.exists():
            continue

        try:
            response = vlm_client.call_on_image(img_path, prompt)
            response_upper = response.strip().upper()

            if "MEANINGFUL" in response_upper and "NOT" not in response_upper:
                meaningful.append(img_file)
                logger.info("Keep: {}", img_file)
            else:
                removed.append(img_file)
                logger.info("Remove: {}", img_file)
        except Exception as e:
            logger.warning("Error classifying {}: {} — keeping by default", img_file, e)
            meaningful.append(img_file)

    logger.info("VLM semantic filter: {} → {} meaningful, {} removed",
                len(files), len(meaningful), len(removed))
    return meaningful, removed
