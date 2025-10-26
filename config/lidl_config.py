"""Configuration constants for Lidl API integration."""


class LidlConfig:
    """Configuration constants for Lidl API integration."""

    # File paths
    RECEIPTS_JSON_FILE = "lidl_receipts.json"
    COOKIES_JSON_FILE = "lidl_cookies.json"

    # API endpoints
    LIDL_BASE_URL = "https://www.lidl.de"
    TICKETS_API_URL = f"{LIDL_BASE_URL}/mre/api/v1/tickets"
    RECEIPT_API_URL = f"{LIDL_BASE_URL}/mre/api/v1/tickets/{{receipt_id}}"

    # Request settings
    DEFAULT_TIMEOUT = 15
    REQUEST_DELAY = 0.5
    PAGES_TO_CHECK = 3

    # Browser settings
    SUPPORTED_BROWSERS = {"firefox": "Firefox", "chrome": "Chrome"}

    # API settings
    DEFAULT_COUNTRY = "DE"
    DEFAULT_LANGUAGE = "de-DE"
    DEFAULT_PAGE_SIZE = 10
