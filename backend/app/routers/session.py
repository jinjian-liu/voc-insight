from fastapi import APIRouter, Cookie, Depends, Response

from app.dependencies import require_runtime_session
from app.schemas import SessionCreate, SessionView
from app.session_store import RuntimeSession, session_store


router = APIRouter(prefix="/session", tags=["session"])


@router.post("", response_model=SessionView)
def create_session(payload: SessionCreate, response: Response) -> SessionView:
    token, session = session_store.create(payload.operator_name, payload.api_key)
    response.set_cookie(
        key="voc_session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return SessionView(ready=True, operator_name=session.operator_name, expires_at=session.expires_at)


@router.get("", response_model=SessionView)
def get_session(session: RuntimeSession = Depends(require_runtime_session)) -> SessionView:
    return SessionView(ready=True, operator_name=session.operator_name, expires_at=session.expires_at)


@router.delete("", status_code=204)
def delete_session(response: Response, voc_session: str | None = Cookie(default=None)) -> None:
    session_store.delete(voc_session)
    response.delete_cookie("voc_session")
