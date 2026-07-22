from __future__ import annotations

import os
import time

from .base import DEFAULT_PROMPT_NAME, LLMJudge

MODEL_ID = "gemini-2.5-flash"


class GeminiJudge(LLMJudge):
    """API fallback for when no local GPU is available (project decision: open-source first,
    docs/decisions.md). Needs GEMINI_API_KEY in the environment — never hardcode the key.
    """

    def __init__(self, model_id: str = MODEL_ID, max_retries: int = 3, prompt_name: str = DEFAULT_PROMPT_NAME) -> None:
        super().__init__(prompt_name=prompt_name)
        import google.generativeai as genai

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set — export it before using --judge gemini.")
        genai.configure(api_key=api_key)
        self.name = f"llm-{model_id}-v1"
        self.max_retries = max_retries
        self._model = genai.GenerativeModel(model_id)

    def _generate(self, prompt: str) -> str:
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = self._model.generate_content(prompt)
                return (resp.text or "").strip()
            except Exception as exc:  # network hiccup / rate limit / safety block — retry with backoff
                last_error = exc
                print(f"  [gemini attempt {attempt + 1}/{self.max_retries}] {exc!r}")
                time.sleep(2**attempt)
        # repr(last_error), not just str() -- run_eval.py's except-block only prints str(exc) on
        # the RuntimeError raised here, and `raise ... from last_error` alone is invisible there
        # (it only shows up in a full traceback, which nothing prints). Folding the real cause
        # into this message is what actually reaches the console log and judge_cache.jsonl.
        raise RuntimeError(
            f"Gemini judge failed after {self.max_retries} attempts: {last_error!r}"
        ) from last_error
