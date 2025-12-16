# price_client.py
import requests
import time
from exceptions import PriceCriticalError, RateLimitError

# Configuration constants
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5  # Time to wait between retries (0.5s, 1s, 2s...)

def get_hyperliquid_price(symbol: str) -> float:
    """
    Fetches the hyperliquid price for a given symbol, with resilience logic.

    Note: This is the function under test. We assume a simple API endpoint.
    """
    url = f"https://api.hyperliquid.com/price/{symbol}"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=5)
            
            # --- API Down/Server Error (5xx) ---
            if response.status_code >= 500:
                print(f"Server error {response.status_code} on attempt {attempt + 1}. Retrying...")
                # Transient error, we continue to retry
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_FACTOR * (2 ** attempt))
                    continue
                else:
                    # Critical failure after all retries
                    raise PriceCriticalError(
                        f"API down: Failed after {MAX_RETRIES} attempts. Status: {response.status_code}"
                    )

            # --- Rate Limit (429) ---
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    # Option 1: Wait and retry (This logic is complex to test without mocking time)
                    # print(f"Rate limited. Waiting for {retry_after} seconds...")
                    # time.sleep(int(retry_after))
                    # continue # Retry immediately after wait
                    
                    # Option 2 (Chosen for robustness): Fail fast and signal the issue.
                    raise RateLimitError(
                        f"Rate limit exceeded. Fail-fast chosen. Retry-After: {retry_after}"
                    )
                else:
                    # Treat an un-signaled 429 as a critical rate limit issue
                    raise RateLimitError("Rate limit exceeded without Retry-After header.")

            # --- Normal Response (200 OK) ---
            response.raise_for_status() # Raises for 4xx clients errors (except 429 handled above)

            data = response.json()
            price_value = data.get("price")

            # --- Bad Data Cases ---
            if price_value is None or not isinstance(price_value, (int, float)):
                raise PriceCriticalError(f"Bad data: Price field is null or missing in response: {data}")

            price = float(price_value)
            if price <= 0:
                raise PriceCriticalError(f"Bad data: Price is non-positive: {price}")
            
            # Success
            return price

        except RateLimitError:
            # Re-raise RateLimitError without wrapping
            raise
        except PriceCriticalError:
            # Re-raise PriceCriticalError without wrapping
            raise
        except requests.exceptions.Timeout:
            print(f"Request timeout on attempt {attempt + 1}. Retrying...")
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_FACTOR * (2 ** attempt))
                continue
            else:
                raise PriceCriticalError(
                    f"Connection Timeout: Failed after {MAX_RETRIES} attempts."
                )
        except requests.exceptions.ConnectionError as e:
            # Handle DNS/network issues
            print(f"Connection error on attempt {attempt + 1}. Retrying...")
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_FACTOR * (2 ** attempt))
                continue
            else:
                raise PriceCriticalError(
                    f"Network Error: Failed after {MAX_RETRIES} attempts. {e}"
                )
        except Exception as e:
            # Catch all other exceptions (e.g., JSON decode error)
            raise PriceCriticalError(f"Unexpected error during fetch: {e}") from e

    # Should be unreachable if the final attempt raises PriceCriticalError
    raise PriceCriticalError("Exhausted all retries without definite failure.")
