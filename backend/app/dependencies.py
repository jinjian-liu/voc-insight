from fastapi import Cookie, HTTPException, status

from app.session_store import RuntimeSession, session_store


def require_runtime_session(voc_session: str | None = Cookie(default=None)) -> RuntimeSession:
    session = session_store.get(voc_session)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="当前会话未初始化或已过期",
        )
    return session

