"""Custom exceptions for the price client."""


class PriceClientException(Exception):
    """Base exception for all price client errors."""
    pass


class TransientError(PriceClientException):
    """Transient errors that may resolve with retries (e.g., timeouts, rate limits)."""
    pass


class PermanentError(PriceClientException):
    """Permanent errors that won't resolve with retries (e.g., invalid API key, not found)."""
    pass


class NetworkError(TransientError):
    """Network-related errors (timeouts, connection failures)."""
    pass


class RateLimitError(TransientError):
    """API rate limit exceeded."""
    pass


class AuthenticationError(PermanentError):
    """Invalid API key or authentication failure."""
    pass


class NotFoundError(PermanentError):
    """Resource not found (e.g., invalid ticker symbol)."""
    pass


class ValidationError(PermanentError):
    """Invalid input parameters."""
    pass
