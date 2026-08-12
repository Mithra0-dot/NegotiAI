"""Deliberately empty at package-init time — same circular-import
caution already applied in app/strategies/, app/scoring/, app/history/.
Import what you need directly: `from eval.user_types import UserType`,
`from eval.run_simulation import run_simulated_session, run_n_sessions`,
`from eval.repository import save_simulated_session, list_simulated_sessions`.
"""
