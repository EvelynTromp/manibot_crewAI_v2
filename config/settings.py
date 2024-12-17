from pydantic_settings import BaseSettings
import logging
from typing import Dict

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
    
    # Search Configuration
    GOOGLE_SEARCH_DELAY: float = 2.0  # Delay between searches in seconds
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(message)s"
    
    # Report Configuration
    REPORT_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S UTC"
    REPORT_CURRENCY_FORMAT: str = "${:,.2f}"
    REPORT_PERCENTAGE_FORMAT: str = "{:.1%}"
    
    # Report Display Options
    SHOW_TECHNICAL_DETAILS: bool = True
    MAX_RESEARCH_POINTS: int = 5
    MAX_ANALYSIS_FACTORS: int = 5
    
    # Rate Limiting
    MAX_CONCURRENT_SEARCHES: int = 3
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 2.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_logging_config(self) -> Dict:
        """Returns a complete logging configuration dictionary."""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': self.LOG_FORMAT
                },
                'detailed': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'standard',
                    'level': self.LOG_LEVEL
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'filename': 'manibot.log',
                    'formatter': 'detailed',
                    'level': 'DEBUG'
                }
            },
            'loggers': {
                '': {  # Root logger
                    'handlers': ['console', 'file'],
                    'level': self.LOG_LEVEL,
                    'propagate': True
                }
            }
        }

# Create the settings instance at module level
settings = Settings()