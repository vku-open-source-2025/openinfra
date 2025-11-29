from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Infrastructure Management System"
    MONGODB_URL: str = "mongodb://mongo:27017"
    DATABASE_NAME: str = "gis_db"
    ADMIN_JWT_SECRET: str = "change-me"
    ADMIN_JWT_ALGORITHM: str = "HS256"
    ADMIN_JWT_EXPIRE_MINUTES: int = 60 * 24
    ADMIN_DEFAULT_USERNAME: str = "admin"
    ADMIN_DEFAULT_PASSWORD: str = "admin123"
    
    class Config:
        env_file = ".env"

settings = Settings()
