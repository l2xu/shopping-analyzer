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
    SUPPORTED_BROWSERS = {"firefox": "Firefox", "chrome": "Chrome", "chromium": "Chromium"}

    # API settings
    DEFAULT_COUNTRY = "DE"
    DEFAULT_LANGUAGE = "de-DE"
    DEFAULT_PAGE_SIZE = 10

    @classmethod
    def set_base_url(cls, base_url: str) -> None:
        """
        Set the base URL and update derived URLs.

        Args:
            base_url: Base URL for Lidl API (e.g., 'https://www.lidl.bg')
        """
        cls.LIDL_BASE_URL = base_url.rstrip("/")
        cls.TICKETS_API_URL = f"{cls.LIDL_BASE_URL}/mre/api/v1/tickets"
        cls.RECEIPT_API_URL = f"{cls.LIDL_BASE_URL}/mre/api/v1/tickets/{{receipt_id}}"
