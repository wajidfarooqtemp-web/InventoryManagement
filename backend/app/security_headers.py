"""
Production security headers on every response (Section 39). CSP is
deliberately strict - no inline scripts, nothing loaded from outside our
own origin. React's built output doesn't need inline scripts, so this
costs nothing in functionality.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"

        # HSTS only makes sense once actually served over HTTPS (Render/
        # Vercel are; local dev over http:// is not) - skipped outside
        # production so it never breaks local testing.
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response