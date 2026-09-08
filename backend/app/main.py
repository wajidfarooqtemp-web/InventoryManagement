from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.config import settings
from app.database import connect_db, disconnect_db
from app.rate_limit import limiter
from app.security_headers import SecurityHeadersMiddleware
from app.error_handlers import unhandled_exception_handler
from app.routers import profile, locations, categories, inventory, movements, periods, activity, purchase, overview, users, data_confirmation

app = FastAPI(title="Inventory System API")

# Rate limiting (Section 37)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Security headers (Section 39) and generic error handling (Section 38)
app.add_middleware(SecurityHeadersMiddleware)
app.add_exception_handler(Exception, unhandled_exception_handler)

origins = [o.strip() for o in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Open the DB pool once when the server starts, close it once when it stops -
# rather than connecting/disconnecting on every single request.
@app.on_event("startup")
async def on_startup():
    await connect_db()


@app.on_event("shutdown")
async def on_shutdown():
    await disconnect_db()


app.include_router(profile.router)
app.include_router(locations.router)
app.include_router(categories.router)
app.include_router(inventory.router)
app.include_router(movements.router)
app.include_router(periods.router)
app.include_router(activity.router)
app.include_router(purchase.router)
app.include_router(overview.router)
app.include_router(users.router)
app.include_router(data_confirmation.router)

@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment}