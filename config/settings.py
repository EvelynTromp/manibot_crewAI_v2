# config/settings.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Simplified configuration settings for the trading system. This version 
    organizes settings into logical groups and removes unnecessary complexity.
    Settings are divided into core API settings, trading parameters, and
    operational settings.
    """

    
    # Trading Parameters
    # These control how the system makes trading decisions
    MIN_BET_AMOUNT: float = 10.0
    MAX_BET_AMOUNT: float = 100.0
    MIN_EDGE_REQUIREMENT: float = 0.02
    MAX_POSITION_SIZE_RATIO: float = 0.15  # Maximum bet relative to market liquidity
    MAX_DAILY_LOSS: float = 100.0  # Maximum allowed loss per day
    
    # Market Qualification Parameters
    # These determine which markets the system will consider trading
    MIN_MARKET_LIQUIDITY: float = 10.0  # Minimum required market liquidity
    MIN_UNIQUE_TRADERS: int = 3  # Minimum number of unique traders in market
    MAX_PROBABILITY: float = 0.9  # Maximum probability for consideration
    MIN_PROBABILITY: float = 0.1  # Minimum probability for consideration
    
    # Operational Settings
    # These control how the system operates and handles requests
    RATE_LIMIT_DELAY: float = 2.0  # Delay between API calls
    MAX_RETRIES: int = 3  # Maximum number of retry attempts
    RETRY_DELAY: float = 2.0  # Delay between retries
    SEARCH_TIMEOUT: int = 30  # Timeout for search operations
    
    # Logging Configuration
    # These control how the system logs its operations
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "manibot.log"
    
    class Config:
        """Configuration for the settings class."""
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields
    
    def validate_configuration(self) -> bool:
        """
        Validate the configuration settings to ensure they are logically consistent.
        Returns True if the configuration is valid, raises ValueError otherwise.
        """
        # Validate bet amounts
        if self.MIN_BET_AMOUNT >= self.MAX_BET_AMOUNT:
            raise ValueError("MIN_BET_AMOUNT must be less than MAX_BET_AMOUNT")
            
        # Validate probabilities
        if self.MIN_PROBABILITY >= self.MAX_PROBABILITY:
            raise ValueError("MIN_PROBABILITY must be less than MAX_PROBABILITY")
            
        # Validate position sizing
        if self.MAX_POSITION_SIZE_RATIO <= 0 or self.MAX_POSITION_SIZE_RATIO > 1:
            raise ValueError("MAX_POSITION_SIZE_RATIO must be between 0 and 1")
            
        # Validate operational parameters
        if self.RATE_LIMIT_DELAY < 0:
            raise ValueError("RATE_LIMIT_DELAY must be non-negative")
            
        if self.MAX_RETRIES < 0:
            raise ValueError("MAX_RETRIES must be non-negative")
            
        return True
    
    def get_logging_config(self) -> dict:
        """
        Returns a dictionary with logging configuration.
        This simplifies logging setup across the application.
        """
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': self.LOG_FORMAT
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
                    'formatter': 'standard',
                    'level': self.LOG_LEVEL
                }
            },
            'loggers': {
                '': {
                    'handlers': ['console', 'file'],
                    'level': self.LOG_LEVEL,
                    'propagate': True
                }
            }
        }
    
    def get_market_requirements(self) -> dict:
        """Returns a dictionary of market requirements for easy validation."""
        return {
            'min_liquidity': self.MIN_MARKET_LIQUIDITY,
            'max_probability': self.MAX_PROBABILITY,
            'min_probability': self.MIN_PROBABILITY
        }
    
    def get_trade_limits(self) -> dict:
        """
        Returns a dictionary of trading limits for easy reference.
        This helps centralize trade validation logic.
        """
        return {
            'min_bet': self.MIN_BET_AMOUNT,
            'max_bet': self.MAX_BET_AMOUNT,
            'max_position_ratio': self.MAX_POSITION_SIZE_RATIO,
            'max_daily_loss': self.MAX_DAILY_LOSS
        }

# Create settings instance
settings = Settings()

# Validate settings on import
settings.validate_configuration()