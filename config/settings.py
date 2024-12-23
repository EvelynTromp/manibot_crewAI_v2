
from typing import Dict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Enhanced configuration settings for the autonomous trading system.
    This version streamlines the configuration by removing legacy search parameters
    and adding support for GPT-4's native search capabilities.
    """
    
    # API Keys - Essential for core functionality
    MANIFOLD_API_KEY: str = "2ad841d8-edd6-4d8d-a08f-0e4e7f2c027d"
    OPENAI_API_KEY: str = "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"
    GOOGLE_API_KEY: str = "AIzaSyD23WN0eOG_Fpt_ZrfWwzQFYGcGaNsixNE"
    
    # GPT Model Configuration
    GPT_MODEL: str = "gpt-4-turbo-preview"  # Model with search capabilities
    MAX_TOKENS: int = 4000
    TEMPERATURE: float = 0.7
    MAX_SEARCH_RESULTS: int = 5  # Maximum number of sources to consider
    MIN_SOURCE_CREDIBILITY: float = 0.7  # Minimum credibility score (0-1)
    SEARCH_TIMEOUT: int = 30  # Seconds to wait for search results
    
    # Market Analysis Configuration
    MIN_PROBABILITY: float = 0.1
    MAX_PROBABILITY: float = 0.9
    MIN_BET_AMOUNT: float = 1.0
    MAX_BET_AMOUNT: float = 100.0
    MIN_EDGE_REQUIREMENT: float = 0.02
    
    # Market Qualification Parameters
    MIN_MARKET_LIQUIDITY: float = 10.0
    MIN_MARKET_VOLUME: float = 3.0
    MIN_UNIQUE_TRADERS: int = 3
    
    # Rate Limiting and Performance
    RATE_LIMIT_DELAY: float = 2.0  # Delay between market analyses
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 2.0
    MAX_CONCURRENT_POSITIONS: int = 10
    
    # Risk Management
    MAX_POSITION_SIZE_RATIO: float = 0.15
    MAX_DAILY_LOSS: float = 100.0
    POSITION_SIZE_SCALING: float = 0.8  # Scale factor for position sizing
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "manibot.log"
    
    # Report Configuration
    REPORT_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S UTC"
    REPORT_CURRENCY_FORMAT: str = "${:,.2f}"
    REPORT_PERCENTAGE_FORMAT: str = "{:.1%}"
    MAX_REPORT_SOURCES: int = 10
    INCLUDE_SOURCE_SNIPPETS: bool = True
    
    # Source Validation
    SOURCE_TYPES: Dict[str, float] = {
        "NEWS": 1.0,
        "ACADEMIC": 0.9,
        "SOCIAL": 0.5,
        "BLOG": 0.7,
        "OFFICIAL": 1.0
    }


    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_logging_config(self) -> Dict:
        """Returns a comprehensive logging configuration dictionary."""
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
                    'filename': self.LOG_FILE,
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