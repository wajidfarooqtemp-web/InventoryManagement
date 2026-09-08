"""
Catches anything unexpected before it reaches the client, so a database
error or bug never leaks a stack trace, file path, or internal detail
(Section 38). Full detail still goes to the server log for real debugging.
"""
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("inventory-system")


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Something went wrong. Please try again."})