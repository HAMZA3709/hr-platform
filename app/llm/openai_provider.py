"""Provider OpenAI."""

from __future__ import annotations

from app.llm.provider import LLMResult

DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str | None = None) -> None:
        import openai

        self._client = openai.OpenAI(api_key=api_key)
        self._model = model or DEFAULT_MODEL

    def generate(self, system: str, prompt: str, max_tokens: int = 500) -> LLMResult:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        text = response.choices[0].message.content or ""
        usage = response.usage
        tokens_in = usage.prompt_tokens if usage is not None else 0
        tokens_out = usage.completion_tokens if usage is not None else 0
        return LLMResult(
            text=text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            provider=self.name,
            model=self._model,
        )
