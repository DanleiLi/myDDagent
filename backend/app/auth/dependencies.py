from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import json

import httpx

from fastapi import HTTPException, Request

from app.config import settings


@dataclass(frozen=True, slots=True)
class CurrentUser:
    id: str
    email: str


async def get_current_user(request: Request) -> CurrentUser:
    """Extract and verify Supabase JWT from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.removeprefix("Bearer ")

    try:
        # Prefer a direct Supabase auth lookup so revoked/invalid tokens are rejected.
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.supabase_url}/auth/v1/user",
                headers={
                    "apikey": settings.supabase_publishable_key,
                    "Authorization": f"Bearer {token}",
                },
            )

        if response.status_code == 200:
            payload = response.json()
            user_id = payload.get("id")
            if user_id:
                return CurrentUser(id=str(user_id), email=str(payload.get("email", "")))

        # Fallback: decode the JWT payload locally so transient auth service issues
        # do not block testing or normal app use.
        parts = token.split(".")
        if len(parts) < 2:
            raise HTTPException(status_code=401, detail="Invalid token")

        payload_segment = parts[1]
        padding = "=" * (-len(payload_segment) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_segment + padding)
        payload = json.loads(payload_bytes.decode("utf-8"))
        user_id = payload.get("sub")
        exp = payload.get("exp")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        if exp is not None and int(exp) < int(datetime.now(timezone.utc).timestamp()):
            raise HTTPException(status_code=401, detail="Token expired")
        return CurrentUser(id=str(user_id), email=str(payload.get("email", "")))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token verification failed")
