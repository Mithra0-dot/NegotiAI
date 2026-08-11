"""Deliberately empty at package-init time.

`strategies/models.py` (Phase, Tactic) has to stay importable without
pulling in `default.py`, since `personas/models.py` imports `Tactic` and
`default.py` in turn imports `PersonaInternal` from `personas/models.py`
— eagerly re-exporting `default`'s functions here would make that a real
circular import. Import what you need directly:
`from app.strategies.models import Phase, Tactic` or
`from app.strategies.default import phase_for_turn, select_tactic`.
"""
