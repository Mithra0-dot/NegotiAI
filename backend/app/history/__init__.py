"""Deliberately empty at package-init time — same circular-import
caution already applied in strategies/ and scoring/. Import what you
need directly: `from app.history.models import SessionRecord`,
`from app.history.schemas import SessionHistoryItem`,
`from app.history.repository import save_session, list_sessions`.
"""
