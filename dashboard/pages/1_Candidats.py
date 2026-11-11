"""Page Candidats : ajouter un candidat, consulter la liste, filtrer."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st
from components.api_client import get, post

st.set_page_config(page_title="Candidats", layout="wide")
st.title("Candidats")

with st.form("new_candidate_form"):
    st.subheader("Ajouter un candidat")
    candidate_ref = st.text_input("Référence candidat (unique)", placeholder="cand-2026-001")
    years_experience = st.number_input("Années d'expérience", min_value=0, max_value=50, value=2)
    skills_raw = st.text_input("Compétences (séparées par des virgules)", placeholder="python, sql, leadership")
    education_level = st.text_input("Niveau d'études (optionnel)", placeholder="Master")
    submitted = st.form_submit_button("Ajouter le candidat")

    if submitted:
        if not candidate_ref.strip():
            st.warning("La référence candidat est requise.")
        else:
            skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
            result = post(
                "/api/v1/candidates",
                json={
                    "candidate_ref": candidate_ref.strip(),
                    "years_experience": int(years_experience),
                    "skills": skills,
                    "education_level": education_level.strip() or None,
                },
            )
            if result is not None:
                st.success(f"Candidat créé (id={result['id']}).")
                st.rerun()

st.divider()
st.subheader("Liste des candidats")

filter_ref = st.text_input("Filtrer par référence (contient)", key="filter_ref")

candidates = get("/api/v1/candidates", params={"limit": 100})
if candidates:
    df = pd.DataFrame(candidates)
    df["skills"] = df["skills"].apply(lambda s: ", ".join(s))
    if filter_ref:
        df = df[df["candidate_ref"].str.contains(filter_ref, case=False, na=False)]
    st.dataframe(df, use_container_width=True)

    st.subheader("Lancer le pipeline pour un candidat")
    candidate_id = st.number_input("ID du candidat", min_value=1, step=1)
    if st.button("Lancer le pipeline"):
        run = post(f"/api/v1/candidates/{int(candidate_id)}/run-pipeline")
        if run is not None:
            st.success(f"Pipeline lancé : run_id={run['run_id']}, statut={run['status']}")
else:
    st.info("Aucun candidat pour l'instant.")
