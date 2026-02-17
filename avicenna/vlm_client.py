"""Qwen VL API client via LangChain OpenAI-compatible interface."""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path

from loguru import logger

from avicenna.config import VLMConfig

_MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}


class VLMClient:
    """Thin wrapper around Qwen VL with retry logic."""

    def __init__(self, config: VLMConfig) -> None:
        self._config = config
        self._llm = None  # lazy init

    def _get_llm(self):
        if self._llm is None:
            from langchain_openai import ChatOpenAI

            self._llm = ChatOpenAI(
                model=self._config.model_name,
                base_url=self._config.base_url,
                api_key=self._config.api_key,
                temperature=self._config.temperature,
            )
        return self._llm

    def call_on_image(self, image_path: str | Path, prompt: str) -> str:
        """Call VLM on a single image. Returns response text or error string."""
        if not self._config.api_key:
            return "[VLM not configured: set VLM_API_KEY or QWEN_API_KEY]"

        image_path = Path(image_path)
        img_bytes = image_path.read_bytes()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        ext = image_path.suffix.lower()
        mime = _MIME_MAP.get(ext, "image/jpeg")

        from langchain_core.messages import HumanMessage

        message = HumanMessage(
            content=[
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{img_b64}"},
                },
                {"type": "text", "text": prompt},
            ]
        )

        last_err: Exception | None = None
        for attempt in range(1, self._config.max_retries + 1):
            try:
                response = self._get_llm().invoke([message])
                return response.content.strip()
            except Exception as e:
                last_err = e
                wait = 2**attempt
                logger.warning(
                    "VLM attempt {}/{} failed for {}: {}. Retrying in {}s…",
                    attempt, self._config.max_retries, image_path.name, e, wait,
                )
                time.sleep(wait)

        return f"[VLM error after {self._config.max_retries} retries: {last_err}]"
