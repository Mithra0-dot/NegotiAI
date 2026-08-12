"""Deliberately empty at package-init time — same lesson already learned
in strategies/__init__.py. scorer.py needs `ChatTurn` from app.schemas,
and schemas.py needs `SessionScore` from scoring.models; eagerly
re-exporting scorer's functions here would recreate that circular
import. Import what you need directly:
`from app.scoring.models import SessionScore, SessionOutcome`,
`from app.scoring.outcome_detection import check_session_end`,
`from app.scoring.scorer import compute_session_score`.
"""
