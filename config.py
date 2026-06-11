from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Skills Sharp 365 Innovation"
    APP_VERSION: str = "4.0.0"
    SECRET_KEY: str = "eduai_super_secret_key_2026_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "sqlite:///./eduai.db"
    
    # AI Keys
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    # LangChain / RAG
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_TOP_K: int = 4
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # AI Model Settings
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    MAX_AI_TOKENS: int = 2048
    AI_TEMPERATURE: float = 0.7
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    
    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    # Redis
    REDIS_URL: str = ""
    
    # Storage
    UPLOAD_DIR: str = "static/uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_VIDEO_TYPES: list = ["video/mp4", "video/webm", "video/ogg"]
    ALLOWED_DOC_TYPES: list = ["application/pdf", "text/plain", "application/msword"]
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:8000"
    CORS_ORIGINS: list = ["*"]
    
    # Features
    ENABLE_PAYMENTS: bool = False
    ENABLE_EMAIL: bool = False
    ENABLE_REDIS: bool = False
    ENABLE_2FA: bool = True
    REQUIRE_COURSE_APPROVAL: bool = True
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
