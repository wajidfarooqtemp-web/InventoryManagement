"""
Answers one question for every incoming request: "who is this, really?"

Flow:
  1. Frontend sends  Authorization: Bearer <supabase-jwt>
  2. We verify the token's SIGNATURE ourselves before trusting anything
     inside it. Modern Supabase projects sign tokens asymmetrically
     (ES256) rather than with a shared secret (the old HS256 scheme) -
     so instead of checking against a secret we already have, we fetch
     Supabase's PUBLIC signing keys (JWKS) and verify against those.
     PyJWKClient handles fetching + caching those keys for us.
  3. We then look up that user's CURRENT role/active status in OUR OWN
     users table - never from the token itself, because an admin may have
     changed someone's role or deactivated them since the token was issued,
     and the old token would still say the old role otherwise.
"""
import jwt
from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.database import get_pool

bearer_scheme = HTTPBearer()

# Supabase publishes its current public signing keys at this fixed URL.
# PyJWKClient fetches and caches them, and automatically picks the right
# key based on the "kid" header on each incoming token - so key rotation
# on Supabase's side doesn't require any change here.
_JWKS_URL = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
_jwks_client = jwt.PyJWKClient(_JWKS_URL)


@dataclass
class CurrentUser:
    id: str
    email: str
    name: str
    role: str


def _decode_token(token: str) -> dict:
    """Raises 401 on any tampering, wrong signature, wrong key, or expiry."""
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],  # current Supabase default
            audience="authenticated",  # Supabase sets this on every login token
        )
    except jwt.PyJWKClientError:
        # Couldn't reach Supabase's JWKS endpoint, or no matching key found.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify session. Please try again.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again.",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    payload = _decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session token.")

    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "select id, email, name, role, active from public.users where id = $1",
            user_id,
        )

    if row is None:
        raise HTTPException(status_code=401, detail="Account not recognized.")
    if not row["active"]:
        raise HTTPException(status_code=403, detail="This account has been deactivated.")

    return CurrentUser(id=str(row["id"]), email=row["email"], name=row["name"], role=row["role"])