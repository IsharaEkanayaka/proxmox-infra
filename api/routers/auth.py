from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request

from ..auth import (
    verify_password,
    generate_session_token,
    get_current_user,
    _extract_bearer_token,
)
from ..database import get_db
from ..errors import APIError
from ..models import LoginRequest, LoginResponse, UserDetail

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest):
    db = get_db()
    try:
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND is_active=1", (req.username,)
        ).fetchone()
        if not user or not user["password_hash"]:
            raise APIError("unauthorized", "invalid username or password", 401)
        if not verify_password(req.password, user["password_hash"]):
            raise APIError("unauthorized", "invalid username or password", 401)

        token = generate_session_token()
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?,?,?)",
            (token, user["id"], now),
        )
        db.commit()

        return LoginResponse(
            token=token,
            user=UserDetail(
                id=user["id"], username=user["username"], name=user["name"],
                role=user["role"], is_active=bool(user["is_active"]),
                created_at=user["created_at"],
            ),
        )
    finally:
        db.close()


@router.post("/auth/logout", status_code=204)
def logout(request: Request):
    try:
        token = _extract_bearer_token(request)
    except APIError:
        return
    db = get_db()
    try:
        db.execute("DELETE FROM sessions WHERE token=?", (token,))
        db.commit()
    finally:
        db.close()
