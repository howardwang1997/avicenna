"""Pipeline orchestration — four-stage PDF→Markdown processing."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from loguru import logger

from avicenna.config import AppConfig
from avicenna.describer import _detect_language, describe_images
from avicenna.extractor import IMAGE_EXTENSIONS, VLM_PROCESSED_MARKER, extract_pdf
from avicenna.filter import filter_by_size, filter_by_vlm_semantics
from avicenna.processor import (
    add_frontmatter,
    get_image_placeholders,
    remove_image_placeholders,
    replace_placeholders_with_descriptions,
)
from avicenna.vlm_client import VLMClient


@dataclass
class ProcessingResult:
    """Result of processing a single PDF — serves as interface for downstream knowledge-base."""
    pdf_path: Path
    md_path: Optional[Path] = None
    images_dir: Optional[Path] = None
    language: str = "en"
    image_count: int = 0
    word_count: int = 0
    metadata: dict = field(default_factory=dict)
    error: Optional[str] = None
    skipped: bool = False


def _infer_organization(relative_path: str) -> str:
    """Guess source organization from directory name."""
    parts = Path(relative_path).parts
    if parts:
        first = parts[0].upper()
        if "CASI" in first:
            return "CASI"
        if "NZSBI" in first or "SBINZ" in first:
            return "SBINZ"
    return ""


def _infer_tags(pdf_stem: str, org: str) -> list[str]:
    tags: list[str] = []
    if org:
        tags.append(org.lower())
    tags.append("ski-instruction")
    lower = pdf_stem.lower().replace("_", " ").replace("-", " ")
    if "level" in lower or "l1" in lower or "l2" in lower or "l3" in lower or "l4" in lower:
        tags.append("certification")
    if "reference" in lower or "ref" in lower:
        tags.append("reference-guide")
    if "park" in lower:
        tags.append("terrain-park")
    if "kid" in lower or "child" in lower:
        tags.append("children")
    return tags


class Pipeline:
    """Four-stage PDF→Markdown processing pipeline."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig()
        self.vlm_client = VLMClient(self.config.vlm)

    def _is_already_processed(self, content_md: Path) -> bool:
        """Check if output already exists and contains VLM_PROCESSED marker."""
        if self.config.force_regenerate:
            return False
        if not content_md.exists():
            return False
        text = content_md.read_text(encoding="utf-8")
        return "<!-- VLM_PROCESSED -->" in text

    def process_single_pdf(self, pdf_path: Path) -> ProcessingResult:
        """Process one PDF through all four stages."""
        # Determine output directory
        try:
            relative = pdf_path.relative_to(self.config.bookshelf_dir)
        except ValueError:
            relative = Path(pdf_path.name)

        # If pdf is directly under bookshelf (no subdir), use stem as dir
        if len(relative.parts) == 1:
            output_subdir = relative.stem
        else:
            # e.g. CASI_GUIDE/simple_en.pdf → CASI_GUIDE/simple_en
            output_subdir = relative.parent / relative.stem

        out_dir = self.config.output_dir / output_subdir
        content_md = out_dir / "content.md"
        images_dir = out_dir / "images"

        # Adaptive skip
        if self._is_already_processed(content_md):
            logger.info("Skipping {} — already processed", pdf_path.name)
            return ProcessingResult(
                pdf_path=pdf_path,
                md_path=content_md,
                images_dir=images_dir,
                skipped=True,
            )

        logger.info("Processing: {}", pdf_path.name)
        out_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)

        # --- Stage 1: MinerU VLM-Transformer extraction ---
        logger.info("[Stage 1/4] MinerU extraction…")
        markdown, all_images, error = extract_pdf(
            pdf_path, images_dir, self.config.mineru,
        )
        if error:
            logger.error("Extraction failed for {}: {}", pdf_path.name, error)
            return ProcessingResult(pdf_path=pdf_path, error=error)

        # --- Stage 2: Size-based filtering ---
        logger.info("[Stage 2/4] Size filtering…")
        size_passed = filter_by_size(images_dir, all_images, self.config.filter)
        size_removed = [f for f in all_images if f not in set(size_passed)]

        # --- Stage 3: VLM semantic filtering ---
        logger.info("[Stage 3/4] VLM semantic filtering…")
        meaningful, semantic_removed = filter_by_vlm_semantics(
            images_dir, size_passed, self.vlm_client, self.config.prompts_dir,
        )
        all_removed = size_removed + semantic_removed

        # Remove placeholders for filtered-out images
        markdown = remove_image_placeholders(markdown, all_removed)

        # Delete removed image files
        for img_file in all_removed:
            img_path = images_dir / img_file
            if img_path.exists():
                img_path.unlink()
                logger.debug("Deleted: {}", img_file)

        # --- Stage 4: VLM description + Markdown processing ---
        logger.info("[Stage 4/4] VLM description + Markdown assembly…")
        language = _detect_language(pdf_path.stem)
        descriptions = describe_images(
            images_dir, meaningful, self.vlm_client,
            self.config.prompts_dir, language,
        )

        markdown = replace_placeholders_with_descriptions(markdown, descriptions)

        # Build metadata & frontmatter
        relative_pdf = str(relative)
        org = _infer_organization(relative_pdf)
        tags = _infer_tags(pdf_path.stem, org)
        metadata = {
            "name": pdf_path.stem,
            "source_pdf": relative_pdf,
            "source_organization": org,
            "language": language,
            "tags": tags,
        }
        markdown = add_frontmatter(markdown, metadata)

        # Append VLM_PROCESSED marker
        markdown = markdown + VLM_PROCESSED_MARKER

        # Write output
        content_md.write_text(markdown, encoding="utf-8")
        logger.info("Saved: {}", content_md)

        word_count = len(markdown.split())
        return ProcessingResult(
            pdf_path=pdf_path,
            md_path=content_md,
            images_dir=images_dir,
            language=language,
            image_count=len(meaningful),
            word_count=word_count,
            metadata=metadata,
        )

    def process_all(self) -> list[ProcessingResult]:
        """Process all PDFs under bookshelf_dir. Single-PDF failure does not block others."""
        results: list[ProcessingResult] = []
        bookshelf = self.config.bookshelf_dir

        if not bookshelf.exists():
            logger.error("Bookshelf directory not found: {}", bookshelf)
            return results

        pdf_files = sorted(bookshelf.rglob("*.pdf"))
        logger.info("Found {} PDFs in {}", len(pdf_files), bookshelf)

        for i, pdf_path in enumerate(pdf_files, 1):
            logger.info("--- [{}/{}] {} ---", i, len(pdf_files), pdf_path.name)
            try:
                result = self.process_single_pdf(pdf_path)
                results.append(result)
                if result.error:
                    logger.error("Failed: {} — {}", pdf_path.name, result.error)
                elif result.skipped:
                    logger.info("Skipped: {}", pdf_path.name)
                else:
                    logger.info(
                        "Done: {} — {} images, {} words",
                        pdf_path.name, result.image_count, result.word_count,
                    )
            except Exception as e:
                logger.error("Unexpected error processing {}: {}", pdf_path.name, e)
                results.append(ProcessingResult(pdf_path=pdf_path, error=str(e)))

        # Summary
        ok = sum(1 for r in results if not r.error and not r.skipped)
        skipped = sum(1 for r in results if r.skipped)
        failed = sum(1 for r in results if r.error)
        logger.info("Summary: {} processed, {} skipped, {} failed out of {} total",
                     ok, skipped, failed, len(results))
        return results
