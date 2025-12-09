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
    STORAGE_TYPE: str = "local"  # "local" or "minio"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "openinfra-assets"
    MINIO_USE_SSL: bool = False
    MINIO_REGION: str = "us-east-1"  # MinIO region (for compatibility)

    # External Services
    OSM_NOMINATIM_URL: str = "https://nominatim.openstreetmap.org"

    # Cloudflare Turnstile (Captcha)
    TURNSTILE_SECRET_KEY: str = ""
    TURNSTILE_SITE_KEY: str = ""
    TURNSTILE_VERIFY_URL: str = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

    # AI Agent - Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_TEXT_MODEL: str = "text-embedding-004"
    GEMINI_VISION_MODEL: str = "gemini-2.5-flash"
    
    # Duplicate Detection Configuration
    DUPLICATE_SIMILARITY_THRESHOLD: float = 0.85
    DUPLICATE_TEXT_WEIGHT: float = 0.6
    DUPLICATE_IMAGE_WEIGHT: float = 0.4
    DUPLICATE_TIME_WINDOW_HOURS: int = 168  # 7 days for active incidents
    DUPLICATE_RESOLVED_TIME_WINDOW_HOURS: int = 720  # 30 days for resolved incidents (recurrence detection)
    DUPLICATE_LOCATION_RADIUS_METERS: float = 50.0
    GEMINI_MAX_IMAGES_PER_INCIDENT: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
