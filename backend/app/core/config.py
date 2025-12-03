from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Infrastructure Management System"
    MONGODB_URL: str = "mongodb://mongo:27017"
    DATABASE_NAME: str = "gis_db"
    REDIS_URL: str = "redis://redis:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ADMIN_JWT_SECRET: str = "change-me"
    ADMIN_JWT_ALGORITHM: str = "HS256"
    ADMIN_JWT_EXPIRE_MINUTES: int = 60 * 24
    ADMIN_DEFAULT_USERNAME: str = "admin"
    ADMIN_DEFAULT_PASSWORD: str = "admin123"

    # File Storage
    STORAGE_TYPE: str = "local"  # "local" or "s3"
    S3_BUCKET_NAME: str = ""
    S3_REGION: str = ""

    # External Services
    OSM_NOMINATIM_URL: str = "https://nominatim.openstreetmap.org"

    class Config:
        env_file = ".env"


settings = Settings()
