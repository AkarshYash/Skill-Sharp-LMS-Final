from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "EduAI Platform"
    SECRET_KEY: str = "eduai_secret_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "sqlite:///./eduai.db"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    STRIPE_SECRET_KEY: str = ""
    REDIS_URL: str = ""
    FRONTEND_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"

settings = Settings()
