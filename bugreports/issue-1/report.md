# Bug Report: Issue #1

**Title:** Upstream Response Times Are Underreported

**Link:** https://github.com/Plepic-OU/claude-logiq/issues/1

---

## Problem Description

When analyzing NGINX Plus logs with decimal response times, the tool consistently **underreports** timing metrics. Response times are truncated (rounded down) instead of being rounded to the nearest millisecond, leading to inaccurate performance data.

---

## How to Reproduce

### Step 1: Create Sample Log File

Save the following as `sample-bug-logs.txt`:

```json
{"timestamp":1446249499322,"stream":{"upstreams":{"api-backend":{"peers":[{"id":0,"server":"10.0.0.1:8080","response_time":1.9}]}}}}
{"timestamp":1446249500322,"stream":{"upstreams":{"api-backend":{"peers":[{"id":0,"server":"10.0.0.1:8080","response_time":2.8}]}}}}
{"timestamp":1446249501322,"stream":{"upstreams":{"api-backend":{"peers":[{"id":0,"server":"10.0.0.1:8080","response_time":3.7}]}}}}
{"timestamp":1446249502322,"stream":{"upstreams":{"api-backend":{"peers":[{"id":0,"server":"10.0.0.1:8080","response_time":4.6}]}}}}
{"timestamp":1446249503322,"stream":{"upstreams":{"api-backend":{"peers":[{"id":0,"server":"10.0.0.1:8080","response_time":5.5}]}}}}
```

**Actual response times:** 1.9ms, 2.8ms, 3.7ms, 4.6ms, 5.5ms

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

### Root Cause

The bug is located in `src/claude_logiq/log_parser.py` at **line 171** in the `_extract_timing_metric()` method.

#### The Problem

The code uses Python's `int()` constructor to convert float values to integers:

```python
def _extract_timing_metric(self, peer_data: dict, metric_name: str) -> Optional[int]:
    value = peer_data.get(metric_name)

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return int(value) if value >= 0 else None  # ← LINE 171: THE BUG

    return None
```

**Python's `int()` function truncates toward zero** (mathematically equivalent to floor for positive numbers), rather than rounding to the nearest integer:

```python
int(2.8)   # Returns 2, not 3
int(5.5)   # Returns 5, not 6
int(99.7)  # Returns 99, not 100
```

#### Why This Matters

Every response time value from the log files goes through this method:
1. Log contains: `{"response_time": 2.8}`
2. Parser converts it to: `2` (truncated)
3. Aggregator calculates statistics using corrupted data
4. Output displays incorrect metrics

The data is corrupted at the **parsing stage** and can never be recovered downstream.

#### Affected Code Paths

The `_extract_timing_metric()` method is called for ALL timing metrics:
- Line 129: `connect_time = self._extract_timing_metric(peer, 'connect_time')`
- Line 130: `first_byte_time = self._extract_timing_metric(peer, 'first_byte_time')`
- Line 131: `response_time = self._extract_timing_metric(peer, 'response_time')`

This means **every single timing value** across all log entries and all upstream pools is affected.

#### Why Tests Didn't Catch It

The existing test file (`tests/test_log_parser.py`, line 152-156) actually **validates the bug** instead of catching it:

```python
def test_extract_timing_metric_valid_values(self):
    """Test extracting valid timing metrics."""
    peer_data = {"connect_time": 10, "first_byte_time": 20.5}

    assert self.parser._extract_timing_metric(peer_data, "connect_time") == 10
    assert self.parser._extract_timing_metric(peer_data, "first_byte_time") == 20  # ← Should be 21
```

The test expects `20.5` to become `20` (truncated), when it should expect `21` (rounded).

### The Fix

Replace line 171 with:
```python
return round(value) if value >= 0 else None
```

Python's `round()` function properly rounds to the nearest integer:
```python
round(2.8)   # Returns 3 ✓
round(5.5)   # Returns 6 ✓
round(99.7)  # Returns 100 ✓
```

This fix:
- ✅ Is backward compatible (integers are unchanged)
- ✅ Requires no API changes
- ✅ Fixes all timing metrics simultaneously
- ✅ Has no performance impact
- ✅ Is a single-line change

### Verification

A comprehensive test suite has been created to verify the fix:
- **Location:** `tests/test_response_time_rounding_bug.py`
- **Tests:** 5 tests covering decimal rounding, all metric types, and edge cases
- **Current Status:** 4 tests failing (demonstrating the bug), 1 passing (integers unaffected)
- **After Fix:** All 5 tests should pass

Run the tests with:
```bash
uv run pytest tests/test_response_time_rounding_bug.py -v
```

### Additional Files

For complete technical details, see:
- **Detailed Analysis:** `bugreports/issue-1/root-cause-analysis.md`
- **Test Suite:** `tests/test_response_time_rounding_bug.py`
- **Quick Summary:** `bugreports/issue-1/summary.md`
