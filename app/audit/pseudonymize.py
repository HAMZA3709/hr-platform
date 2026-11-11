"""Pseudonymisation des identifiants candidats pour l'audit RGPD."""

from __future__ import annotations

import hashlib

from app.core.config import get_settings


def pseudonymize(candidate_ref: str) -> str:
    """Hash SHA-256 salé, tronqué à 20 caractères hex.

    Le sel vient de AUDIT_PSEUDONYMIZATION_SALT (.env) — sans lui, retrouver
    le candidat_ref d'origine à partir du hash n'est pas praticable, mais le
    même candidat produit toujours le même pseudonyme (permet de recouper des
    événements liés sans exposer l'identité en clair dans les logs).
    """
    settings = get_settings()
    salted = f"{settings.audit_pseudonymization_salt}:{candidate_ref}"
    return hashlib.sha256(salted.encode("utf-8")).hexdigest()[:20]
