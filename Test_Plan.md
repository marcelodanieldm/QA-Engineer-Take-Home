# Test Plan: Stock Price API Client

## Executive Summary

This test plan outlines the comprehensive testing strategy for the Stock Price API Client, focusing on reliability, error handling, and retry logic. The plan emphasizes distinguishing between permanent and transient failures to ensure appropriate retry behavior.

## Test Objectives

1. Verify successful price retrieval for valid inputs
2. Ensure permanent failures (authentication, validation, not found) do NOT trigger retries
3. Confirm transient failures (network, rate limits) DO trigger appropriate retries
4. Validate edge cases and boundary conditions
5. Test realistic API failure patterns

## Scope

### In Scope
- Happy path scenarios with valid inputs
- Permanent error handling (authentication, validation, not found)
- Transient error handling with retry logic (network errors, rate limits)
- Edge cases (empty inputs, boundary values, mixed error scenarios)
- Client initialization and configuration
- Return type validation

### Out of Scope
- Actual network calls to real APIs
- Performance/load testing
- Concurrent request handling beyond basic isolation
- Cost analysis of API calls
- Monitoring and alerting

## Test Strategy

### 1. Happy Path Testing
**Priority: HIGH**

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| Valid ticker with valid API key | Fetch price for "AAPL" with valid credentials | Returns float price value |
| Multiple valid tickers | Fetch prices for different valid tickers | Each returns correct price |
| Case insensitivity | Fetch with lowercase ticker "aapl" | Handles case properly |

**Rationale:** Ensures core functionality works as expected before testing failure modes.

---

### 2. Permanent Failure Testing (NO RETRY)
**Priority: CRITICAL**

These errors indicate issues that won't resolve with retries and should fail immediately.

| Test Case | Error Type | Expected Behavior | Retry Count |
|-----------|------------|-------------------|-------------|
| Invalid API key | AuthenticationError | Fail immediately | 1 (no retry) |
| Missing API key | AuthenticationError | Fail immediately | 1 (no retry) |
| Unknown ticker | NotFoundError | Fail immediately | 1 (no retry) |
| Empty ticker | ValidationError | Fail immediately | 1 (no retry) |
| Invalid ticker format | ValidationError | Fail immediately | 1 (no retry) |
| Non-string ticker | ValidationError | Fail immediately | 1 (no retry) |

**Key Assertion:** `mock_api.call_count == 1` confirms no retries occurred.

**Rationale:** Retrying permanent errors wastes resources and delays failure reporting. Authentication and validation errors won't resolve on their own.

---

### 3. Transient Failure Testing (WITH RETRY)
**Priority: CRITICAL**

These errors may resolve with retries and should trigger the retry mechanism.

| Test Case | Error Type | Retry Behavior | Expected Outcome |
|-----------|------------|----------------|------------------|
| Single network timeout | NetworkError | Retry and succeed on attempt 2 | Returns price, 2 calls |
| Multiple rate limits | RateLimitError | Retry twice, succeed on attempt 3 | Returns price, 3 calls |
| Network error exhausts retries | NetworkError | All retries fail | Raises NetworkError, max_retries calls |
| Rate limit exhausts retries | RateLimitError | All retries fail | Raises RateLimitError, max_retries calls |
| Mixed transient errors | Network + RateLimit | Retry through both | Eventually succeeds |

**Key Assertion:** `mock_api.call_count` matches expected retry attempts.

**Rationale:** Network issues and rate limits are temporary. Retrying gives the system time to recover, improving success rates.

---

### 4. Edge Cases & Boundary Conditions
**Priority: MEDIUM**

| Test Case | Description | Purpose |
|-----------|-------------|---------|
| Zero retries (max_retries=1) | No retry on transient error | Validates retry configuration |
| High retry count (max_retries=10) | Multiple retries before success | Validates upper bounds |
| Permanent after transient | Network error → Auth error | Stops retrying on permanent error |
| Maximum ticker length | 5-character ticker | Validates length boundaries |
| Return type validation | Ensure float returned | Type safety |
| Request isolation | Multiple sequential requests | Each request independent |

**Rationale:** Edge cases expose bugs in boundary handling and configuration logic.

---

### 5. Realistic Scenarios
**Priority: MEDIUM**

| Test Case | Description | Real-World Analogy |
|-----------|-------------|-------------------|
| Unmocked API behavior | Test actual mock function | Validates mock realism |
| Batch price fetch | Fetch multiple tickers sequentially | Portfolio pricing |
| Retry with backoff simulation | Rate limit clears after 2 attempts | Real API rate limiting |

**Rationale:** Integration-style tests ensure the system behaves realistically under normal usage patterns.

---

## Test Environment

### Tools & Frameworks
- **Testing Framework:** Pytest
- **Mocking:** unittest.mock (patch, MagicMock)
- **Python Version:** 3.8+
- **Dependencies:** pytest, unittest (standard library)

### Test Data
- **Valid Tickers:** AAPL, GOOGL, MSFT, AMZN, TSLA, META
- **Valid API Key:** "valid_api_key"
- **Invalid Inputs:** Empty strings, numeric values, special characters, excessive length

---

## Critical Decision: Retry vs. No Retry

### Transient Errors (RETRY)
**Why retry?**
- Network timeouts can resolve when server recovers
- Rate limits clear after time window
- Temporary overload conditions pass
- **Expected resolution time:** Seconds to minutes

**Example:** A 429 Rate Limit error might resolve in 1 second. Retrying 3 times with small delays could succeed without user intervention.

### Permanent Errors (NO RETRY)
**Why not retry?**
- Invalid API keys remain invalid
- Nonexistent tickers don't suddenly exist
- Malformed input stays malformed
- **Expected resolution time:** Never (requires user intervention)

**Example:** An invalid API key error will never resolve by retrying. It wastes time and resources. The user must provide a correct key.

---

## Metrics & Success Criteria

### Coverage Metrics
- **Line Coverage:** > 95%
- **Branch Coverage:** > 90%
- **Test Pass Rate:** 100%

### Quality Metrics
- All permanent errors trigger exactly 1 API call
- All transient errors trigger `max_retries` API calls (when exhausted)
- Successful retries trigger `< max_retries` API calls
- Zero false positives (tests fail when they should pass)
- Zero false negatives (tests pass when they should fail)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Mock doesn't reflect real API | Medium | High | Regular validation against real API docs |
| Retry logic causes delays | Low | Medium | Configurable retry count with reasonable defaults |
| False permanent error classification | Low | High | Careful error categorization with documentation |
| Test brittleness from tight coupling | Medium | Medium | Use dependency injection and clear interfaces |

---

## Test Execution

### Running Tests
```bash
# Run all tests
pytest test_price.py -v

# Run specific test class
pytest test_price.py::TestPermanentFailures -v

# Run with coverage
pytest test_price.py --cov=price_client --cov-report=html

# Run only high-priority tests (using markers)
pytest test_price.py -m critical
```

### Expected Results
- All tests should pass in < 5 seconds
- No network calls should be made
- Clear failure messages for any failures

---

## Maintenance & Future Enhancements

### Maintenance Plan
1. **Review quarterly** to align with API changes
2. **Update mocks** when real API behavior changes
3. **Add regression tests** for any bugs found in production
4. **Monitor test execution time** to prevent slowdowns

### Future Enhancements
1. **Parametrized tests** for more ticker combinations
2. **Property-based testing** using Hypothesis
3. **Circuit breaker pattern** testing for cascading failures
4. **Exponential backoff** validation for retry timing
5. **Logging verification** to ensure proper error tracking
6. **Caching tests** if caching is added to client

---

## Conclusion

This test plan provides comprehensive coverage of the Stock Price API Client with emphasis on the critical distinction between permanent and transient failures. The tests ensure that:

1. ✅ Transient errors trigger retries (network, rate limits)
2. ✅ Permanent errors fail fast (auth, validation, not found)
3. ✅ Happy paths work reliably
4. ✅ Edge cases are handled correctly
5. ✅ The system behaves realistically under various conditions

The test suite serves as both validation and documentation, clearly demonstrating the expected behavior of the system under various failure modes.
