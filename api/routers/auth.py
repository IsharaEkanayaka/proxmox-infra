import secrets
import string
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from ..auth import (
    verify_password,
    generate_session_token,
    generate_api_key,
    hash_api_key,
    get_current_user,
    _extract_bearer_token,
)
from .. import config
from ..database import get_db
from ..errors import APIError
from ..models import LoginRequest, LoginResponse, UserDetail

router = APIRouter()


def _gen_id(prefix: str) -> str:
    chars = string.ascii_lowercase + string.digits
    return f"{prefix}_{''.join(secrets.choice(chars) for _ in range(8))}"


# ---------------------------------------------------------------------------
# GitHub OAuth
# ---------------------------------------------------------------------------

@router.get("/auth/github")
def github_login():
    """Return the GitHub OAuth authorization URL. Frontend redirects the user there."""
    if not config.GITHUB_CLIENT_ID:
        raise APIError("not_configured", "GitHub OAuth is not configured on this server", 501)
    params = urlencode({
        "client_id": config.GITHUB_CLIENT_ID,
        "redirect_uri": config.GITHUB_REDIRECT_URI,
        "scope": "read:user user:email read:org",
    })
    return {"url": f"https://github.com/login/oauth/authorize?{params}"}


@router.get("/auth/github/callback")
def github_callback(code: str):
    """
    GitHub redirects here after the user approves.
    Exchanges the code for an access token, fetches the GitHub user profile,
    then finds or auto-creates the kubesmith user and issues a session token.
    """
    if not config.GITHUB_CLIENT_ID:
        raise APIError("not_configured", "GitHub OAuth is not configured on this server", 501)

    # 1. Exchange code for GitHub access token
    with httpx.Client() as client:
        token_res = client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": config.GITHUB_CLIENT_ID,
                "client_secret": config.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
    if token_res.status_code != 200:
        raise APIError("github_error", "Failed to exchange GitHub code for token", 502)
    token_data = token_res.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise APIError("github_error", token_data.get("error_description", "No access token returned"), 502)

    # 2. Fetch GitHub user profile
    with httpx.Client() as client:
        user_res = client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
    if user_res.status_code != 200:
        raise APIError("github_error", "Failed to fetch GitHub user profile", 502)
    gh = user_res.json()
    github_id = str(gh["id"])
    github_username = gh["login"]
    display_name = gh.get("name") or github_username

    # 3. Check org membership (if configured)
    if config.GITHUB_ORG:
        with httpx.Client() as client:
            org_res = client.get(
                f"https://api.github.com/orgs/{config.GITHUB_ORG}/members/{github_username}",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
        # 204 = member, anything else = not a member
        if org_res.status_code != 204:
            return RedirectResponse(
                url=f"{config.FRONTEND_URL}/?auth_error=not_org_member"
            )

    # 4. Find or create kubesmith user
    db = get_db()
    try:
        user = db.execute(
            "SELECT * FROM users WHERE github_id=? AND is_active=1", (github_id,)
        ).fetchone()

        if not user:
            # Auto-create as viewer — an admin can promote later
            user_id = _gen_id("usr")
            raw_key = generate_api_key()
            key_hash = hash_api_key(raw_key)
            now = datetime.now(timezone.utc).isoformat()
            db.execute(
                "INSERT INTO users (id, username, name, role, api_key, is_active, created_at, github_id, github_username) "
                "VALUES (?, ?, ?, 'viewer', ?, 1, ?, ?, ?)",
                (user_id, github_username, display_name, key_hash, now, github_id, github_username),
            )
            db.commit()
            user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

        # 4. Create session
        session_token = generate_session_token()
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
            (session_token, user["id"], now),
        )
        db.commit()
    finally:
        db.close()

    # 5. Redirect to frontend with token in query param
    return RedirectResponse(url=f"{config.FRONTEND_URL}/?token={session_token}")


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
