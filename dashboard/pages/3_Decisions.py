"""Page Décisions : consulter les décisions d'onboarding, filtrer par statut."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st
from components.api_client import get

st.set_page_config(page_title="Décisions", layout="wide")
st.title("Décisions d'onboarding")

decisions = get("/api/v1/decisions", params={"limit": 200})
if decisions:
    df = pd.DataFrame(decisions)

    ready_filter = st.selectbox("Filtrer", options=["Toutes", "Prêt uniquement", "Non prêt uniquement"])
    if ready_filter == "Prêt uniquement":
        df = df[df["ready"] == True]  # noqa: E712
    elif ready_filter == "Non prêt uniquement":
        df = df[df["ready"] == False]  # noqa: E712

    st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns(2)
    col1.metric("Total décisions", len(decisions))
    ready_count = sum(1 for d in decisions if d["ready"])
    col2.metric("Taux 'prêt'", f"{ready_count / len(decisions):.0%}" if decisions else "-")
else:
    st.info("Aucune décision pour l'instant.")
