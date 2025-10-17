import re
import time
from typing import Optional

import bcrypt
import jwt
from flask import request, g
from .config import get_config

PUBLIC_PATHS = [
    r"^/$",
    r"^/_ping$",
    r"^/docs.*$",
    r"^/static/.*$",
    r"^/auth/register$",
    r"^/auth/login$",
]

_cfg = get_config()


def _is_public(path: str) -> bool:
    for p in PUBLIC_PATHS:
        if re.match(p, path):
            return True
    return False


# PUBLIC_INTERFACE
def create_password_hash(password: str) -> bytes:
    """Create bcrypt hash for a password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt)


# PUBLIC_INTERFACE
def verify_password(password: str, password_hash: bytes) -> bool:
    """Verify password with bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash)
    except Exception:
        return False


# PUBLIC_INTERFACE
def create_jwt_token(user_id: int, email: str, ttl_seconds: int = 60 * 60 * 24) -> str:
    """Create a signed JWT for the given user."""
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl_seconds,
    }
    return jwt.encode(payload, _cfg.JWT_SECRET, algorithm="HS256")


# PUBLIC_INTERFACE
def parse_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    """Extract bearer token from Authorization header."""
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


# PUBLIC_INTERFACE
def decode_jwt_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token, returning payload or None."""
    try:
        payload = jwt.decode(token, _cfg.JWT_SECRET, algorithms=["HS256"])
        return payload
    except Exception:
        return None


def jwt_required_middleware():
    """Per-request middleware to populate g.user for protected routes."""
    path = request.path
    if _is_public(path):
        return
    token = parse_bearer_token(request.headers.get("Authorization"))
    if not token:
        g.user = None
        return
    payload = decode_jwt_token(token)
    if not payload:
        g.user = None
        return
    g.user = {"id": int(payload.get("sub", 0)), "email": payload.get("email")}
