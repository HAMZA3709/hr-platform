"""
Métriques Prometheus du pipeline RH.

IMPORTANT — cardinalité : aucun label ne doit jamais porter candidate_id,
run_id, ou toute valeur à cardinalité non bornée. Les labels utilisés
(agent_name, status, llm_provider) ont un nombre de valeurs possibles fixe
et restreint.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

PIPELINE_RUNS_TOTAL = Counter(
    "hr_pipeline_runs_total", "Nombre total d'exécutions du pipeline", ["status"]
)
PIPELINE_DURATION = Histogram(
    "hr_pipeline_duration_seconds",
    "Durée totale d'une exécution du pipeline",
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60),
)

AGENT_EXECUTIONS_TOTAL = Counter(
    "hr_agent_executions_total", "Nombre d'exécutions par agent", ["agent_name", "status"]
)
AGENT_DURATION = Histogram(
    "hr_agent_duration_seconds",
    "Latence d'exécution par agent",
    ["agent_name"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)
AGENT_ERROR_TOTAL = Counter(
    "hr_agent_errors_total", "Nombre d'erreurs par agent", ["agent_name"]
)

LLM_TOKENS_TOTAL = Counter(
    "hr_llm_tokens_total", "Tokens LLM consommés", ["provider", "direction"]
)
LLM_COST_TOTAL = Counter(
    "hr_llm_cost_usd_total", "Coût LLM estimé cumulé en USD", ["provider"]
)
LLM_PROVIDER_CALLS_TOTAL = Counter(
    "hr_llm_provider_calls_total", "Appels LLM par provider", ["provider"]
)

QUEUE_DEPTH = Gauge("hr_pipeline_queue_depth", "Candidats en attente de traitement")

# Coût simulé/estimé par 1000 tokens, par provider (à ajuster selon tarif réel)
COST_PER_1K_TOKENS = {"anthropic": 0.003, "openai": 0.0006, "simulation": 0.0}


def record_agent_execution(
    agent_name: str, status: str, duration_s: float, tokens_in: int, tokens_out: int, llm_provider: str
) -> None:
    AGENT_EXECUTIONS_TOTAL.labels(agent_name=agent_name, status=status).inc()
    AGENT_DURATION.labels(agent_name=agent_name).observe(duration_s)
    if status == "error":
        AGENT_ERROR_TOTAL.labels(agent_name=agent_name).inc()

    LLM_TOKENS_TOTAL.labels(provider=llm_provider, direction="input").inc(tokens_in)
    LLM_TOKENS_TOTAL.labels(provider=llm_provider, direction="output").inc(tokens_out)
    LLM_PROVIDER_CALLS_TOTAL.labels(provider=llm_provider).inc()

    cost_rate = COST_PER_1K_TOKENS.get(llm_provider, 0.0)
    LLM_COST_TOTAL.labels(provider=llm_provider).inc((tokens_in + tokens_out) / 1000 * cost_rate)


def record_pipeline_run(status: str, duration_s: float) -> None:
    PIPELINE_RUNS_TOTAL.labels(status=status).inc()
    PIPELINE_DURATION.observe(duration_s)
