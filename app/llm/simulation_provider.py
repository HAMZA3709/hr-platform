"""Provider de simulation : aucune clé API, latence/texte déterministes-aléatoires.

Utilisé par défaut (LLM_PROVIDER=none) et automatiquement en repli si un
provider réel échoue ou n'est pas configurable.
"""

from __future__ import annotations

import random
import time

from app.llm.provider import LLMResult


class SimulationProvider:
    name = "simulation"

    def generate(self, system: str, prompt: str, max_tokens: int = 500) -> LLMResult:
        time.sleep(random.uniform(0.05, 0.2))
        text = (
            "[Texte généré par simulation locale — aucun LLM réel appelé] "
            "Résumé indicatif basé sur les règles métier appliquées."
        )
        return LLMResult(
            text=text,
            tokens_in=random.randint(150, 600),
            tokens_out=random.randint(50, 300),
            provider=self.name,
            model="simulation-v1",
        )
