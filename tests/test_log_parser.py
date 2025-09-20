"""
Tests for the log parser module.
"""

import json
import pytest

from claude_logiq.log_parser import LogParser


class TestLogParser:
    """Test cases for LogParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = LogParser()

    def test_parse_valid_log_line(self):
        """Test parsing a valid log line with upstream data."""
        log_line = json.dumps({
            "timestamp": 1446249499322,
            "stream": {
                "upstreams": {
                    "postgresql_backends": {
                        "peers": [
                            {
                                "server": "10.0.0.2:15432",
                                "connect_time": 1,
                                "first_byte_time": 2,
                                "response_time": 2
                            },
                            {
                                "server": "10.0.0.2:15433",
                                "connect_time": 1,
                                "first_byte_time": 5,
                                "response_time": 5
                            }
                        ]
                    }
                }
            }
        })

        entry = self.parser._parse_log_line(log_line)

        assert entry is not None
        assert entry.timestamp == 1446249499322
        assert len(entry.upstream_metrics) == 2

        # Check first upstream metric
        metric1 = entry.upstream_metrics[0]
        assert metric1.pool_name == "postgresql_backends"
        assert metric1.server == "10.0.0.2:15432"
        assert metric1.connect_time == 1
        assert metric1.first_byte_time == 2
        assert metric1.response_time == 2

        # Check second upstream metric
        metric2 = entry.upstream_metrics[1]
        assert metric2.pool_name == "postgresql_backends"
        assert metric2.server == "10.0.0.2:15433"
        assert metric2.connect_time == 1
        assert metric2.first_byte_time == 5
        assert metric2.response_time == 5

    def test_parse_log_line_missing_timestamp(self):
        """Test parsing a log line without timestamp."""
        log_line = json.dumps({
            "stream": {
                "upstreams": {
                    "test_pool": {
                        "peers": [{"server": "test:8080", "connect_time": 1}]
                    }
                }
            }
        })

        entry = self.parser._parse_log_line(log_line)
        assert entry is None

    def test_parse_log_line_no_stream_data(self):
        """Test parsing a log line without stream data."""
        log_line = json.dumps({
            "timestamp": 1446249499322,
            "other_data": {"key": "value"}
        })

        entry = self.parser._parse_log_line(log_line)
        assert entry is None

    def test_parse_log_line_empty_upstreams(self):
        """Test parsing a log line with empty upstreams."""
        log_line = json.dumps({
            "timestamp": 1446249499322,
            "stream": {
                "upstreams": {}
            }
        })

        entry = self.parser._parse_log_line(log_line)
        assert entry is None

    def test_parse_log_line_partial_timing_data(self):
        """Test parsing with partial timing data (some metrics missing)."""
        log_line = json.dumps({
            "timestamp": 1446249499322,
            "stream": {
                "upstreams": {
                    "test_pool": {
                        "peers": [
                            {
                                "server": "10.0.0.1:8080",
                                "connect_time": 1,
                                # missing first_byte_time and response_time
                            },
                            {
                                "server": "10.0.0.1:8081",
                                "first_byte_time": 5,
                                "response_time": 10
                                # missing connect_time
                            }
                        ]
                    }
                }
            }
        })

        entry = self.parser._parse_log_line(log_line)

        assert entry is not None
        assert len(entry.upstream_metrics) == 2

        # First peer should have only connect_time
        metric1 = entry.upstream_metrics[0]
        assert metric1.connect_time == 1
        assert metric1.first_byte_time is None
        assert metric1.response_time is None

        # Second peer should have first_byte_time and response_time
        metric2 = entry.upstream_metrics[1]
        assert metric2.connect_time is None
        assert metric2.first_byte_time == 5
        assert metric2.response_time == 10

    def test_parse_log_line_invalid_json(self):
        """Test parsing invalid JSON."""
        with pytest.raises(json.JSONDecodeError):
            self.parser._parse_log_line("invalid json {")

    def test_extract_timing_metric_valid_values(self):
        """Test extracting valid timing metrics."""
        peer_data = {"connect_time": 10, "first_byte_time": 20.5}

        assert self.parser._extract_timing_metric(peer_data, "connect_time") == 10
        assert self.parser._extract_timing_metric(peer_data, "first_byte_time") == 20
        assert self.parser._extract_timing_metric(peer_data, "missing_metric") is None

    def test_extract_timing_metric_negative_values(self):
        """Test extracting negative timing values (should be filtered out)."""
        peer_data = {"connect_time": -5, "first_byte_time": 0}

        assert self.parser._extract_timing_metric(peer_data, "connect_time") is None
        assert self.parser._extract_timing_metric(peer_data, "first_byte_time") == 0

    def test_extract_timing_metric_invalid_types(self):
        """Test extracting timing metrics with invalid data types."""
        peer_data = {
            "string_value": "10ms",
            "list_value": [1, 2, 3],
            "dict_value": {"time": 5}
        }

        assert self.parser._extract_timing_metric(peer_data, "string_value") is None
        assert self.parser._extract_timing_metric(peer_data, "list_value") is None
        assert self.parser._extract_timing_metric(peer_data, "dict_value") is None

    def test_parse_log_file_success(self, tmp_path):
        """Test parsing a log file successfully."""
        # Create test log file
        log_data = [
            json.dumps({
                "timestamp": 1446249499322,
                "stream": {
                    "upstreams": {
                        "test_pool": {
                            "peers": [{"server": "test:8080", "connect_time": 1}]
                        }
                    }
                }
            }),
            json.dumps({
                "timestamp": 1446249500000,
                "stream": {
                    "upstreams": {
                        "test_pool": {
                            "peers": [{"server": "test:8080", "response_time": 5}]
                        }
                    }
                }
            })
        ]

        log_file = tmp_path / "test.log"
        log_file.write_text("\n".join(log_data))

        entries = list(self.parser.parse_log_file(str(log_file)))

        assert len(entries) == 2
        assert entries[0].timestamp == 1446249499322
        assert entries[1].timestamp == 1446249500000

        stats = self.parser.get_parsing_stats()
        assert stats["parsed_entries"] == 2
        assert stats["skipped_entries"] == 0
        assert stats["error_entries"] == 0

    def test_parse_log_file_not_found(self):
        """Test parsing a non-existent log file."""
        with pytest.raises(FileNotFoundError):
            list(self.parser.parse_log_file("/non/existent/file.log"))

    def test_parse_log_file_with_errors(self, tmp_path):
        """Test parsing a log file with some invalid lines."""
        log_data = [
            json.dumps({
                "timestamp": 1446249499322,
                "stream": {
                    "upstreams": {
                        "test_pool": {
                            "peers": [{"server": "test:8080", "connect_time": 1}]
                        }
                    }
                }
            }),
            "invalid json line",
            "",  # empty line
            json.dumps({"timestamp": "invalid", "stream": {}})  # invalid timestamp
        ]

        log_file = tmp_path / "test.log"
        log_file.write_text("\n".join(log_data))

        entries = list(self.parser.parse_log_file(str(log_file)))

        assert len(entries) == 1  # Only one valid entry

        stats = self.parser.get_parsing_stats()
        assert stats["parsed_entries"] == 1
        assert stats["skipped_entries"] == 1  # invalid timestamp entry
        assert stats["error_entries"] == 1  # invalid json entry

    def test_parsing_stats_reset(self):
        """Test resetting parsing statistics."""
        # Simulate some parsing activity
        self.parser.parsed_entries = 5
        self.parser.skipped_entries = 2
        self.parser.error_entries = 1

        stats_before = self.parser.get_parsing_stats()
        assert stats_before["parsed_entries"] == 5

        self.parser.reset_stats()

        stats_after = self.parser.get_parsing_stats()
        assert stats_after["parsed_entries"] == 0
        assert stats_after["skipped_entries"] == 0
        assert stats_after["error_entries"] == 0