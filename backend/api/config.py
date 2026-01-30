"""API configuration settings."""
import logging
import os
from pathlib import Path

from core.settings import get_settings

logger = logging.getLogger(__name__)

# Get centralized settings
_settings = get_settings()

# Centralized API key - used across all API modules
API_KEY = os.getenv("API_KEY")

# API server settings
API_CONFIG = {
    "host": os.getenv("API_HOST", _settings.api.host),
    "port": int(os.getenv("API_PORT", str(_settings.api.port))),
    "reload": os.getenv("API_RELOAD", "false").lower() == "true",
    "log_level": os.getenv("API_LOG_LEVEL", _settings.api.log_level),
    "cors_origins": os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"],
    "api_key": API_KEY,  # Optional API key for authentication
}

# Log warning if wildcard CORS is used
if "*" in API_CONFIG["cors_origins"]:
    logger.warning("WARNING: CORS configured with wildcard origin (*). Set CORS_ORIGINS for production.")

# JWT configuration
JWT_CONFIG = {
    "secret_key": _settings.jwt.secret,
    "algorithm": _settings.jwt.algorithm,
    "access_token_expire_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    "refresh_token_expire_days": int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
    "issuer": _settings.jwt.issuer,
    "audience": _settings.jwt.audience,
}

# Log JWT status
logger.info("JWT authentication enabled (using JWT_SECRET)")

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
