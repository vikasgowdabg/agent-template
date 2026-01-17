import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Required
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Optional
    MONGO_CONNECTION_STRING: str = os.getenv("MONGO_CONNECTION_STRING", "")
