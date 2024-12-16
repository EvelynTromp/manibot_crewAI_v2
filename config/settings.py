from pydantic_settings import BaseSettings
from typing import Dict
import os

class Settings(BaseSettings):
    # API Keys
    MANIFOLD_API_KEY: str = "6a40ae0d-1de0-4217-acb8-124728eebcfc"
    OPENAI_API_KEY: str = "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"
    GOOGLE_API_KEY: str = "AIzaSyD23WN0eOG_Fpt_ZrfWwzQFYGcGaNsixNE"
    
    # Agent Configuration
    MAX_SEARCH_RESULTS: int = 5
    MAX_TOKENS: int = 4000
    TEMPERATURE: float = 0.7
    
    # Market Configuration
    MIN_PROBABILITY: float = 0.1
    MAX_PROBABILITY: float = 0.9
    MIN_BET_AMOUNT: float = 10
    MAX_BET_AMOUNT: float = 100
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()