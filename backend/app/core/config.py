from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Infrastructure Management System"
    MONGODB_URL: str = "mongodb://mongo:27017"
    DATABASE_NAME: str = "gis_db"
    
    class Config:
        env_file = ".env"

settings = Settings()
