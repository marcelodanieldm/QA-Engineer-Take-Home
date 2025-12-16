# test_price.py
import pytest
from unittest.mock import MagicMock
from requests import Response
from price_client import get_hyperliquid_price, MAX_RETRIES
from exceptions import PriceCriticalError, RateLimitError

# Helper fixture to create a mock response object
@pytest.fixture
def mock_response(mocker):
    """Fixture to create a mock requests.Response object."""
    def _mock_response(status_code=200, json_data=None, headers=None):
        resp = mocker.MagicMock(spec=Response)
        resp.status_code = status_code
        resp.json.return_value = json_data if json_data is not None else {}
        resp.raise_for_status = MagicMock()
        resp.headers = headers if headers is not None else {}
        return resp
    return _mock_response

# ----------------------------------------------------
# 1. Normal Case (200 OK)
# ----------------------------------------------------

def test_normal_case_200_ok(mocker, mock_response):
    """
    Severity: Low. Mock a valid response with a positive numeric price.
    Assert the function returns the expected float.
    """
    mock_resp = mock_response(json_data={"price": 1234.56})
    mocker.patch('requests.get', return_value=mock_resp)
    
    price = get_hyperliquid_price("ETH")
    assert price == 1234.56
    assert isinstance(price, float)
    
# ----------------------------------------------------
# 2. API Down (500 Error)
# ----------------------------------------------------

def test_api_down_500_retry_success(mocker, mock_response):
    """
    Severity: Low. Mock transient 500 errors followed by success.
    Assert the function succeeds and the API call is made N times.
    """
    mock_resp_fail = mock_response(status_code=500)
    mock_resp_success = mock_response(json_data={"price": 100.0})
    
    # Fail twice, succeed on the third attempt (MAX_RETRIES=3)
    mock_get = mocker.patch(
        'requests.get', 
        side_effect=[mock_resp_fail, mock_resp_fail, mock_resp_success]
    )
    
    price = get_hyperliquid_price("BTC")
    assert price == 100.0
    # The call should be made MAX_RETRIES times (3)
    assert mock_get.call_count == MAX_RETRIES

def test_api_down_500_critical_failure(mocker, mock_response):
    """
    Severity: Critical. Mock 500 on all N attempts.
    Assert: Retry N times, then raise PriceCriticalError.
    """
    mock_resp_fail = mock_response(status_code=500)
    
    # Fail MAX_RETRIES times (3)
    mock_get = mocker.patch(
        'requests.get', 
        return_value=mock_resp_fail
    )
    
    with pytest.raises(PriceCriticalError) as excinfo:
        get_hyperliquid_price("SOL")
        
    assert "Failed after 3 attempts" in str(excinfo.value)
    assert mock_get.call_count == MAX_RETRIES

# ----------------------------------------------------
# 3. Bad Data Cases (200 OK with bad content)
# ----------------------------------------------------

@pytest.mark.parametrize("bad_json", [
    {"price": -100.0},        # price: -100 (Critical)
    {"price": None},          # price: null (Critical)
    {"value": 500},           # Missing 'price' field (Critical)
])
def test_bad_data_critical_cases(mocker, mock_response, bad_json):
    """
    Severity: Critical. Response is 200, but data is invalid.
    Assert: Treat as critical and raise PriceCriticalError.
    """
    mock_resp = mock_response(json_data=bad_json)
    mocker.patch('requests.get', return_value=mock_resp)
    
    with pytest.raises(PriceCriticalError) as excinfo:
        get_hyperliquid_price("LTC")
    
    assert "Bad data" in str(excinfo.value)
    
# ----------------------------------------------------
# 4. Rate Limit (429)
# ----------------------------------------------------

def test_rate_limit_429_fail_fast(mocker, mock_response):
    """
    Severity: High. Mock a 429 response.
    Assert: Fails fast and signals rate limiting via RateLimitError.
    """
    mock_resp = mock_response(
        status_code=429, 
        headers={"Retry-After": "5"}
    )
    mock_get = mocker.patch('requests.get', return_value=mock_resp)
    
    with pytest.raises(RateLimitError) as excinfo:
        get_hyperliquid_price("ARB")
        
    assert "Rate limit exceeded. Fail-fast chosen." in str(excinfo.value)
    # Ensure it only tried once (fail fast)
    assert mock_get.call_count == 1

def test_rate_limit_429_no_retry_after(mocker, mock_response):
    """
    Severity: High. Mock a 429 response missing the Retry-After header.
    Assert: Fails fast and signals rate limiting.
    """
    mock_resp = mock_response(status_code=429, headers={})
    mocker.patch('requests.get', return_value=mock_resp)
    
    with pytest.raises(RateLimitError):
        get_hyperliquid_price("ARB")
