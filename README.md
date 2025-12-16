# QA Engineer Take-Home: Stock Price API Client

**Candidate:** Marcelo Daniel Lucero  
**Position:** QA Engineer

## Overview

This project implements a robust stock price API client with comprehensive error handling, retry logic, and a full test suite. The solution demonstrates best practices in QA engineering, including proper distinction between permanent and transient failures, realistic API simulation, and thorough test coverage.

This challenge was completed as part of the QA Engineer position application process.

## Project Structure

```
QA-Engineer-Take-Home/
├── .github/
│   ├── workflows/
│   │   └── test.yml              # GitHub Actions CI/CD pipeline
│   ├── scripts/
│   │   └── quality_gate.py       # Severity-based quality gate script
│   └── CI_CD_GUIDE.md           # Detailed CI/CD documentation
├── exceptions.py                 # Custom exception hierarchy
├── price_client.py               # API client with retry logic
├── test_price.py                 # Comprehensive Pytest suite
├── Test_Plan.md                 # Detailed test plan and strategy
└── README.md                    # This file
```

## Key Features

### 1. CI/CD Pipeline with Quality Gates (`.github/`)
- **GitHub Actions Workflow:** Automated testing on every push/PR
- **Severity-Based Quality Gates:** 
  - Critical/High failures → Block PR merge
  - Low failures → Allow merge with warnings
- **Automated PR Comments:** Test summaries posted to pull requests
- **JUnit XML Reporting:** Structured test results for analysis
- See [CI/CD Guide](.github/CI_CD_GUIDE.md) for detailed documentation

### 2. Exception Hierarchy (`exceptions.py`)
- **Base Exception:** `PriceFetchError`
- **Critical Errors:** `PriceCriticalError` (API down, bad data)
- **Rate Limit Errors:** `RateLimitError` (fail-fast behavior)

### 3. Price Client (`price_client.py`)
- **Hyperliquid API Integration:** Fetches crypto prices with retry logic
- **Smart Retry Logic:** Automatically retries transient errors (500 errors, timeouts, network issues)
- **Exponential Backoff:** 0.5s, 1s, 2s retry delays
- **Fail-Fast Rate Limiting:** Immediate failure on 429 errors
- **Data Validation:** Checks for null, negative, and malformed prices

### 4. Test Suite (`test_price.py`)
- **8 Test Cases** (with parametrization) covering:
  - ✅ Happy path scenarios (200 OK responses)
  - ✅ Server errors with retry (500, 502, 503, 504)
  - ✅ Bad data handling (negative, null, missing fields)
  - ✅ Rate limiting (429 with/without Retry-After header)
  - ✅ Severity categorization for quality gates

## Installation

### Prerequisites
- Python 3.8 or higher
- pip

### Setup

### 1. Exception Hierarchy (`exceptions.py`)
- **Base Exception:** `PriceClientException`
- **Transient Errors:** `NetworkError`, `RateLimitError` (retryable)
- **Permanent Errors:** `AuthenticationError`, `NotFoundError`, `ValidationError` (not retryable)

### 2. Price Client (`price_client.py`)
- **Mock API:** `get_stock_price_from_api()` simulates realistic API behavior
- **Smart Retry Logic:** Automatically retries transient errors, fails fast on permanent errors
- **Configurable:** Adjustable retry count and API authentication
- **Realistic Failures:** Includes random transient failures (10% chance) to simulate real-world conditions

### 3. Test Suite (`test_price.py`)
- **Test Cases** covering:
  - ✅ Happy path scenarios
  - ✅ Permanent failures (no retry)
  - ✅ Transient failures (with retry)
  - ✅ Edge cases and boundaries
  - ✅ Realistic integration scenarios

## Installation

### Prerequisites
- Python 3.8 or higher
- pip

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/marcelodanieldm/QA-Engineer-Take-Home.git
cd QA-Engineer-Take-Home
```

2. **Create virtual environment (recommended):**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install pytest
```

## Running Tests

### Run All Tests
```bash
pytest test_price.py -v
```

### Run Specific Test Classes
```bash
# Happy path tests only
pytest test_price.py::TestHappyPath -v

# Permanent failure tests
pytest test_price.py::TestPermanentFailures -v

# Transient failure tests
pytest test_price.py::TestTransientFailures -v

# Edge cases
pytest test_price.py::TestEdgeCases -v
```

### Run with Coverage
```bash
pytest test_price.py --cov=price_client --cov=exceptions --cov-report=html
```

### Run with JUnit XML (for CI)
```bash
pytest test_price.py -v --junit-xml=test-results.xml
```

### Test Quality Gate Script
```bash
python .github/scripts/quality_gate.py test-results.xml
```

### Expected Output
```
test_price.py::TestHappyPath::test_successful_price_fetch_with_valid_ticker PASSED
test_price.py::TestPermanentFailures::test_invalid_api_key PASSED
test_price.py::TestTransientFailures::test_network_error_with_successful_retry PASSED
...
========================= XX passed in X.XXs =========================
```

## Design Decisions & Reasoning

### 1. Exception Hierarchy

**Decision:** Create distinct exception types for transient vs. permanent errors.

**Reasoning:**
- **Clarity:** Immediately obvious which errors should retry
- **Maintainability:** Easy to add new error types
- **Testability:** Clear assertions on error types
- **Real-world alignment:** Mirrors actual API error patterns

### 2. Retry Logic

**Decision:** Only retry transient errors (network, rate limits), not permanent errors (auth, validation).

**Reasoning:**
- **Efficiency:** Permanent errors (invalid API key) will never resolve with retries
- **Cost:** Each API call may cost money; don't waste retries on unrecoverable errors
- **User experience:** Fail fast on permanent errors so users can fix them immediately
- **Resource utilization:** Network issues and rate limits often resolve in seconds

**Example:**
```python
# This SHOULD retry (transient)
NetworkError("Connection timeout")  # May work on retry #2

# This SHOULD NOT retry (permanent)
AuthenticationError("Invalid API key")  # Will never work without new key
```

### 3. Mock API Realism

**Decision:** Include random failures (10% chance) in mock API.

**Reasoning:**
- **Real-world testing:** Actual APIs have intermittent failures
- **Stress testing:** Validates retry logic under pressure
- **Confidence:** Tests that pass with random failures are more robust
- **Documentation:** Shows stakeholders what real usage looks like

### 4. Test Organization

**Decision:** Organize tests by failure category (happy path, permanent, transient, edge cases).

**Reasoning:**
- **Clarity:** Easy to find and understand related tests
- **Documentation:** Test organization serves as system documentation
- **Maintenance:** Clear where to add new tests
- **Selective running:** Can run just one category during development

### 5. Assertion Strategy

**Decision:** Assert on both return values AND mock call counts.

**Reasoning:**
- **Validation:** Ensures correct result is returned
- **Behavior verification:** Confirms retry logic executes correctly
- **Debugging:** Call counts immediately reveal retry issues
- **Regression prevention:** Catches unintended retry behavior changes

**Example:**
```python
# Permanent error should only call API once
assert mock_api.call_count == 1  # Critical for permanent errors!

# Transient error should retry
assert mock_api.call_count == 3  # Confirms retry logic
```

## Test Coverage Highlights

### Critical Test Cases

1. **Permanent Error - No Retry (Most Important)**
```python
def test_invalid_api_key(self):
    # CRITICAL: Should only call API once
    assert mock_api.call_count == 1  # ← KEY ASSERTION
```

2. **Transient Error - With Retry**
```python
def test_network_error_with_successful_retry(self):
    # Should retry and succeed
    assert price == 175.50
    assert mock_api.call_count == 2  # ← Confirms retry happened
```

3. **Mixed Scenario**
```python
def test_permanent_error_after_transient_errors(self):
    # Should stop retrying when hitting permanent error
    assert mock_api.call_count == 2  # ← Validates smart retry logic
```

## Real-World Applicability

This solution addresses common production scenarios:

### Scenario 1: Rate Limiting
**Problem:** API returns 429 Too Many Requests
**Solution:** `RateLimitError` triggers retry, often succeeds after brief wait
**Test:** `test_rate_limit_with_successful_retry`

### Scenario 2: Network Hiccup
**Problem:** Temporary connection timeout
**Solution:** `NetworkError` triggers retry, usually succeeds
**Test:** `test_network_error_with_successful_retry`

### Scenario 3: Bad Configuration
**Problem:** Developer uses wrong API key
**Solution:** `AuthenticationError` fails immediately with clear message
**Test:** `test_invalid_api_key` (confirms NO retry)

### Scenario 4: Invalid User Input
**Problem:** User enters "XYZ123" as ticker
**Solution:** `ValidationError` fails fast, user can correct immediately
**Test:** `test_invalid_ticker_format` (confirms NO retry)

## Performance Considerations

- **Fast Failure:** Permanent errors fail in < 100ms (no retry delay)
- **Retry Efficiency:** Transient retries use exponential backoff (if implemented)
- **Test Speed:** Full test suite runs in < 5 seconds
- **Mock Speed:** No actual network calls = instant tests

## Future Enhancements

1. **Exponential Backoff:** Add increasing delays between retries
2. **Circuit Breaker:** Stop retrying after consecutive failures
3. **Caching:** Cache successful price fetches to reduce API calls
4. **Metrics:** Track retry rates and failure patterns
5. **Async Support:** Add async/await for concurrent requests
6. **Real API Testing:** Integration tests against staging API

## Troubleshooting

### Tests Failing Due to Random Failures

**Problem:** Mock API has 10% random failure rate
**Solution:** Tests mock the API to control randomness. If seeing intermittent failures, check that mocking is applied correctly.

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'pytest'`
**Solution:** Run `pip install pytest`

### Wrong Python Version

**Problem:** Tests fail with syntax errors
**Solution:** Ensure Python 3.8+ is installed: `python --version`

## Contributing

This is a take-home assignment, but feedback is welcome! Key areas for improvement:
- Additional edge cases
- Performance optimizations
- More realistic API simulations

## License

This project is for demonstration purposes as part of a QA Engineer assessment.

## Contact

For questions about this implementation, please reach out through the appropriate channels.

---
