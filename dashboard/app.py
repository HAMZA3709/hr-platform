"""Page d'accueil : état des services (API, base de données, OpenMetadata)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from components.api_client import get

st.set_page_config(page_title="Pipeline RH — Accueil", layout="wide")
st.title("Pipeline RH multi-agents — Tableau de bord")

st.markdown(
    "Interface RH pour soumettre des candidats, suivre le pipeline, et "
    "consulter les décisions. Cette interface communique uniquement avec "
    "l'API FastAPI (jamais directement avec la base de données)."
)

st.subheader("État des services")
col1, col2, col3 = st.columns(3)

with col1:
    health = get("/health")
    if health and health.get("status") == "ok":
        st.success("API : opérationnelle")
    else:
        st.error("API : injoignable")

with col2:
    db_health = get("/health/database")
    if db_health and db_health.get("status") == "ok":
        st.success("Base de données : opérationnelle")
    else:
        st.error(f"Base de données : {db_health}")

with col3:
    om_health = get("/health/openmetadata")
    if om_health is None:
        st.warning("OpenMetadata : statut inconnu")
    elif om_health.get("status") == "ok":
        st.success("OpenMetadata : opérationnel")
    elif om_health.get("status") == "disabled":
        st.info("OpenMetadata : désactivé (OPENMETADATA_ENABLED=false)")
    else:
        st.error(f"OpenMetadata : {om_health}")

st.divider()
st.markdown(
    "Utilisez le menu à gauche pour : **Candidats** (ajouter/consulter), "
    "**Pipeline** (lancer/suivre une exécution), **Décisions** (consulter les "
    "décisions d'onboarding), **Indicateurs** (vue RH agrégée)."
)
