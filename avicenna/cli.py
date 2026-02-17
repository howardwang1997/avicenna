"""CLI entry point for avicenna."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger

from avicenna.config import AppConfig
from avicenna.pipeline import Pipeline


def _setup_logger() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}",
        level="INFO",
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="avicenna",
        description="PDF → Markdown preprocessing for ski instruction manuals",
    )
    sub = parser.add_subparsers(dest="command")

    # --- process ---
    proc = sub.add_parser("process", help="Convert PDFs to enriched Markdown")
    proc.add_argument("--pdf", type=str, default=None,
                       help="Path to a single PDF (relative to project root or absolute)")
    proc.add_argument("--force", action="store_true",
                       help="Force regeneration even if output exists")
    proc.add_argument("--bookshelf", type=str, default=None,
                       help="Override bookshelf directory")
    proc.add_argument("--output", type=str, default=None,
                       help="Override output directory")
    proc.add_argument("--backend", choices=["auto", "vlm-transformers", "pipeline"],
                       default="auto",
                       help="MinerU backend (default: auto — VLM if GPU, else Pipeline)")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    _setup_logger()

    if args.command == "process":
        config = AppConfig(force_regenerate=args.force)
        config.mineru.backend = args.backend
        if args.bookshelf:
            config.bookshelf_dir = Path(args.bookshelf).resolve()
        if args.output:
            config.output_dir = Path(args.output).resolve()

        pipeline = Pipeline(config)

        if args.pdf:
            pdf_path = Path(args.pdf)
            if not pdf_path.is_absolute():
                pdf_path = Path.cwd() / pdf_path
            pdf_path = pdf_path.resolve()
            if not pdf_path.exists():
                logger.error("PDF not found: {}", pdf_path)
                sys.exit(1)
            result = pipeline.process_single_pdf(pdf_path)
            if result.error:
                logger.error("Failed: {}", result.error)
                sys.exit(1)
            elif result.skipped:
                logger.info("Skipped (already processed). Use --force to regenerate.")
            else:
                logger.info("Done — {} images, {} words → {}",
                            result.image_count, result.word_count, result.md_path)
        else:
            results = pipeline.process_all()
            failed = [r for r in results if r.error]
            if failed:
                sys.exit(1)


if __name__ == "__main__":
    main()
