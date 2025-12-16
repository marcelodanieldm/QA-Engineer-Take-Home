"""Mock price API client with realistic failure patterns."""

import random
from typing import Optional
from exceptions import (
    NetworkError,
    RateLimitError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
)


def get_stock_price_from_api(ticker: str, api_key: Optional[str] = None) -> float:
    """
    Mock function simulating a real stock price API with realistic failure modes.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
        api_key: Optional API authentication key
        
    Returns:
        float: Mock stock price
        
    Raises:
        ValidationError: Invalid ticker format
        AuthenticationError: Missing or invalid API key
        NotFoundError: Ticker not found
        RateLimitError: Rate limit exceeded
        NetworkError: Network/timeout issues
    """
    # Validate ticker format
    if not ticker or not isinstance(ticker, str):
        raise ValidationError("Ticker must be a non-empty string")
    
    if not ticker.isalpha() or len(ticker) > 5:
        raise ValidationError(f"Invalid ticker format: {ticker}")
    
    # Check authentication
    if api_key is None:
        raise AuthenticationError("API key is required")
    
    if api_key != "valid_api_key":
        raise AuthenticationError("Invalid API key")
    
    # Simulate unknown tickers
    valid_tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META"]
    if ticker.upper() not in valid_tickers:
        raise NotFoundError(f"Ticker '{ticker}' not found")
    
    # Simulate transient failures (10% chance)
    failure_roll = random.random()
    if failure_roll < 0.05:
        raise NetworkError("Connection timeout")
    elif failure_roll < 0.10:
        raise RateLimitError("Rate limit exceeded. Please try again later.")
    
    # Return mock price based on ticker
    mock_prices = {
        "AAPL": 175.50,
        "GOOGL": 140.25,
        "MSFT": 380.00,
        "AMZN": 155.75,
        "TSLA": 245.30,
        "META": 350.60,
    }
    
    return mock_prices[ticker.upper()]


class PriceClient:
    """
    Client for fetching stock prices with retry logic and error handling.
    """
    
    def __init__(self, api_key: str, max_retries: int = 3):
        """
        Initialize the price client.
        
        Args:
            api_key: API authentication key
            max_retries: Maximum number of retries for transient errors
        """
        self.api_key = api_key
        self.max_retries = max_retries
    
    def get_price(self, ticker: str) -> float:
        """
        Get stock price with automatic retry logic for transient errors.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            float: Stock price
            
        Raises:
            ValidationError: Invalid input
            AuthenticationError: Authentication failed
            NotFoundError: Ticker not found
            NetworkError: Network error after retries exhausted
            RateLimitError: Rate limit error after retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return get_stock_price_from_api(ticker, self.api_key)
            except (NetworkError, RateLimitError) as e:
                # Transient errors - retry
                last_exception = e
                if attempt < self.max_retries - 1:
                    continue
                else:
                    # Exhausted retries
                    raise
            except (ValidationError, AuthenticationError, NotFoundError):
                # Permanent errors - don't retry
                raise
        
        # Should not reach here, but raise last exception if we do
        if last_exception:
            raise last_exception
