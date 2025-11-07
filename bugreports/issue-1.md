# Issue #1: Upstream Response Times Are Underreported

**Author:** joosep-wm (Joosep Simm)
**Created:** 2025-11-06T17:29:39Z
**State:** OPEN
**URL:** https://github.com/Plepic-OU/claude-logiq/issues/1

---

## Problem Description

When analyzing NGINX Plus logs with decimal response times, the tool consistently **underreports** timing metrics. Response times are truncated (rounded down) instead of being rounded to the nearest millisecond, leading to inaccurate performance data.

---

## How to Reproduce

### Step 1: Create Sample Log File

Save the following as `sample-bug-logs.txt`:

```json
{"timestamp":1446249500322,"stream":{"upstreams":{"api-backend":{"peers":[{"id":0,"server":"10.0.0.1:8080","response_time":2.8}]}}}}
{"timestamp":1446249501322,"stream":{"upstreams":{"api-backend":{"peers":[{"id":0,"server":"10.0.0.1:8080","response_time":3.7}]}}}}
{"timestamp":1446249502322,"stream":{"upstreams":{"api-backend":{"peers":[{"id":0,"server":"10.0.0.1:8080","response_time":4.6}]}}}}
{"timestamp":1446249503322,"stream":{"upstreams":{"api-backend":{"peers":[{"id":0,"server":"10.0.0.1:8080","response_time":5.5}]}}}}
```

**Actual response times:** 2.8ms, 3.7ms, 4.6ms, 5.5ms

### Step 2: Run the Tool

```bash
uv run claude-logiq sample-bug-logs.txt --period PT5S
```

### Step 3: Observe the Incorrect Output

```
Time Bucket: 2015-10-31T01:58:20 - 2015-10-31T01:58:25
  Response Time:
    Min: 2ms        ← WRONG: should be 3ms (rounded from 2.8)
    Max: 5ms        ← WRONG: should be 6ms (rounded from 5.5)
    Avg: 3.50ms     ← WRONG: should be 4.50ms
    P5:  2.00ms
    P95: 4.00ms
    Count: 4 samples
```

---

## Expected vs Actual Results

| Metric | Input Values | Expected (Rounded) | Actual (Truncated) | Error |
|--------|-------------|-------------------|-------------------|-------|
| Min    | 2.8ms       | 3ms              | 2ms              | -33%  |
| Max    | 5.5ms       | 6ms              | 5ms              | -17%  |
| Avg    | 2.8, 3.7, 4.6, 5.5 | 4.50ms   | 3.50ms           | -22%  |

---

## Impact

### Data Accuracy
- **Systematic underestimation** of all timing metrics
- Average response time is underreported by ~22% in this example
- Percentiles (P95/P99) are also affected

### Business Impact
- **False sense of good performance**: Systems appear faster than they actually are
- **Misleading SLA reports**: May show compliance when actually violating SLAs
- **Incorrect capacity planning**: Based on artificially low timing data

### Example
If your actual P95 response time is 99.7ms (close to 100ms SLA), the tool will report it as 99ms, hiding a potential SLA violation.

## Notes

- This bug affects ALL timing metrics: min, max, mean, median, and percentiles
- The issue exists for all upstream pools analyzed by the tool
- The magnitude of error depends on the decimal values in your log data
- In datasets with many `.5` to `.9` decimal values, the error can be significant

---

## Root Cause Analysis

### Summary
The tool underreports upstream response times by **truncating** decimal millisecond values instead of **rounding** them to the nearest millisecond. This systematic underestimation affects all timing metrics (connect_time, first_byte_time, response_time) and leads to inaccurate performance data.

### Root Cause Location
**File:** `src/claude_logiq/log_parser.py:171`

**Problematic Code:**
```python
def _extract_timing_metric(self, peer_data: dict, metric_name: str) -> Optional[int]:
    value = peer_data.get(metric_name)

    if value is None:
        return None

    # Handle different data types
    if isinstance(value, (int, float)):
        # Convert to int (milliseconds)
        return int(value) if value >= 0 else None  # ← BUG HERE: Line 171

    return None
```

**The Problem:** Python's `int()` function performs **truncation** (floor operation) on positive floating-point numbers, not rounding:
- `int(2.8)` returns `2` (truncated) instead of `3` (rounded)
- `int(3.7)` returns `3` (truncated) instead of `4` (rounded)
- `int(5.5)` returns `5` (truncated) instead of `6` (rounded)

### Fix Applied
**Change:** Replace `int(value)` with `round(value)` in `src/claude_logiq/log_parser.py:171`

**Before:**
```python
return int(value) if value >= 0 else None
```

**After:**
```python
return round(value) if value >= 0 else None
```

### Test Coverage
Created comprehensive test suite at `tests/test_decimal_response_time_bug.py` with 4 test cases:
1. `test_decimal_response_time_rounding` - Core truncation vs rounding issue
2. `test_decimal_response_time_edge_cases` - Various decimal edge cases
3. `test_all_timing_metrics_decimal_rounding` - Verifies fix for all three metrics
4. `test_issue_1_reproduction` - Full end-to-end reproduction

All tests initially failed (demonstrating the bug), and now pass after the fix.
