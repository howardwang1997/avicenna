"""MinerU PDF extraction with configurable backend."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from loguru import logger

from avicenna.config import MinerUConfig

VLM_PROCESSED_MARKER = "\n\n<!-- VLM_PROCESSED -->"

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")


def _has_gpu() -> bool:
    """Check whether a CUDA GPU is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def _collect_images(output_images_dir: Path) -> list[str]:
    """Return sorted list of extracted image filenames."""
    return sorted(
        f
        for f in os.listdir(output_images_dir)
        if f.lower().endswith(IMAGE_EXTENSIONS)
    )


def _extract_vlm(pdf_bytes: bytes, output_images_dir: Path) -> str:
    """Run the VLM-transformer backend (requires GPU)."""
    from mineru.backend.vlm.vlm_analyze import doc_analyze as vlm_doc_analyze
    from mineru.backend.vlm.vlm_middle_json_mkcontent import union_make as vlm_union_make
    from mineru.data.data_reader_writer import FileBasedDataWriter
    from mineru.utils.enum_class import MakeMode

    image_writer = FileBasedDataWriter(str(output_images_dir))

    logger.info("[MinerU] Running VLM-transformer backend…")
    middle_json, _infer_result = vlm_doc_analyze(
        pdf_bytes,
        image_writer=image_writer,
        backend="transformers",
    )
    logger.info("[MinerU] VLM extraction complete")

    pdf_info = middle_json.get("pdf_info", {})
    return vlm_union_make(pdf_info, MakeMode.MM_MD, "images")


def _extract_pipeline(pdf_bytes: bytes, output_images_dir: Path, language: str) -> str:
    """Run the pipeline backend (CPU-friendly)."""
    from mineru.backend.pipeline.pipeline_analyze import doc_analyze as pipeline_doc_analyze
    from mineru.backend.pipeline.pipeline_middle_json_mkcontent import union_make as pipeline_union_make
    from mineru.backend.pipeline.model_json_to_middle_json import result_to_middle_json as pipeline_result_to_middle_json
    from mineru.data.data_reader_writer import FileBasedDataWriter
    from mineru.utils.enum_class import MakeMode

    logger.info("[MinerU] Running pipeline backend…")
    infer_results, all_image_lists, all_pdf_docs, lang_list, ocr_enabled_list = pipeline_doc_analyze(
        [pdf_bytes], [language], parse_method="auto", formula_enable=True, table_enable=True
    )

    image_writer = FileBasedDataWriter(str(output_images_dir))
    middle_json = pipeline_result_to_middle_json(
        infer_results[0], all_image_lists[0], all_pdf_docs[0],
        image_writer, lang_list[0], ocr_enabled_list[0], True
    )
    logger.info("[MinerU] Pipeline extraction complete")

    return pipeline_union_make(middle_json["pdf_info"], MakeMode.MM_MD, "images")


def extract_pdf(
    pdf_path: Path,
    output_images_dir: Path,
    config: MinerUConfig | None = None,
) -> tuple[str, list[str], Optional[str]]:
    """Run MinerU on a single PDF using the configured backend.

    Returns:
        (markdown_content, image_filenames, error_or_none)
    """
    config = config or MinerUConfig()
    logger.info("Extracting PDF: {}", pdf_path.name)

    # Resolve backend
    backend = config.backend
    if backend == "auto":
        backend = "vlm-transformers" if _has_gpu() else "pipeline"
        logger.info("[MinerU] Auto-detected backend: {}", backend)
    else:
        logger.info("[MinerU] Using backend: {}", backend)

    try:
        pdf_bytes = pdf_path.read_bytes()
        output_images_dir.mkdir(parents=True, exist_ok=True)

        if backend == "vlm-transformers":
            markdown_content = _extract_vlm(pdf_bytes, output_images_dir)
        else:
            markdown_content = _extract_pipeline(pdf_bytes, output_images_dir, config.language)

        logger.info("[MinerU] Markdown length: {} chars", len(markdown_content))

        all_images = _collect_images(output_images_dir)
        logger.info("[MinerU] Extracted {} images", len(all_images))

        return markdown_content, all_images, None

    except Exception as e:
        import traceback
        error_msg = f"MinerU extraction failed: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return "", [], error_msg
