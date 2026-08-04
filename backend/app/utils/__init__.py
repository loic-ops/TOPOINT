import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta

from app.config import settings


def generate_salt() -> str:
    return secrets.token_hex(16)


def hash_pin(pin: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode(),
        salt.encode(),
        iterations=100_000,
    ).hex()


def create_session_token(employee_id: int) -> str:
    payload = f"{employee_id}:{int(time.time())}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}:{signature}"


def verify_session_token(token: str) -> int | None:
    try:
        parts = token.rsplit(":", 1)
        if len(parts) != 2:
            return None
        payload, signature = parts
        expected = hmac.new(
            settings.SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        emp_id_str, ts_str = payload.split(":", 1)
        ts = int(ts_str)
        if time.time() - ts > settings.TOKEN_EXPIRE_MINUTES * 60:
            return None
        return int(emp_id_str)
    except (ValueError, IndexError):
        return None
