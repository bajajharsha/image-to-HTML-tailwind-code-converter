from pydantic_settings import BaseSettings
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    GEMINI_MODEL_NAME: str
    GEMINI_STREAM_URL: str
    CLAUDE_API_KEY: str
    CLAUDE_MODEL_NAME: str
    UPLOAD_DIR: str
    GEMINI_URL: str
    MONGO_URI: str
    CLAUDE_URL: str
    MONGODB_DB_NAME: str
    ERROR_COLLECTION_NAME: str
    LLM_USAGE_COLLECTION_NAME: str
    GEMINI_STREAM_URL: str
    HOST: str

    class Config:
        env_file = os.path.join(PROJECT_ROOT, '.env')

settings = Settings()