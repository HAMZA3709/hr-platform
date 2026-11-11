"""Page Pipeline : consulter les exécutions et leur détail (étapes, erreurs)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st
from components.api_client import get

st.set_page_config(page_title="Pipeline", layout="wide")
st.title("Exécutions du pipeline")

runs = get("/api/v1/pipeline-runs", params={"limit": 100})
if runs:
    df = pd.DataFrame(runs)

    status_filter = st.multiselect(
        "Filtrer par statut", options=sorted(df["status"].unique()), default=list(df["status"].unique())
    )
    df = df[df["status"].isin(status_filter)]

    st.dataframe(df, use_container_width=True)

    st.subheader("Détail d'une exécution")
    run_id = st.text_input("run_id")
    if run_id:
        run = get(f"/api/v1/pipeline-runs/{run_id}")
        if run:
            st.json(run)
else:
    st.info("Aucune exécution de pipeline pour l'instant.")
