# CI/CD Pipeline with Quality Gates

This project implements a sophisticated CI/CD pipeline with severity-based quality gates to ensure safe continuous deployment while maintaining development velocity.

## Quality Gate Strategy

### Severity Levels

Tests are categorized by severity to determine merge eligibility:

| Severity | Impact | Quality Gate Action | Example Tests |
|----------|--------|---------------------|---------------|
| **Critical** | System failure, data corruption | ❌ **Block PR merge** | `test_api_down_500_critical_failure`, `test_bad_data_critical_cases` |
| **High** | Service degradation, security issues | ❌ **Block PR merge** | `test_rate_limit_429_fail_fast`, `test_rate_limit_429_no_retry_after` |
| **Low** | Minor issues, edge cases | ✅ **Allow merge with warning** | `test_normal_case_200_ok`, `test_api_down_500_retry_success` |

### Quality Gate Rules

1. **Critical/High Severity Failures**
   - ❌ GitHub Actions job **FAILS**
   - 🚫 PR merge is **BLOCKED**
   - 🔔 Team is notified
   - ✋ Must be fixed before merging

2. **Low Severity Failures Only**
   - ✅ GitHub Actions job **PASSES**
   - ⚠️ Warning annotation generated
   - 👀 Manual review recommended
   - ✓ PR can be merged if approved

3. **All Tests Pass**
   - ✅ GitHub Actions job **PASSES**
   - ✓ PR can be merged automatically

## GitHub Actions Workflow

### Pipeline Steps

```yaml
1. Checkout code
2. Set up Python environment
3. Install dependencies (pytest, pytest-mock, requests)
4. Run test suite with JUnit XML output
5. Parse results with quality_gate.py script
6. Apply severity-based quality gates
7. Upload test artifacts
8. Comment PR with detailed summary
```

### Workflow File

`.github/workflows/test.yml` - Main CI pipeline

### Quality Gate Script

`.github/scripts/quality_gate.py` - Python script that:
- Parses JUnit XML test results
- Maps tests to severity levels
- Applies quality gate rules
- Generates detailed reports
- Sets exit codes to control PR merge status

## Usage

### Running Locally

```bash
# Install dependencies
pip install pytest pytest-mock requests

# Run tests
pytest test_price.py -v

# Run tests with JUnit XML (for CI simulation)
pytest test_price.py -v --junit-xml=test-results.xml

# Run quality gate script
python .github/scripts/quality_gate.py test-results.xml
```

### CI/CD Behavior

#### Scenario 1: All Tests Pass
```
✅ All tests passed
✅ Quality Gate: PASS
✅ PR can be merged
```

#### Scenario 2: Critical/High Failure
```
❌ Critical severity failure detected
❌ Quality Gate: FAILED
🚫 PR merge blocked
Action required: Fix failing tests
```

#### Scenario 3: Low Severity Failure Only
```
⚠️  Low severity failure detected
✅ Quality Gate: PASSED with warnings
✅ PR can be merged (manual review recommended)
```

## Customizing Severity Levels

Edit `.github/scripts/quality_gate.py` to modify severity mappings:

```python
SEVERITY_MAPPING = {
    'test_name_pattern': 'Critical',  # Blocks merge
    'another_test': 'High',           # Blocks merge
    'edge_case_test': 'Low',          # Warning only
}
```

## Benefits

### Safety
- ✅ Critical bugs cannot be deployed
- ✅ High-risk changes require fixing before merge
- ✅ Multiple quality checkpoints

### Velocity
- ⚡ Low-risk issues don't block deployments
- ⚡ Teams can move fast on non-critical changes
- ⚡ Manual override available for low-severity issues

### Visibility
- 📊 Clear test result summaries on every PR
- 📈 Severity-based failure metrics
- 🎯 Prioritized failure information

## Extending the Pipeline

### Add More Quality Gates

```python
# Example: Add code coverage gate
def check_coverage_gate(coverage_percent: float) -> bool:
    if coverage_percent < 80:
        print("⚠️  Coverage below 80%")
        return False  # Block if critical
    return True
```

### Add Notifications

```yaml
- name: Notify on Critical Failure
  if: failure()
  uses: slack-notify-action@v1
  with:
    message: "Critical test failure - PR blocked"
```

### Add Performance Testing

```yaml
- name: Run Performance Tests
  run: pytest test_performance.py --benchmark
```

## Best Practices

1. **Keep Critical Tests Focused**
   - Only mark tests as Critical/High if they truly block deployment
   - Most tests should be Low severity

2. **Regular Review**
   - Periodically review severity mappings
   - Update based on production incidents

3. **Clear Documentation**
   - Document why each test has its severity level
   - Maintain test plan with severity justifications

4. **Fast Feedback**
   - Keep test suite execution time under 5 minutes
   - Run critical tests first for quick feedback

## Monitoring & Metrics

Track these metrics in your CI/CD dashboard:
- Pass rate by severity level
- Time to fix Critical/High failures
- Frequency of manual overrides for Low failures
- Overall deployment velocity

## Troubleshooting

### Quality Gate Script Fails
```bash
# Check XML file exists
ls -la test-results.xml

# Validate XML format
python -c "import xml.etree.ElementTree as ET; ET.parse('test-results.xml')"

# Debug script
python .github/scripts/quality_gate.py test-results.xml -v
```

### All Tests Marked as High Severity
- Check `SEVERITY_MAPPING` in `quality_gate.py`
- Unmapped tests default to 'High' for safety
- Add explicit mappings for Low severity tests

## Future Enhancements

- [ ] Integration with Slack/Teams for notifications
- [ ] Automatic severity detection from test docstrings
- [ ] Historical trend analysis
- [ ] Custom severity rules per branch/environment
- [ ] Integration with issue tracking systems
