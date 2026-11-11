"""Tests de pseudonymisation (app.audit.pseudonymize)."""

from __future__ import annotations

from app.audit.pseudonymize import pseudonymize


def test_pseudonymize_is_deterministic():
    assert pseudonymize("cand-001") == pseudonymize("cand-001")


def test_pseudonymize_differs_between_candidates():
    assert pseudonymize("cand-001") != pseudonymize("cand-002")


def test_pseudonymize_does_not_contain_original_value():
    original = "jean.dupont@example.com"
    hashed = pseudonymize(original)
    assert original not in hashed
    assert "jean" not in hashed.lower()


def test_pseudonymize_output_is_fixed_length_hex():
    hashed = pseudonymize("cand-001")
    assert len(hashed) == 20
    int(hashed, 16)  # lève ValueError si ce n'est pas de l'hex valide
