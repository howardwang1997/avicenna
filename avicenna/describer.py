"""VLM-powered image description generation."""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from avicenna.vlm_client import VLMClient


def _detect_language(pdf_name: str) -> str:
    """Heuristic language detection from filename."""
    lower = pdf_name.lower()
    if any(kw in lower for kw in ("chinese", "mandarin", "中文")):
        return "zh"
    return "en"


_LANG_LABELS = {
    "en": "English",
    "zh": "中文",
}


def describe_images(
    images_dir: Path,
    files: list[str],
    vlm_client: VLMClient,
    prompts_dir: Path,
    language: str = "en",
) -> dict[str, str]:
    """Generate VLM descriptions for each image.

    Returns:
        {filename: description_text}
    """
    prompt_template = (prompts_dir / "describe_image.txt").read_text(encoding="utf-8").strip()
    lang_label = _LANG_LABELS.get(language, "English")
    prompt = prompt_template.replace("{language}", lang_label)

    descriptions: dict[str, str] = {}

    for img_file in files:
        img_path = images_dir / img_file
        if not img_path.exists():
            continue

        logger.info("Describing image: {}", img_file)
        desc = vlm_client.call_on_image(img_path, prompt)
        descriptions[img_file] = desc.strip()

    logger.info("Described {}/{} images", len(descriptions), len(files))
    return descriptions
