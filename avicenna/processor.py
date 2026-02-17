"""Markdown post-processing: placeholder handling and frontmatter."""

from __future__ import annotations

import os
import re
from typing import Any


def get_image_placeholders(md: str) -> list[str]:
    """Extract image filenames from markdown ![...](path/file) placeholders."""
    pattern = r"!\[[^\]]*\]\(([^)]+)\)"
    matches = re.findall(pattern, md)
    return [os.path.basename(m) for m in matches if os.path.basename(m)]


def remove_image_placeholders(md: str, removed_files: list[str]) -> str:
    """Remove entire lines containing placeholders for the given image files."""
    result = md
    for img_file in removed_files:
        pattern = rf"^.*!\[[^\]]*\]\([^)]*{re.escape(img_file)}\s*\).*$\n?"
        result = re.sub(pattern, "", result, flags=re.MULTILINE)
    return result


def replace_placeholders_with_descriptions(
    md: str,
    descriptions: dict[str, str],
) -> str:
    """Replace image placeholders with image ref + blockquote description.

    Output format preserves the image link and adds a descriptive blockquote:
        ![Figure description](images/filename.jpg)

        > **[Image: filename.jpg]**
        > {VLM description}
    """
    result = md
    for img_file, desc in descriptions.items():
        pattern = rf"!\[[^\]]*\]\([^)]*{re.escape(img_file)}\s*\)"
        replacement = (
            f"![{desc[:80]}](images/{img_file})\n\n"
            f"> **[Image: {img_file}]**\n"
            f"> {desc}"
        )
        result = re.sub(pattern, replacement, result)
    return result


def add_frontmatter(md: str, metadata: dict[str, Any]) -> str:
    """Prepend YAML frontmatter to markdown content."""
    lines = ["---"]
    for key, value in metadata.items():
        if isinstance(value, list):
            lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines) + md
