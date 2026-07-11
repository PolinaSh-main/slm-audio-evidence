from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SpeechQAModel(ABC):
    """Common interface: give a wav path and a question, get the model's text answer."""

    name: str = "base"

    @abstractmethod
    def answer(
        self,
        audio_path: str,
        question: str,
        prompt_template: str,
        gen_kwargs: dict[str, Any] | None = None,
    ) -> str:
        """prompt_template contains '{question}'; implementations fill it and query the model."""


def render_prompt(prompt_template: str, question: str) -> str:
    return prompt_template.replace("{question}", question)
