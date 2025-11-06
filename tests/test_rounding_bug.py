"""
Test for decimal rounding bug in upstream response times.

This test demonstrates that decimal response times are being truncated
instead of rounded to the nearest millisecond, causing underreporting
of timing metrics.

Bug report: https://github.com/Plepic-OU/claude-logiq/issues/1
"""

import json
import pytest
from claude_logiq.log_parser import LogParser


class TestDecimalRoundingBug:
    """Test cases demonstrating the decimal truncation bug."""

    def test_decimal_response_times_should_round_not_truncate(self):
        """
        Test that decimal response times are properly rounded, not truncated.

        This test uses response times with decimal values that should round up:
        - 1.9ms should become 2ms (not 1ms)
        - 2.8ms should become 3ms (not 2ms)
        - 3.7ms should become 4ms (not 3ms)
        - 4.6ms should become 5ms (not 4ms)
        - 5.5ms should become 6ms (not 5ms)

        Current behavior: int(value) truncates decimals (floor operation)
        Expected behavior: round(value) rounds to nearest integer
        """
        parser = LogParser()

        # Create log entries with decimal response times
        log_lines = [
            {
                "timestamp": 1446249499000,
                "stream": {
                    "upstreams": {
                        "test_pool": {
                            "peers": [
                                {
                                    "server": "10.0.0.1:8080",
                                    "response_time": 1.9  # Should round to 2, not truncate to 1
                                }
                            ]
                        }
                    }
                }
            },
            {
                "timestamp": 1446249499100,
                "stream": {
                    "upstreams": {
                        "test_pool": {
                            "peers": [
                                {
                                    "server": "10.0.0.1:8080",
                                    "response_time": 2.8  # Should round to 3, not truncate to 2
                                }
                            ]
                        }
                    }
                }
            },
            {
                "timestamp": 1446249499200,
                "stream": {
                    "upstreams": {
                        "test_pool": {
                            "peers": [
                                {
                                    "server": "10.0.0.1:8080",
                                    "response_time": 3.7  # Should round to 4, not truncate to 3
                                }
                            ]
                        }
                    }
                }
            },
            {
                "timestamp": 1446249499300,
                "stream": {
                    "upstreams": {
                        "test_pool": {
                            "peers": [
                                {
                                    "server": "10.0.0.1:8080",
                                    "response_time": 4.6  # Should round to 5, not truncate to 4
                                }
                            ]
                        }
                    }
                }
            },
            {
                "timestamp": 1446249499400,
                "stream": {
                    "upstreams": {
                        "test_pool": {
                            "peers": [
                                {
                                    "server": "10.0.0.1:8080",
                                    "response_time": 5.5  # Should round to 6, not truncate to 5
                                }
                            ]
                        }
                    }
                }
            }
        ]

        # Parse the log entries
        entries = []
        for log_data in log_lines:
            log_line = json.dumps(log_data)
            entry = parser._parse_log_line(log_line)
            if entry:
                entries.append(entry)

        # Verify all entries were parsed
        assert len(entries) == 5, "All 5 log entries should be parsed"

        # Extract the response times that were parsed
        response_times = [
            entry.upstream_metrics[0].response_time
            for entry in entries
            if entry.upstream_metrics[0].response_time is not None
        ]

        # These are the EXPECTED values after proper rounding
        expected_rounded = [2, 3, 4, 5, 6]

        # These are the ACTUAL values being produced (truncated)
        actual_truncated = [1, 2, 3, 4, 5]

        # Test will FAIL because values are truncated instead of rounded
        assert response_times == expected_rounded, (
            f"Response times should be rounded, not truncated. "
            f"Expected {expected_rounded}, got {response_times}"
        )

    def test_decimal_timing_metrics_all_types(self):
        """
        Test that all timing metric types (connect, first_byte, response) are properly rounded.

        This ensures the bug affects all timing metrics, not just response_time.
        """
        parser = LogParser()

        log_data = {
            "timestamp": 1446249499000,
            "stream": {
                "upstreams": {
                    "test_pool": {
                        "peers": [
                            {
                                "server": "10.0.0.1:8080",
                                "connect_time": 1.7,      # Should round to 2, not truncate to 1
                                "first_byte_time": 2.9,   # Should round to 3, not truncate to 2
                                "response_time": 4.6      # Should round to 5, not truncate to 4
                            }
                        ]
                    }
                }
            }
        }

        entry = parser._parse_log_line(json.dumps(log_data))
        assert entry is not None

        metric = entry.upstream_metrics[0]

        # Expected values after proper rounding
        assert metric.connect_time == 2, (
            f"connect_time 1.7 should round to 2, got {metric.connect_time}"
        )
        assert metric.first_byte_time == 3, (
            f"first_byte_time 2.9 should round to 3, got {metric.first_byte_time}"
        )
        assert metric.response_time == 5, (
            f"response_time 4.6 should round to 5, got {metric.response_time}"
        )

    def test_decimal_edge_case_exactly_half(self):
        """
        Test rounding behavior for values exactly at 0.5.

        Python's round() uses "banker's rounding" (round half to even),
        but for timing metrics, we should use standard rounding (round half up).
        """
        parser = LogParser()

        log_data = {
            "timestamp": 1446249499000,
            "stream": {
                "upstreams": {
                    "test_pool": {
                        "peers": [
                            {
                                "server": "10.0.0.1:8080",
                                "response_time": 2.5  # Standard rounding: should be 3 (or 2 with banker's)
                            }
                        ]
                    }
                }
            }
        }

        entry = parser._parse_log_line(json.dumps(log_data))
        assert entry is not None

        metric = entry.upstream_metrics[0]

        # With proper rounding (banker's or standard), should be 2 or 3
        # Current truncation produces 2, but for wrong reason
        # This test documents the edge case behavior
        assert metric.response_time in [2, 3], (
            f"response_time 2.5 should round to 2 or 3, got {metric.response_time}"
        )
