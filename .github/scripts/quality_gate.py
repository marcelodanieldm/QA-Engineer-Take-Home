#!/usr/bin/env python3
"""
Quality Gate Script for CI/CD Pipeline

This script parses JUnit XML test results and applies quality gates based on test severity:
- Critical/High severity failures → FAIL the build (block PR merge)
- Low severity failures → PASS with warning (allow PR merge with annotation)
"""

import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple

# Define severity mapping based on test names/docstrings
SEVERITY_MAPPING = {
    # Critical severity - Block merge
    'test_api_down_500_critical_failure': 'Critical',
    'test_bad_data_critical_cases': 'Critical',
    
    # High severity - Block merge
    'test_rate_limit_429_fail_fast': 'High',
    'test_rate_limit_429_no_retry_after': 'High',
    
    # Low severity - Warning only
    'test_normal_case_200_ok': 'Low',
    'test_api_down_500_retry_success': 'Low',
}

def get_test_severity(test_name: str) -> str:
    """
    Determine the severity level of a test based on its name.
    Default to 'High' if not explicitly mapped.
    """
    for pattern, severity in SEVERITY_MAPPING.items():
        if pattern in test_name:
            return severity
    return 'High'  # Default to High for safety

def parse_junit_xml(xml_file: str) -> Tuple[List[Dict], Dict[str, int]]:
    """
    Parse JUnit XML file and extract test results.
    
    Returns:
        - List of failed tests with severity
        - Summary statistics
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    failed_tests = []
    stats = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'critical_failed': 0,
        'high_failed': 0,
        'low_failed': 0
    }
    
    # Parse testsuite(s)
    testsuites = root.findall('.//testsuite')
    if not testsuites:
        testsuites = [root] if root.tag == 'testsuite' else []
    
    for testsuite in testsuites:
        for testcase in testsuite.findall('testcase'):
            test_name = testcase.get('name', '')
            classname = testcase.get('classname', '')
            
            stats['total'] += 1
            
            # Check if test failed
            failure = testcase.find('failure')
            error = testcase.find('error')
            
            if failure is not None or error is not None:
                severity = get_test_severity(test_name)
                failure_message = failure.get('message', '') if failure is not None else error.get('message', '')
                
                failed_tests.append({
                    'name': test_name,
                    'classname': classname,
                    'severity': severity,
                    'message': failure_message
                })
                
                stats['failed'] += 1
                if severity == 'Critical':
                    stats['critical_failed'] += 1
                elif severity == 'High':
                    stats['high_failed'] += 1
                elif severity == 'Low':
                    stats['low_failed'] += 1
            else:
                stats['passed'] += 1
    
    return failed_tests, stats

def apply_quality_gate(failed_tests: List[Dict], stats: Dict[str, int]) -> int:
    """
    Apply quality gate rules:
    - Critical or High failures → Exit code 1 (FAIL)
    - Only Low failures → Exit code 0 (PASS with warning)
    - All passed → Exit code 0 (PASS)
    
    Returns exit code for the CI job.
    """
    print("\n" + "="*70)
    print("QUALITY GATE ANALYSIS")
    print("="*70)
    
    print(f"\nTest Summary:")
    print(f"  Total Tests: {stats['total']}")
    print(f"  Passed: {stats['passed']}")
    print(f"  Failed: {stats['failed']}")
    
    if stats['failed'] == 0:
        print("\n✅ ALL TESTS PASSED - Quality Gate: PASS")
        write_summary("✅ All tests passed", stats, failed_tests)
        return 0
    
    print(f"\nFailure Breakdown by Severity:")
    print(f"  🔴 Critical: {stats['critical_failed']}")
    print(f"  🟠 High: {stats['high_failed']}")
    print(f"  🟡 Low: {stats['low_failed']}")
    
    # Check for Critical or High severity failures
    if stats['critical_failed'] > 0 or stats['high_failed'] > 0:
        print("\n❌ QUALITY GATE: FAILED")
        print("🚫 PR merge blocked due to Critical/High severity test failures")
        print("\nFailed Tests (blocking):")
        for test in failed_tests:
            if test['severity'] in ['Critical', 'High']:
                print(f"  - [{test['severity']}] {test['name']}")
                print(f"    Message: {test['message'][:100]}")
        
        write_summary("❌ Quality Gate FAILED - PR blocked", stats, failed_tests)
        return 1
    
    # Only Low severity failures
    if stats['low_failed'] > 0:
        print("\n⚠️  QUALITY GATE: PASSED WITH WARNINGS")
        print("✅ PR merge allowed (only low-severity failures)")
        print("⚠️  Manual review recommended for:")
        for test in failed_tests:
            if test['severity'] == 'Low':
                print(f"  - [{test['severity']}] {test['name']}")
        
        write_summary("⚠️  Quality Gate PASSED with warnings", stats, failed_tests)
        return 0
    
    return 0

def write_summary(status: str, stats: Dict[str, int], failed_tests: List[Dict]):
    """Write a markdown summary for PR comments."""
    summary = f"""## Test Results Summary

**Status:** {status}

### Statistics
- **Total Tests:** {stats['total']}
- **Passed:** {stats['passed']}
- **Failed:** {stats['failed']}

### Failure Severity Breakdown
- **Critical:** {stats['critical_failed']}
- **High:** {stats['high_failed']}
- **Low:** {stats['low_failed']}

"""
    
    if failed_tests:
        summary += "\n### Failed Tests\n\n"
        for test in failed_tests:
            summary += f"- **[{test['severity']}]** `{test['name']}`\n"
        
        # Add quality gate decision
        if stats['critical_failed'] > 0 or stats['high_failed'] > 0:
            summary += "\n### Quality Gate Decision\n"
            summary += "**PR MERGE BLOCKED** - Critical or High severity test failures detected.\n"
            summary += "Please fix these issues before merging.\n"
        else:
            summary += "\n### Quality Gate Decision\n"
            summary += "**PR MERGE ALLOWED** - Only low-severity failures detected.\n"
            summary += "Manual review recommended before merging.\n"
    else:
        summary += "\n### All Tests Passed!\n"
    
    # Write to file for GitHub Actions
    with open('.github/scripts/test-summary.md', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print("\n" + summary)

def main():
    if len(sys.argv) < 2:
        print("Usage: python quality_gate.py <junit-xml-file>")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    
    try:
        failed_tests, stats = parse_junit_xml(xml_file)
        exit_code = apply_quality_gate(failed_tests, stats)
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Error parsing test results: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
