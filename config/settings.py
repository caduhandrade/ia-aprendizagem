import os
import logging
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Google API Configuration
    google_api_key: str = Field(..., description="Google API key for Generative AI")
    
    # Application Configuration  
    app_name: str = Field("IA Aprendizagem")
    debug: bool = Field(False)
    environment: str = Field("development")
    
    # Session Configuration
    session_timeout_hours: int = Field(24, ge=1, le=168)  # 1 hour to 7 days
    max_sessions_per_user: int = Field(10, ge=1, le=100)
    
    # API Configuration
    api_host: str = Field("0.0.0.0")
    api_port: int = Field(49152, ge=1, le=65535)
    api_workers: int = Field(1, ge=1, le=8)
    
    # CORS Configuration
    cors_origins: str = Field("*")
    
    # Logging Configuration
    log_level: str = Field("INFO")
    
    @field_validator("google_api_key")
    @classmethod
    def validate_google_api_key(cls, v):
        if not v or v.strip() == "":
            raise ValueError("GOOGLE_API_KEY is required and cannot be empty")
        return v.strip()
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()
    
    @property
    def cors_origins_list(self) -> list:
        """Parse CORS origins string into a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"
    
    model_config = {
        "env_file": ".env", 
        "case_sensitive": False,
        "env_prefix": ""
    }


def setup_logging(settings: Settings) -> None:
    """Setup application logging."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # Set specific loggers for libraries
    if not settings.is_development:
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


# Global settings instance
try:
    settings = Settings()
    setup_logging(settings)
except Exception as e:
    print(f"Error loading settings: {e}")
    raise
