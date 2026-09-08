from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"
    # Allow both local development and the production Vercel frontend.
    allowed_origins: str = "http://localhost:5173,https://kanihomeinventory.vercel.app"

    # Added in Phase 2 - needed to talk to Supabase and verify login tokens.
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    database_url: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"  # .env also holds test-only vars (Phase 13) that
                           # conftest.py reads directly via os.environ -
                           # Settings doesn't need to know about those.

settings = Settings()