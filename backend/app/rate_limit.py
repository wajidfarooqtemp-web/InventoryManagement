"""
Rate limiting for sensitive/stock-changing endpoints (Section 37).
Keyed by IP address. Note: our own backend has no login endpoint - the
frontend talks to Supabase Auth directly for login, and Supabase Auth
already enforces its own rate limits on login attempts server-side. This
file only protects OUR endpoints: uploads and stock-changing actions.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)