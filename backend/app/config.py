import os
from dotenv import load_dotenv
from pydantic import BaseSettings

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "StyleMate"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]  # Frontend URL
    
    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # ChromaDB settings
    CHROMA_DB_DIR: str = os.getenv("CHROMA_DB_DIR", "./chromadb")
    
    # AI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    class Config:
        case_sensitive = True

# Create settings instance
settings = Settings()