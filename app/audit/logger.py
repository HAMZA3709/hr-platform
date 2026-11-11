"""
Logger d'audit structuré (JSON via structlog), et persistance en base
(table audit_events).

Interdits stricts, jamais loggés ni persistés ici :
nom complet, adresse, téléphone, email, contenu complet du CV, clés API,
tokens d'authentification. Seuls les NOMS de champs utilisés pour une
décision sont journalisés (`fields_used`), jamais leurs valeurs.
"""

from __future__ import annotations

import logging
import sys

import structlog
from sqlalchemy.orm import Session

from app.audit.pseudonymize import pseudonymize
from app.db.models import AuditEvent

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.EventRenamer("message"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    _configured = True


def get_audit_logger():
    _configure()
    return structlog.get_logger("hr_audit")


def log_and_persist_decision(
    db: Session,
    candidate_ref: str,
    action: str,
    agent: str | None,
    decision: str | None,
    justification: str | None,
    rules_applied: list[str],
    fields_used: list[str],
    correlation_id: str | None = None,
    run_id: str | None = None,
) -> None:
    """Journalise (stdout JSON) ET persiste (table audit_events) un événement d'audit."""
    pseudo_ref = pseudonymize(candidate_ref)

    get_audit_logger().info(
        action,
        pseudonymized_ref=pseudo_ref,
        agent=agent,
        decision=decision,
        justification=justification,
        rules_applied=rules_applied,
        fields_used=fields_used,
        correlation_id=correlation_id,
        run_id=run_id,
    )

    db.add(
        AuditEvent(
            pseudonymized_ref=pseudo_ref,
            action=action,
            agent=agent,
            decision=decision,
            justification=justification,
            rules_applied=rules_applied,
            fields_used=fields_used,
            correlation_id=correlation_id,
            run_id=run_id,
        )
    )
    db.commit()
