"""
Provider Groq.

L'API Groq est compatible avec le format OpenAI — on réutilise donc le SDK
`openai`, simplement pointé vers l'endpoint de Groq. Groq propose un tier
gratuit avec des limites généreuses.

Clé API : https://console.groq.com/keys
"""

from __future__ import annotations

from app.llm.provider import LLMResult

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.3-70b-versatile"


class GroqProvider:
    name = "groq"

    def __init__(self, api_key: str, model: str | None = None) -> None:
        import openai

        self._client = openai.OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
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