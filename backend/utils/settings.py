from pydantic import AnyUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    CLIENT_ID: str
    CLIENT_SECRET: str
    TENANT_ID: str
    REDIRECT_URI: str
    MONGODB_URI: AnyUrl
    DATABASE_NAME: str = "work_intel"
    FRONTEND_URL: str = "http://localhost:8080"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()