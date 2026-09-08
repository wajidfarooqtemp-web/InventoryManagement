from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"
    allowed_origins: str = "http://localhost:5173"

    # Added in Phase 2 - needed to talk to Supabase and verify login tokens.
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    database_url: str = ""

    class Config:
        env_file = ".env"

settings = Settings()