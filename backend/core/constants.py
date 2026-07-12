"""Application-wide constants."""

# Application
APP_NAME: str = "Sona AI OS"
APP_DESCRIPTION: str = "AI-native operating system"
API_VERSION: str = "v1"
API_PREFIX: str = f"/api/{API_VERSION}"

# Status
STATUS_HEALTHY: str = "healthy"
STATUS_UNHEALTHY: str = "unhealthy"
STATUS_DEGRADED: str = "degraded"

# Pagination defaults
DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100
MIN_PAGE_SIZE: int = 1

# Rate limiting
DEFAULT_RATE_LIMIT: int = 60  # requests per minute
BURST_RATE_LIMIT: int = 100

# Headers
HEADER_REQUEST_ID: str = "X-Request-ID"
HEADER_API_VERSION: str = "X-API-Version"
HEADER_RESPONSE_TIME: str = "X-Response-Time"

# Content types
CONTENT_TYPE_JSON: str = "application/json"

# Time
SECONDS_IN_MINUTE: int = 60
SECONDS_IN_HOUR: int = 3600
SECONDS_IN_DAY: int = 86400
