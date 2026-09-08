from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_db, disconnect_db
from app.routers import profile, locations, categories, inventory, movements

app = FastAPI(title="Inventory System API")

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


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment}