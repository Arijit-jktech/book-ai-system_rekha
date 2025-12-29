"""
Core configuration module for the Book Management System.
"""
from functools import lru_cache
from typing import List, Optional, Union

from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings that automatically read from environment variables."""
    
    # Application Settings
    app_name: str = Field(
        default="Intelligent Book Management System", 
        env="APP_NAME",
        description="Application name"
    )
    app_version: str = Field(
        default="1.0.0", 
        env="APP_VERSION",
        description="Application version"
    )
    debug: bool = Field(
        default=False, 
        env="DEBUG",
        description="Debug mode flag"
    )
    environment: str = Field(
        default="development", 
        env="ENVIRONMENT",
        description="Environment (development, staging, production)"
    )
    
    # Database Configuration
    database_url: str = Field(
        ..., 
        env="DATABASE_URL",
        description="Async database connection URL"
    )
    database_url_sync: Optional[str] = Field(
        default=None, 
        env="DATABASE_URL_SYNC",
        description="Sync database connection URL (optional)"
    )
    
    # JWT Authentication
    secret_key: str = Field(
        ..., 
        env="SECRET_KEY",
        description="JWT secret key (minimum 32 characters)"
    )
    algorithm: str = Field(
        default="HS256", 
        env="ALGORITHM",
        description="JWT signing algorithm"
    )
    access_token_expire_minutes: int = Field(
        default=1440, 
        env="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="JWT token expiration time in minutes"
    )
    
    # AI Service Configuration
    ai_provider: str = Field(
        default="auto",
        env="AI_PROVIDER",
        description="AI provider mode: auto | openai_compat | ollama"
    )
    ai_service_url: str = Field(
        default="http://localhost:11434", 
        env="AI_SERVICE_URL",
        description="AI service base URL"
    )
    ai_api_key: Optional[str] = Field(
        default=None, 
        env="AI_API_KEY",
        description="AI service API key (optional for local Ollama)"
    )
    ai_model_name: str = Field(
        default="llama3", 
        env="AI_MODEL_NAME",
        description="AI model name"
    )
    ai_max_tokens: int = Field(
        default=1024,
        env="AI_MAX_TOKENS",
        description="Default max tokens/num_predict for AI responses"
    )
    ai_temperature: float = Field(
        default=0.7,
        env="AI_TEMPERATURE",
        description="Sampling temperature for AI responses"
    )
    ai_top_p: float = Field(
        default=0.9,
        env="AI_TOP_P",
        description="Nucleus sampling probability for AI responses"
    )
    ai_timeout: int = Field(
        default=300, 
        env="AI_TIMEOUT",
        description="AI service request timeout in seconds"
    )
    
    # Redis Configuration (Optional for caching)
    redis_url: Optional[str] = Field(
        default=None, 
        env="REDIS_URL",
        description="Redis connection URL for caching"
    )
    redis_port: int = Field(
        default=6379, 
        env="REDIS_PORT",
        description="Redis port"
    )
    
    # CORS Configuration
    allowed_origins: Union[List[str], str] = Field(
        default=["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:3000"],
        env="ALLOWED_ORIGINS",
        description="Allowed CORS origins"
    )
    
    # Pagination Settings
    default_page_size: int = Field(
        default=20, 
        env="DEFAULT_PAGE_SIZE",
        description="Default number of items per page"
    )
    max_page_size: int = Field(
        default=100, 
        env="MAX_PAGE_SIZE",
        description="Maximum number of items per page"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO", 
        env="LOG_LEVEL",
        description="Logging level"
    )
    log_format: str = Field(
        default="json", 
        env="LOG_FORMAT",
        description="Log format (json or text)"
    )
    
    # Security Settings
    bcrypt_rounds: int = Field(
        default=12, 
        env="BCRYPT_ROUNDS",
        description="Number of bcrypt hashing rounds"
    )
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        """Validate that secret key is long enough."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("allowed_origins", pre=True)
    def validate_allowed_origins(cls, v):
        """Parse allowed origins from string or list."""
        if isinstance(v, str):
            # Handle comma-separated string or JSON array string
            if v.startswith("[") and v.endswith("]"):
                import json
                return json.loads(v)
            else:
                return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment value."""
        if v.lower() not in ["development", "staging", "production"]:
            raise ValueError("ENVIRONMENT must be development, staging, or production")
        return v.lower()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def database_url_sync_computed(self) -> str:
        """Get sync database URL, computed from async URL if not provided."""
        if self.database_url_sync:
            return self.database_url_sync
        # Convert asyncpg URL to psycopg2 URL
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings instance."""
    return Settings()