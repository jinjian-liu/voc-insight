from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from threading import Lock

from app.config import get_settings


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class RuntimeSession:
    operator_name: str
    api_key: str
    expires_at: datetime


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, RuntimeSession] = {}
        self._lock = Lock()

    def create(self, operator_name: str, api_key: str) -> tuple[str, RuntimeSession]:
        token = token_urlsafe(32)
        session = RuntimeSession(
            operator_name=operator_name,
            api_key=api_key,
            expires_at=utc_now() + timedelta(hours=get_settings().session_idle_hours),
        )
        with self._lock:
            self._purge_expired()
            self._sessions[token] = session
        return token, session

    def get(self, token: str | None) -> RuntimeSession | None:
        if not token:
            return None
        with self._lock:
            session = self._sessions.get(token)
            if session is None:
                return None
            if session.expires_at <= utc_now():
                self._sessions.pop(token, None)
                return None
            session.expires_at = utc_now() + timedelta(hours=get_settings().session_idle_hours)
            return session

    def delete(self, token: str | None) -> None:
        if not token:
            return
        with self._lock:
            self._sessions.pop(token, None)

    def _purge_expired(self) -> None:
        now = utc_now()
        expired = [token for token, item in self._sessions.items() if item.expires_at <= now]
        for token in expired:
            self._sessions.pop(token, None)


session_store = SessionStore()

