"""Interface commune à tous les providers LLM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMResult:
    text: str
    tokens_in: int
    tokens_out: int
    provider: str
    model: str


class LLMProvider(Protocol):
    name: str

    def generate(self, system: str, prompt: str, max_tokens: int = 500) -> LLMResult: ...
