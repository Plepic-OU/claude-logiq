"""
Test case to reproduce Issue #1: Upstream Response Times Are Underreported.

This test demonstrates the bug where decimal response times (e.g., 2.8ms, 3.7ms)
are truncated (rounded down) instead of being rounded to the nearest millisecond.

Bug location: src/claude_logiq/log_parser.py:171
Root cause: int(value) truncates instead of rounding
Expected behavior: round(value) to nearest millisecond
"""

import json
import pytest

from claude_logiq.log_parser import LogParser


class TestDecimalResponseTimeBug:
    """Test cases demonstrating the decimal response time truncation bug."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = LogParser()

    def test_decimal_response_time_rounding(self):
        """
        Test that decimal response times are ROUNDED to nearest millisecond.

        This test currently FAILS because the code uses int() which truncates.

        Input values: 2.8ms, 3.7ms, 4.6ms, 5.5ms
        Expected (rounded): 3ms, 4ms, 5ms, 6ms
        Actual (truncated): 2ms, 3ms, 4ms, 5ms
        """
        test_cases = [
            # (input_value, expected_rounded, actual_truncated)
            (2.8, 3, 2),  # 2.8 should round to 3, not truncate to 2
            (3.7, 4, 3),  # 3.7 should round to 4, not truncate to 3
            (4.6, 5, 4),  # 4.6 should round to 5, not truncate to 4
            (5.5, 6, 5),  # 5.5 should round to 6, not truncate to 5
        ]

        for input_value, expected_rounded, actual_truncated in test_cases:
            peer_data = {"response_time": input_value}

            # This will FAIL until the bug is fixed
            result = self.parser._extract_timing_metric(peer_data, "response_time")

            # Expected behavior: should round to nearest integer
            assert result == expected_rounded, (
                f"Response time {input_value}ms should round to {expected_rounded}ms, "
                f"but got {result}ms (truncated to {actual_truncated}ms)"
            )

    def test_decimal_response_time_edge_cases(self):
        """
        Test decimal rounding edge cases.

        This test verifies proper rounding behavior for various decimal values.
        """
        test_cases = [
            # Values that round up
            (0.6, 1),  # 0.6 rounds up to 1
            (1.6, 2),  # 1.6 rounds up to 2
            (99.7, 100),  # 99.7 rounds up to 100
            # Values that round down
            (0.4, 0),  # 0.4 rounds down to 0
            (1.4, 1),  # 1.4 rounds down to 1
            (99.4, 99),  # 99.4 rounds down to 99
            # Banker's rounding (round half to even)
            (0.5, 0),  # 0.5 rounds to 0 (even)
            (1.5, 2),  # 1.5 rounds to 2 (even)
            (2.5, 2),  # 2.5 rounds to 2 (even)
            # Exact values (no rounding needed)
            (1.0, 1),  # 1.0 stays as 1
            (5.0, 5),  # 5.0 stays as 5
            (100.0, 100),  # 100.0 stays as 100
        ]

        for input_value, expected in test_cases:
            peer_data = {"response_time": input_value}

            result = self.parser._extract_timing_metric(peer_data, "response_time")

            assert result == expected, (
                f"Response time {input_value}ms should round to {expected}ms, "
                f"but got {result}ms"
            )

    def test_all_timing_metrics_decimal_rounding(self):
        """
        Test that ALL timing metrics (connect_time, first_byte_time, response_time)
        are rounded correctly, not just response_time.

        The bug affects all three timing metrics.
        """
        peer_data = {"connect_time": 2.8, "first_byte_time": 3.7, "response_time": 4.6}

        connect_result = self.parser._extract_timing_metric(peer_data, "connect_time")
        first_byte_result = self.parser._extract_timing_metric(
            peer_data, "first_byte_time"
        )
        response_result = self.parser._extract_timing_metric(peer_data, "response_time")

        # All should be rounded, not truncated
        assert connect_result == 3, (
            f"connect_time 2.8ms should round to 3ms, got {connect_result}ms"
        )
        assert first_byte_result == 4, (
            f"first_byte_time 3.7ms should round to 4ms, got {first_byte_result}ms"
        )
        assert response_result == 5, (
            f"response_time 4.6ms should round to 5ms, got {response_result}ms"
        )

    def test_issue_1_reproduction(self, tmp_path):
        """
        Full reproduction of Issue #1 using the exact sample data from the bug report.

        This test parses the sample-bug-logs.txt content and verifies that
        the extracted timing values are ROUNDED, not TRUNCATED.
        """
        # Sample data from issue #1
        log_data = [
            json.dumps(
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
                }
            ),
            json.dumps(
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
                }
            ),
            json.dumps(
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
                }
            ),
            json.dumps(
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
                }
            ),
        ]

        log_file = tmp_path / "sample-bug-logs.txt"
        log_file.write_text("\n".join(log_data))

        entries = list(self.parser.parse_log_file(str(log_file)))

        assert len(entries) == 4, "Should parse all 4 log entries"

        # Extract the response times that were parsed
        response_times = [entry.upstream_metrics[0].response_time for entry in entries]

        # Expected: [3, 4, 5, 6] (rounded)
        # Actual (with bug): [2, 3, 4, 5] (truncated)
        expected_rounded = [3, 4, 5, 6]

        assert response_times == expected_rounded, (
            f"Response times should be {expected_rounded} (rounded from [2.8, 3.7, 4.6, 5.5]), "
            f"but got {response_times} (truncated)"
        )

        # Verify statistics would be correct
        # Expected: min=3, max=6, avg=4.5
        # Actual (with bug): min=2, max=5, avg=3.5
        assert min(response_times) == 3, (
            f"Minimum should be 3ms (from 2.8ms rounded), got {min(response_times)}ms"
        )
        assert max(response_times) == 6, (
            f"Maximum should be 6ms (from 5.5ms rounded), got {max(response_times)}ms"
        )

        avg = sum(response_times) / len(response_times)
        assert avg == 4.5, f"Average should be 4.5ms, got {avg}ms"
