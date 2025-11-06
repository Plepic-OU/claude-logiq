# Bug Report #1: Upstream Response Times Are Underreported

**Issue Link:** https://github.com/Plepic-OU/claude-logiq/issues/1
**Reported by:** joosep-wm
**Date:** November 6, 2025

## Summary
The claude-logiq tool systematically underreports timing metrics when analyzing NGINX Plus logs containing decimal response times. Values are truncated rather than rounded to the nearest millisecond.

## Core Problem
Response times with decimal values are being converted using truncation (floor operation) instead of proper rounding, causing significant measurement errors across all timing statistics.

## Reproduction Steps

**Test Data:** Five JSON log entries with response times: 1.9ms, 2.8ms, 3.7ms, 4.6ms, 5.5ms

**Command:** `uv run claude-logiq sample-bug-logs.txt --period PT5S`

## Reported Discrepancies

| Metric | Input | Expected | Actual | Error |
|--------|-------|----------|--------|-------|
| Minimum | 2.8ms | 3ms | 2ms | -33% |
| Maximum | 5.5ms | 6ms | 5ms | -17% |
| Average | 2.8–5.5ms | 4.50ms | 3.50ms | -22% |

## Impact Assessment

**Data Integrity Issues:**
- Affects minimum, maximum, mean, median, and percentile calculations
- Magnitude varies based on decimal precision in source logs

**Operational Consequences:**
- Performance appears better than actual conditions
- SLA compliance reports may show false positives when violations exist
- Capacity planning becomes unreliable with artificially low metrics

**Real-World Example:** A P95 response time of 99.7ms near a 100ms SLA threshold gets reported as 99ms, masking actual violations.

## Root Cause Analysis

### Location
**File:** `/src/claude_logiq/log_parser.py`
**Function:** `_extract_timing_metric()`
**Line:** 171

### Technical Explanation

The bug occurs in the `_extract_timing_metric()` method of the `LogParser` class. When converting floating-point timing values from the JSON log data to integers (milliseconds), the code uses Python's `int()` constructor:

```python
def _extract_timing_metric(self, peer_data: dict, metric_name: str) -> Optional[int]:
    value = peer_data.get(metric_name)

    if value is None:
        return None

    if isinstance(value, (int, float)):
        # BUG: int(value) truncates decimals instead of rounding
        return int(value) if value >= 0 else None

    return None
```

**The Problem:**
Python's `int()` function performs truncation (floor operation) toward zero, not rounding:
- `int(1.9)` returns `1` (truncated) instead of `2` (rounded)
- `int(2.8)` returns `2` (truncated) instead of `3` (rounded)
- `int(5.5)` returns `5` (truncated) instead of `6` (rounded)

This truncation systematically underreports all timing metrics by discarding the fractional component, leading to artificially lower values across all statistics (min, max, mean, median, percentiles).

### Why This Matters

NGINX Plus logs can contain timing values with decimal precision (e.g., 1.9ms, 2.8ms). When these values are truncated instead of rounded:

1. **Statistical Bias:** All metrics are biased downward, making performance appear better than reality
2. **SLA Compliance:** Response times near thresholds (e.g., 99.7ms near 100ms SLA) falsely appear compliant
3. **Magnitude of Error:** Values with high decimal components (e.g., 1.9ms) can lose nearly 50% of their value
4. **Affects All Metrics:** The bug impacts connect_time, first_byte_time, and response_time

### Failing Test

A comprehensive failing test has been created at:
**`/tests/test_rounding_bug.py`**

The test demonstrates:
1. Five response times (1.9ms, 2.8ms, 3.7ms, 4.6ms, 5.5ms) are truncated to (1ms, 2ms, 3ms, 4ms, 5ms)
2. Expected rounded values should be (2ms, 3ms, 4ms, 5ms, 6ms)
3. All three timing metric types (connect_time, first_byte_time, response_time) exhibit the same truncation behavior

Test execution:
```bash
uv run pytest tests/test_rounding_bug.py -v
```

Test results confirm the bug:
- `test_decimal_response_times_should_round_not_truncate`: FAILED
- `test_decimal_timing_metrics_all_types`: FAILED

### Reproduction Example

Given a log entry with `response_time: 1.9`:
```json
{
  "timestamp": 1446249499000,
  "stream": {
    "upstreams": {
      "test_pool": {
        "peers": [{"server": "10.0.0.1:8080", "response_time": 1.9}]
      }
    }
  }
}
```

**Current behavior:** Parsed as `response_time = 1` (truncated)
**Expected behavior:** Should be parsed as `response_time = 2` (rounded)

## Recommended Fix Approach

### Solution
Replace `int(value)` with `round(value)` in the `_extract_timing_metric()` method at line 171 of `/src/claude_logiq/log_parser.py`.

### Implementation Guidance
The fix is a one-line change:

**Current (buggy) code:**
```python
return int(value) if value >= 0 else None
```

**Fixed code:**
```python
return round(value) if value >= 0 else None
```

### Considerations
1. **Python's round() behavior:** Python 3 uses "banker's rounding" (round half to even) for values exactly at 0.5. For example:
   - `round(2.5)` returns `2` (rounds to even)
   - `round(3.5)` returns `4` (rounds to even)
   - This is generally acceptable for timing metrics and reduces systematic bias

2. **Alternative approach:** If strict "round half up" behavior is required, use:
   ```python
   return int(value + 0.5) if value >= 0 else None
   ```

3. **Impact:** This change affects all timing metrics (connect_time, first_byte_time, response_time) consistently

4. **Test validation:** After implementing the fix, run the failing test to verify:
   ```bash
   uv run pytest tests/test_rounding_bug.py -v
   ```
   All tests should pass after the fix.

5. **Regression testing:** Ensure existing tests still pass:
   ```bash
   uv run pytest tests/test_log_parser.py -v
   ```

### Expected Outcomes After Fix
- Response times will accurately reflect source data with proper rounding
- Statistical metrics (min, max, mean, percentiles) will be more accurate
- SLA compliance reporting will correctly identify threshold violations
- No performance impact (round() is as fast as int() for small values)
