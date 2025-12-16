"""Custom exceptions for the price client."""


class PriceFetchError(Exception):
    """Base exception for all price fetching failures."""
    pass


class PriceCriticalError(PriceFetchError):
    """Raised for errors requiring an immediate halt (e.g., bad data, API down after retries)."""
    pass


class RateLimitError(PriceFetchError):
    """Raised when rate limit is hit and a fast-fail is chosen."""
    pass
