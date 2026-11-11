"""Page Indicateurs : vue RH agrégée (taux de rétention, score moyen, etc.)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from components.api_client import get

st.set_page_config(page_title="Indicateurs RH", layout="wide")
st.title("Indicateurs RH")

runs = get("/api/v1/pipeline-runs", params={"limit": 500}) or []
decisions = get("/api/v1/decisions", params={"limit": 500}) or []

col1, col2, col3, col4 = st.columns(4)

total_runs = len(runs)
success_runs = sum(1 for r in runs if r["status"] == "success")
rejected_runs = sum(1 for r in runs if r["status"] == "rejected_at_screening")
error_runs = sum(1 for r in runs if r["status"] == "error")

col1.metric("Pipelines exécutés", total_runs)
col2.metric(
    "Taux de rétention (screening)",
    f"{(total_runs - rejected_runs) / total_runs:.0%}" if total_runs else "-",
)
col3.metric("Rejetés au tri", rejected_runs)
col4.metric("Erreurs", error_runs)

if decisions:
    ready_count = sum(1 for d in decisions if d["ready"])
    st.metric("Taux d'onboarding (prêt)", f"{ready_count / len(decisions):.0%}")

st.divider()
st.caption(
    "Ces indicateurs sont aussi disponibles en métriques Prometheus (endpoint /metrics de "
    "l'API) et documentés comme entités Metric dans OpenMetadata si l'intégration est activée."
)
