"""
Integration tests for the complete log processing pipeline.
"""

import json
from claude_logiq.log_parser import LogParser
from claude_logiq.time_aggregator import TimeAggregator
from claude_logiq.output_formatter import OutputFormatterFactory


class TestLogProcessingIntegration:
    """Integration tests for the complete log processing pipeline."""

    def test_complete_pipeline_grouped_format(self, tmp_path):
        """Test the complete pipeline from parsing to grouped output."""
        # Create test log data similar to actual NGINX Plus logs
        log_data = [
            json.dumps({
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
            }),
            json.dumps({
                "timestamp": 1446249504427,
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
                                    "server": "10.0.0.2:15434",
                                    "connect_time": 1,
                                    "first_byte_time": 21,
                                    "response_time": 21
                                }
                            ]
                        }
                    }
                }
            })
        ]

        # Write test log file
        log_file = tmp_path / "test.log"
        log_file.write_text("\n".join(log_data))

        # Initialize components
        parser = LogParser()
        aggregator = TimeAggregator(bucket_duration_seconds=300)  # 5 minutes
        formatter = OutputFormatterFactory.create_formatter("grouped")

        # Execute pipeline
        log_entries = list(parser.parse_log_file(str(log_file)))
        aggregated_buckets = aggregator.aggregate_metrics(log_entries)
        output = formatter.format_results(aggregated_buckets)

        # Validate results
        assert len(log_entries) == 2
        assert len(aggregated_buckets) == 1  # Same time bucket

        bucket = aggregated_buckets[0]
        assert bucket.pool_name == "postgresql_backends"

        # Check that statistics are calculated
        assert bucket.connect_time_stats is not None
        assert bucket.connect_time_stats.count == 4  # 2 peers × 2 entries
        assert bucket.first_byte_time_stats is not None
        assert bucket.response_time_stats is not None

        # Check output format
        assert "NGINX Plus Upstream Timing Analysis" in output
        assert "postgresql_backends" in output
        assert "Connect Time:" in output
        assert "First Byte Time:" in output
        assert "Response Time:" in output

    def test_complete_pipeline_csv_format(self, tmp_path):
        """Test the complete pipeline with CSV output format."""
        # Create simpler test data
        log_data = [
            json.dumps({
                "timestamp": 1446249499322,
                "stream": {
                    "upstreams": {
                        "test_pool": {
                            "peers": [
                                {
                                    "server": "server1:8080",
                                    "connect_time": 5,
                                    "response_time": 10
                                }
                            ]
                        }
                    }
                }
            })
        ]

        # Write test log file
        log_file = tmp_path / "test.log"
        log_file.write_text("\n".join(log_data))

        # Initialize components
        parser = LogParser()
        aggregator = TimeAggregator(bucket_duration_seconds=600)  # 10 minutes
        formatter = OutputFormatterFactory.create_formatter("csv")

        # Execute pipeline
        log_entries = list(parser.parse_log_file(str(log_file)))
        aggregated_buckets = aggregator.aggregate_metrics(log_entries)
        output = formatter.format_results(aggregated_buckets)

        # Validate CSV output
        lines = output.strip().split('\n')
        assert len(lines) >= 2  # Header + at least one data row

        # Check header
        header = lines[0]
        assert "pool_name" in header
        assert "metric_type" in header

        # Check data rows
        csv_content = output
        assert "test_pool" in csv_content
        assert "connect_time" in csv_content
        assert "response_time" in csv_content

    def test_pipeline_with_multiple_pools_and_buckets(self, tmp_path):
        """Test pipeline with multiple pools and time buckets."""
        # Create test data spanning multiple time buckets and pools
        log_data = [
            json.dumps({
                "timestamp": 1446249499322,  # First bucket
                "stream": {
                    "upstreams": {
                        "pool_a": {
                            "peers": [{"server": "server1", "connect_time": 1}]
                        }
                    }
                }
            }),
            json.dumps({
                "timestamp": 1446249799322,  # Second bucket (5 minutes later)
                "stream": {
                    "upstreams": {
                        "pool_b": {
                            "peers": [{"server": "server2", "connect_time": 2}]
                        }
                    }
                }
            })
        ]

        # Write test log file
        log_file = tmp_path / "test.log"
        log_file.write_text("\n".join(log_data))

        # Initialize components
        parser = LogParser()
        aggregator = TimeAggregator(bucket_duration_seconds=300)  # 5 minutes
        formatter = OutputFormatterFactory.create_formatter("grouped")

        # Execute pipeline
        log_entries = list(parser.parse_log_file(str(log_file)))
        aggregated_buckets = aggregator.aggregate_metrics(log_entries)
        output = formatter.format_results(aggregated_buckets)

        # Should have 2 buckets (different pools in different time buckets)
        assert len(aggregated_buckets) == 2

        # Check that output contains both pools
        assert "pool_a" in output
        assert "pool_b" in output

    def test_pipeline_with_parsing_errors(self, tmp_path):
        """Test pipeline handling of parsing errors and partial data."""
        log_data = [
            # Valid entry
            json.dumps({
                "timestamp": 1446249499322,
                "stream": {
                    "upstreams": {
                        "valid_pool": {
                            "peers": [{"server": "server1", "connect_time": 1}]
                        }
                    }
                }
            }),
            # Invalid JSON
            "invalid json line",
            # Missing timestamp
            json.dumps({
                "stream": {
                    "upstreams": {
                        "invalid_pool": {
                            "peers": [{"server": "server2", "connect_time": 2}]
                        }
                    }
                }
            }),
            # Empty line
            "",
            # Another valid entry
            json.dumps({
                "timestamp": 1446249500000,
                "stream": {
                    "upstreams": {
                        "valid_pool": {
                            "peers": [{"server": "server3", "response_time": 5}]
                        }
                    }
                }
            })
        ]

        # Write test log file
        log_file = tmp_path / "test.log"
        log_file.write_text("\n".join(log_data))

        # Initialize components
        parser = LogParser()
        aggregator = TimeAggregator(bucket_duration_seconds=300)
        formatter = OutputFormatterFactory.create_formatter("grouped")

        # Execute pipeline
        log_entries = list(parser.parse_log_file(str(log_file)))
        aggregated_buckets = aggregator.aggregate_metrics(log_entries)
        output = formatter.format_results(aggregated_buckets)

        # Should have successfully processed 2 valid entries
        stats = parser.get_parsing_stats()
        assert stats["parsed_entries"] == 2
        assert stats["error_entries"] >= 1  # Invalid JSON
        assert stats["skipped_entries"] >= 1  # Missing timestamp

        # Should still produce results from valid entries
        assert len(aggregated_buckets) >= 1
        assert "valid_pool" in output

    def test_pipeline_empty_results(self, tmp_path):
        """Test pipeline behavior with no valid upstream data."""
        log_data = [
            # Entry without upstream data
            json.dumps({
                "timestamp": 1446249499322,
                "other_data": {"key": "value"}
            }),
            # Entry with empty upstreams
            json.dumps({
                "timestamp": 1446249500000,
                "stream": {"upstreams": {}}
            })
        ]

        # Write test log file
        log_file = tmp_path / "test.log"
        log_file.write_text("\n".join(log_data))

        # Initialize components
        parser = LogParser()
        aggregator = TimeAggregator(bucket_duration_seconds=300)
        formatter = OutputFormatterFactory.create_formatter("grouped")

        # Execute pipeline
        log_entries = list(parser.parse_log_file(str(log_file)))
        aggregated_buckets = aggregator.aggregate_metrics(log_entries)
        output = formatter.format_results(aggregated_buckets)

        # Should have no valid entries with upstream data
        assert len(log_entries) == 0
        assert len(aggregated_buckets) == 0
        assert "No upstream timing data found" in output