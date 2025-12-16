"""
Comprehensive test suite for the Price Client.

This test suite covers:
1. Happy path scenarios
2. Permanent failures (don't retry)
3. Transient failures (retry logic)
4. Edge cases and boundary conditions
"""

import pytest
from unittest.mock import patch, MagicMock
from price_client import PriceClient, get_stock_price_from_api
from exceptions import (
    ValidationError,
    AuthenticationError,
    NotFoundError,
    NetworkError,
    RateLimitError,
)


# ============================================================================
# HAPPY PATH TESTS
# ============================================================================

class TestHappyPath:
    """Tests for successful API calls."""
    
    def test_successful_price_fetch_with_valid_ticker(self):
        """Should return price for valid ticker with valid API key."""
        client = PriceClient(api_key="valid_api_key")
        
        with patch('price_client.get_stock_price_from_api', return_value=175.50):
            price = client.get_price("AAPL")
            assert price == 175.50
    
    def test_successful_price_fetch_multiple_tickers(self):
        """Should return correct prices for different valid tickers."""
        client = PriceClient(api_key="valid_api_key")
        
        mock_prices = {
            "AAPL": 175.50,
            "GOOGL": 140.25,
            "MSFT": 380.00,
        }
        
        for ticker, expected_price in mock_prices.items():
            with patch('price_client.get_stock_price_from_api', return_value=expected_price):
                price = client.get_price(ticker)
                assert price == expected_price
    
    def test_case_insensitive_ticker(self):
        """Should handle tickers regardless of case."""
        with patch('price_client.get_stock_price_from_api', return_value=175.50):
            # Mock function handles case internally
            price = get_stock_price_from_api("aapl", "valid_api_key")
            assert price == 175.50


# ============================================================================
# PERMANENT FAILURE TESTS (Should NOT Retry)
# ============================================================================

class TestPermanentFailures:
    """Tests for permanent errors that should not trigger retries."""
    
    def test_invalid_api_key(self):
        """Should raise AuthenticationError for invalid API key without retry."""
        client = PriceClient(api_key="invalid_key")
        
        with patch('price_client.get_stock_price_from_api', side_effect=AuthenticationError("Invalid API key")) as mock_api:
            with pytest.raises(AuthenticationError, match="Invalid API key"):
                client.get_price("AAPL")
            
            # Should only be called once (no retries for permanent errors)
            assert mock_api.call_count == 1
    
    def test_missing_api_key(self):
        """Should raise AuthenticationError when API key is None."""
        with pytest.raises(AuthenticationError, match="API key is required"):
            get_stock_price_from_api("AAPL", api_key=None)
    
    def test_ticker_not_found(self):
        """Should raise NotFoundError for unknown ticker without retry."""
        client = PriceClient(api_key="valid_api_key")
        
        with patch('price_client.get_stock_price_from_api', side_effect=NotFoundError("Ticker 'INVALID' not found")) as mock_api:
            with pytest.raises(NotFoundError, match="not found"):
                client.get_price("INVALID")
            
            # Should only be called once
            assert mock_api.call_count == 1
    
    def test_empty_ticker(self):
        """Should raise ValidationError for empty ticker without retry."""
        client = PriceClient(api_key="valid_api_key")
        
        with patch('price_client.get_stock_price_from_api', side_effect=ValidationError("Ticker must be a non-empty string")) as mock_api:
            with pytest.raises(ValidationError, match="non-empty string"):
                client.get_price("")
            
            # Should only be called once
            assert mock_api.call_count == 1
    
    def test_invalid_ticker_format(self):
        """Should raise ValidationError for invalid ticker format without retry."""
        client = PriceClient(api_key="valid_api_key")
        
        invalid_tickers = ["123", "ABC-DEF", "TOOLONG123", "A@PL"]
        
        for ticker in invalid_tickers:
            with patch('price_client.get_stock_price_from_api', side_effect=ValidationError(f"Invalid ticker format: {ticker}")) as mock_api:
                with pytest.raises(ValidationError):
                    client.get_price(ticker)
                
                # Should only be called once per ticker
                assert mock_api.call_count == 1
    
    def test_non_string_ticker(self):
        """Should raise ValidationError for non-string ticker."""
        with pytest.raises(ValidationError, match="must be a non-empty string"):
            get_stock_price_from_api(12345, "valid_api_key")


# ============================================================================
# TRANSIENT FAILURE TESTS (Should Retry)
# ============================================================================

class TestTransientFailures:
    """Tests for transient errors that should trigger retry logic."""
    
    def test_network_error_with_successful_retry(self):
        """Should retry on NetworkError and succeed on second attempt."""
        client = PriceClient(api_key="valid_api_key", max_retries=3)
        
        # First call fails, second succeeds
        with patch('price_client.get_stock_price_from_api', side_effect=[
            NetworkError("Connection timeout"),
            175.50
        ]) as mock_api:
            price = client.get_price("AAPL")
            
            assert price == 175.50
            assert mock_api.call_count == 2
    
    def test_rate_limit_with_successful_retry(self):
        """Should retry on RateLimitError and succeed on third attempt."""
        client = PriceClient(api_key="valid_api_key", max_retries=3)
        
        # Two failures, then success
        with patch('price_client.get_stock_price_from_api', side_effect=[
            RateLimitError("Rate limit exceeded"),
            RateLimitError("Rate limit exceeded"),
            140.25
        ]) as mock_api:
            price = client.get_price("GOOGL")
            
            assert price == 140.25
            assert mock_api.call_count == 3
    
    def test_network_error_exhausts_retries(self):
        """Should raise NetworkError after exhausting all retries."""
        client = PriceClient(api_key="valid_api_key", max_retries=3)
        
        # All attempts fail
        with patch('price_client.get_stock_price_from_api', side_effect=NetworkError("Connection timeout")) as mock_api:
            with pytest.raises(NetworkError, match="Connection timeout"):
                client.get_price("AAPL")
            
            # Should try max_retries times
            assert mock_api.call_count == 3
    
    def test_rate_limit_exhausts_retries(self):
        """Should raise RateLimitError after exhausting all retries."""
        client = PriceClient(api_key="valid_api_key", max_retries=2)
        
        with patch('price_client.get_stock_price_from_api', side_effect=RateLimitError("Rate limit exceeded")) as mock_api:
            with pytest.raises(RateLimitError, match="Rate limit exceeded"):
                client.get_price("MSFT")
            
            # Should try max_retries times
            assert mock_api.call_count == 2
    
    def test_mixed_transient_errors_with_success(self):
        """Should handle different transient errors and eventually succeed."""
        client = PriceClient(api_key="valid_api_key", max_retries=4)
        
        # Mix of transient errors, then success
        with patch('price_client.get_stock_price_from_api', side_effect=[
            NetworkError("Timeout"),
            RateLimitError("Rate limit"),
            NetworkError("Connection reset"),
            380.00
        ]) as mock_api:
            price = client.get_price("MSFT")
            
            assert price == 380.00
            assert mock_api.call_count == 4


# ============================================================================
# EDGE CASES AND BOUNDARY CONDITIONS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_zero_retries_configuration(self):
        """Should not retry when max_retries is set to 1."""
        client = PriceClient(api_key="valid_api_key", max_retries=1)
        
        with patch('price_client.get_stock_price_from_api', side_effect=NetworkError("Timeout")) as mock_api:
            with pytest.raises(NetworkError):
                client.get_price("AAPL")
            
            # Should only try once
            assert mock_api.call_count == 1
    
    def test_high_retry_count(self):
        """Should respect high max_retries setting."""
        client = PriceClient(api_key="valid_api_key", max_retries=10)
        
        # Fail 9 times, succeed on 10th
        side_effects = [NetworkError("Timeout")] * 9 + [175.50]
        
        with patch('price_client.get_stock_price_from_api', side_effect=side_effects) as mock_api:
            price = client.get_price("AAPL")
            
            assert price == 175.50
            assert mock_api.call_count == 10
    
    def test_permanent_error_after_transient_errors(self):
        """Should stop retrying when encountering a permanent error."""
        client = PriceClient(api_key="valid_api_key", max_retries=5)
        
        # Transient error, then permanent error
        with patch('price_client.get_stock_price_from_api', side_effect=[
            NetworkError("Timeout"),
            AuthenticationError("Invalid API key")
        ]) as mock_api:
            with pytest.raises(AuthenticationError):
                client.get_price("AAPL")
            
            # Should stop after permanent error (2 attempts total)
            assert mock_api.call_count == 2
    
    def test_ticker_with_maximum_length(self):
        """Should handle tickers at the maximum allowed length."""
        with patch('price_client.get_stock_price_from_api', return_value=100.00):
            # 5 characters is typically the max for tickers
            price = get_stock_price_from_api("ABCDE", "valid_api_key")
            assert price == 100.00
    
    def test_price_return_type(self):
        """Should always return a float value for successful calls."""
        client = PriceClient(api_key="valid_api_key")
        
        with patch('price_client.get_stock_price_from_api', return_value=175.50):
            price = client.get_price("AAPL")
            assert isinstance(price, float)
    
    def test_concurrent_requests_isolation(self):
        """Each request should be independent with its own retry logic."""
        client = PriceClient(api_key="valid_api_key", max_retries=2)
        
        # First request fails, second succeeds
        with patch('price_client.get_stock_price_from_api', side_effect=[
            NetworkError("Timeout"),
            NetworkError("Timeout"),  # First request exhausts retries
            175.50  # Second request succeeds immediately
        ]) as mock_api:
            # First request
            with pytest.raises(NetworkError):
                client.get_price("AAPL")
            
            # Second request should work
            price = client.get_price("AAPL")
            assert price == 175.50
            assert mock_api.call_count == 3


# ============================================================================
# INTEGRATION-STYLE TESTS
# ============================================================================

class TestRealisticScenarios:
    """Tests simulating realistic API usage patterns."""
    
    def test_realistic_api_call_without_mocking(self):
        """Test the actual mock API function behavior."""
        # This tests the mock function itself to ensure it behaves realistically
        
        # Valid call should work
        price = get_stock_price_from_api("AAPL", "valid_api_key")
        assert isinstance(price, float)
        assert price > 0
        
        # Invalid API key should fail
        with pytest.raises(AuthenticationError):
            get_stock_price_from_api("AAPL", "wrong_key")
        
        # Invalid ticker should fail
        with pytest.raises(NotFoundError):
            get_stock_price_from_api("INVALID", "valid_api_key")
    
    def test_batch_price_fetch(self):
        """Simulate fetching prices for multiple tickers in sequence."""
        client = PriceClient(api_key="valid_api_key")
        tickers = ["AAPL", "GOOGL", "MSFT"]
        
        prices = {}
        for ticker in tickers:
            with patch('price_client.get_stock_price_from_api', return_value=100.00 + len(ticker)):
                prices[ticker] = client.get_price(ticker)
        
        assert len(prices) == 3
        assert all(isinstance(price, float) for price in prices.values())
    
    def test_retry_with_backoff_simulation(self):
        """Simulate a scenario where retries eventually succeed (e.g., after rate limit clears)."""
        client = PriceClient(api_key="valid_api_key", max_retries=3)
        
        # Simulate rate limit that clears after 2 attempts
        with patch('price_client.get_stock_price_from_api', side_effect=[
            RateLimitError("Rate limit exceeded"),
            RateLimitError("Rate limit exceeded"),
            175.50
        ]) as mock_api:
            price = client.get_price("AAPL")
            
            assert price == 175.50
            assert mock_api.call_count == 3
