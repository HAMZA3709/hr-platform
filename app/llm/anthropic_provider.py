"""Provider Anthropic (Claude)."""

from __future__ import annotations

from app.llm.provider import LLMResult

DEFAULT_MODEL = "claude-sonnet-5"


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str | None = None) -> None:
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model or DEFAULT_MODEL

    def generate(self, system: str, prompt: str, max_tokens: int = 500) -> LLMResult:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        return LLMResult(
            text=text,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            provider=self.name,
            model=self._model,
        )
