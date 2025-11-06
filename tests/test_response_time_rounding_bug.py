"""
Failing test for Issue #1: Upstream Response Times Are Underreported

This test demonstrates the bug where response times with decimal values are
truncated instead of rounded, causing systematic underreporting of metrics.

Bug location: src/claude_logiq/log_parser.py, line 171
The _extract_timing_metric() method uses int(value) which truncates decimals
instead of round(value) which rounds to the nearest integer.

Expected behavior: 2.8ms should be stored as 3ms (rounded)
Actual behavior: 2.8ms is stored as 2ms (truncated)
"""

import json
import pytest

from claude_logiq.log_parser import LogParser
from claude_logiq.time_aggregator import TimeAggregator


class TestResponseTimeRoundingBug:
    """Tests for Issue #1: Response time decimal truncation bug."""

    def test_decimal_response_times_should_be_rounded_not_truncated(self):
        """
        Test that response times with decimals are properly rounded.

        This test reproduces the exact scenario from Issue #1 where response
        times like 2.8ms and 5.5ms are being truncated to 2ms and 5ms instead
        of being rounded to 3ms and 6ms.
        """
        parser = LogParser()

        # Test individual decimal values that should be rounded up
        test_cases = [
            (2.8, 3, "2.8ms should round to 3ms"),
            (5.5, 6, "5.5ms should round to 6ms"),
            (99.7, 100, "99.7ms should round to 100ms"),
            (1.5, 2, "1.5ms should round to 2ms"),
            (0.6, 1, "0.6ms should round to 1ms"),
        ]

        for input_value, expected_output, message in test_cases:
            peer_data = {"response_time": input_value}
            result = parser._extract_timing_metric(peer_data, "response_time")
            assert result == expected_output, f"{message}, but got {result}"

    def test_all_timing_metrics_affected_by_truncation_bug(self):
        """
        Test that all three timing metrics are affected by the truncation bug.

        This verifies that connect_time, first_byte_time, and response_time
        all suffer from the same truncation issue.
        """
        parser = LogParser()
        peer_data = {
            "connect_time": 1.9,
            "first_byte_time": 3.7,
            "response_time": 5.5,
        }

        # All should be rounded, not truncated
        assert parser._extract_timing_metric(peer_data, "connect_time") == 2
        assert parser._extract_timing_metric(peer_data, "first_byte_time") == 4
        assert parser._extract_timing_metric(peer_data, "response_time") == 6

    def test_bug_report_scenario_with_aggregation(self, tmp_path):
        """
        Test the exact scenario from the bug report with time aggregation.

        This reproduces the bug report where input values [2.8, 3.7, 4.6, 5.5]
        are truncated to [2, 3, 4, 5] resulting in incorrect statistics.

        Expected behavior:
        - Min: 3ms (rounded from 2.8)
        - Max: 6ms (rounded from 5.5)
        - Avg: 4.50ms (average of [3, 4, 5, 6])

        Actual behavior (bug):
        - Min: 2ms (truncated from 2.8)
        - Max: 5ms (truncated from 5.5)
        - Avg: 3.50ms (average of [2, 3, 4, 5])
        """
        # Create log entries matching the bug report
        log_entries = [
            {
                "timestamp": 1446249499322,
                "stream": {
                    "upstreams": {
                        "api-backend": {
                            "peers": [
                                {
                                    "id": 0,
                                    "server": "10.0.0.1:8080",
                                    "response_time": 1.9,
                                }
                            ]
                        }
                    }
                },
            },
            {
                "timestamp": 1446249500322,
                "stream": {
                    "upstreams": {
                        "api-backend": {
                            "peers": [
                                {
                                    "id": 0,
                                    "server": "10.0.0.1:8080",
                                    "response_time": 2.8,
                                }
                            ]
                        }
                    }
                },
            },
            {
                "timestamp": 1446249501322,
                "stream": {
                    "upstreams": {
                        "api-backend": {
                            "peers": [
                                {
                                    "id": 0,
                                    "server": "10.0.0.1:8080",
                                    "response_time": 3.7,
                                }
                            ]
                        }
                    }
                },
            },
            {
                "timestamp": 1446249502322,
                "stream": {
                    "upstreams": {
                        "api-backend": {
                            "peers": [
                                {
                                    "id": 0,
                                    "server": "10.0.0.1:8080",
                                    "response_time": 4.6,
                                }
                            ]
                        }
                    }
                },
            },
            {
                "timestamp": 1446249503322,
                "stream": {
                    "upstreams": {
                        "api-backend": {
                            "peers": [
                                {
                                    "id": 0,
                                    "server": "10.0.0.1:8080",
                                    "response_time": 5.5,
                                }
                            ]
                        }
                    }
                },
            },
        ]

        # Write log file
        log_file = tmp_path / "bug_report_test.log"
        log_file.write_text("\n".join(json.dumps(entry) for entry in log_entries))

        # Parse log file
        parser = LogParser()
        parsed_entries = list(parser.parse_log_file(str(log_file)))

        # Aggregate with 5-second buckets (all entries in same bucket)
        aggregator = TimeAggregator(5.0)
        buckets = aggregator.aggregate_metrics(parsed_entries)

        # Should have one bucket with one pool
        assert len(buckets) == 1
        bucket = buckets[0]
        assert bucket.pool_name == "api-backend"

        # Verify response time statistics
        # Note: First value (1.9 -> 2) is excluded from analysis in the bug report
        # The bug report focuses on [2.8, 3.7, 4.6, 5.5] which should become [3, 4, 5, 6]
        stats = bucket.response_time_stats
        assert stats is not None

        # With proper rounding, we expect:
        # Values: [2, 3, 4, 5, 6] (rounded from [1.9, 2.8, 3.7, 4.6, 5.5])
        # Min: 2, Max: 6, Avg: 4.0

        # Check min value (2.8 should round to 3, but 1.9 rounds to 2)
        # Since 1.9 is included, min should be 2
        assert stats.min_value == 2, f"Min should be 2 (from 1.9), got {stats.min_value}"

        # Check max value (5.5 should round to 6)
        assert (
            stats.max_value == 6
        ), f"Max should be 6 (rounded from 5.5), got {stats.max_value}"

        # Check average (should be 4.0 from [2, 3, 4, 5, 6])
        expected_avg = 4.0
        assert (
            abs(stats.avg_value - expected_avg) < 0.01
        ), f"Avg should be {expected_avg}, got {stats.avg_value}"

        # Check count
        assert stats.count == 5, f"Should have 5 samples, got {stats.count}"

    def test_edge_case_half_values_use_bankers_rounding(self):
        """
        Test that .5 values use banker's rounding (round half to even).

        Python's round() function uses "round half to even" which means:
        - 0.5 rounds to 0 (even)
        - 1.5 rounds to 2 (even)
        - 2.5 rounds to 2 (even)
        - 3.5 rounds to 4 (even)

        This is the expected behavior for the fix.
        """
        parser = LogParser()

        test_cases = [
            (0.5, 0, "0.5 should round to 0 (banker's rounding)"),
            (1.5, 2, "1.5 should round to 2 (banker's rounding)"),
            (2.5, 2, "2.5 should round to 2 (banker's rounding)"),
            (3.5, 4, "3.5 should round to 4 (banker's rounding)"),
            (4.5, 4, "4.5 should round to 4 (banker's rounding)"),
            (5.5, 6, "5.5 should round to 6 (banker's rounding)"),
        ]

        for input_value, expected_output, message in test_cases:
            peer_data = {"response_time": input_value}
            result = parser._extract_timing_metric(peer_data, "response_time")
            assert result == expected_output, f"{message}, but got {result}"

    def test_integer_values_unaffected(self):
        """
        Test that integer values are not affected by the rounding fix.

        This ensures the fix doesn't break existing functionality for integer inputs.
        """
        parser = LogParser()

        test_cases = [
            (0, 0),
            (1, 1),
            (5, 5),
            (10, 10),
            (100, 100),
            (999, 999),
        ]

        for input_value, expected_output in test_cases:
            peer_data = {"response_time": input_value}
            result = parser._extract_timing_metric(peer_data, "response_time")
            assert (
                result == expected_output
            ), f"Integer {input_value} should remain {expected_output}, got {result}"
