"""
Tests for the output formatter module.
"""

import pytest
from claude_logiq.output_formatter import (
    GroupedFormatter,
    CSVFormatter,
    OutputFormatterFactory,
)
from claude_logiq.time_aggregator import AggregatedBucket, TimingStats


class TestOutputFormatterFactory:
    """Test cases for OutputFormatterFactory."""

    def test_create_grouped_formatter(self):
        """Test creating grouped formatter."""
        formatter = OutputFormatterFactory.create_formatter("grouped")
        assert isinstance(formatter, GroupedFormatter)

    def test_create_csv_formatter(self):
        """Test creating CSV formatter."""
        formatter = OutputFormatterFactory.create_formatter("csv")
        assert isinstance(formatter, CSVFormatter)

    def test_create_invalid_formatter(self):
        """Test creating formatter with invalid type."""
        with pytest.raises(ValueError, match="Unsupported format type"):
            OutputFormatterFactory.create_formatter("invalid")

    def test_get_supported_formats(self):
        """Test getting supported formats."""
        formats = OutputFormatterFactory.get_supported_formats()
        assert "grouped" in formats
        assert "csv" in formats
        assert len(formats) == 2


class TestGroupedFormatter:
    """Test cases for GroupedFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = GroupedFormatter()

    def test_format_empty_results(self):
        """Test formatting empty results."""
        output = self.formatter.format_results([])
        assert "No upstream timing data found" in output

    def test_format_single_bucket(self):
        """Test formatting a single bucket."""
        # Create test data
        connect_stats = TimingStats(
            min_value=1,
            max_value=5,
            avg_value=3.0,
            p5_value=1.5,
            p95_value=4.5,
            count=10,
            metric_name="connect_time",
        )

        bucket = AggregatedBucket(
            pool_name="test_pool",
            bucket_start=1446249300000,
            bucket_end=1446249600000,
            connect_time_stats=connect_stats,
        )

        output = self.formatter.format_results([bucket])

        # Check that output contains expected elements
        assert "NGINX Plus Upstream Timing Analysis" in output
        assert "test_pool" in output
        assert "Connect Time:" in output
        assert "Min: 1ms" in output
        assert "Max: 5ms" in output
        assert "Avg: 3.00ms" in output
        assert "P5:  1.50ms" in output
        assert "P95: 4.50ms" in output
        assert "Count: 10 samples" in output

    def test_format_multiple_buckets_same_pool(self):
        """Test formatting multiple buckets from the same pool."""
        # Create test data with two time buckets
        bucket1 = AggregatedBucket(
            pool_name="test_pool",
            bucket_start=1446249300000,
            bucket_end=1446249600000,
            connect_time_stats=TimingStats(
                min_value=1,
                max_value=5,
                avg_value=3.0,
                p5_value=1.5,
                p95_value=4.5,
                count=10,
                metric_name="connect_time",
            ),
        )

        bucket2 = AggregatedBucket(
            pool_name="test_pool",
            bucket_start=1446249600000,
            bucket_end=1446249900000,
            response_time_stats=TimingStats(
                min_value=10,
                max_value=50,
                avg_value=30.0,
                p5_value=15.0,
                p95_value=45.0,
                count=20,
                metric_name="response_time",
            ),
        )

        output = self.formatter.format_results([bucket1, bucket2])

        # Check that both buckets are present under the same pool
        assert "test_pool" in output
        assert "Connect Time:" in output
        assert "Response Time:" in output
        assert output.count("Time Bucket:") == 2  # Two time buckets

    def test_format_multiple_pools(self):
        """Test formatting multiple pools."""
        bucket1 = AggregatedBucket(
            pool_name="pool_a",
            bucket_start=1446249300000,
            bucket_end=1446249600000,
            connect_time_stats=TimingStats(
                min_value=1,
                max_value=5,
                avg_value=3.0,
                p5_value=1.5,
                p95_value=4.5,
                count=10,
                metric_name="connect_time",
            ),
        )

        bucket2 = AggregatedBucket(
            pool_name="pool_b",
            bucket_start=1446249300000,
            bucket_end=1446249600000,
            response_time_stats=TimingStats(
                min_value=10,
                max_value=50,
                avg_value=30.0,
                p5_value=15.0,
                p95_value=45.0,
                count=20,
                metric_name="response_time",
            ),
        )

        output = self.formatter.format_results([bucket1, bucket2])

        # Check that both pools are present
        assert "pool_a" in output
        assert "pool_b" in output
        assert "Connect Time:" in output
        assert "Response Time:" in output

    def test_format_all_metric_types(self):
        """Test formatting with all three metric types."""
        bucket = AggregatedBucket(
            pool_name="full_pool",
            bucket_start=1446249300000,
            bucket_end=1446249600000,
            connect_time_stats=TimingStats(
                min_value=1,
                max_value=5,
                avg_value=3.0,
                p5_value=1.5,
                p95_value=4.5,
                count=10,
                metric_name="connect_time",
            ),
            first_byte_time_stats=TimingStats(
                min_value=5,
                max_value=15,
                avg_value=10.0,
                p5_value=6.0,
                p95_value=14.0,
                count=8,
                metric_name="first_byte_time",
            ),
            response_time_stats=TimingStats(
                min_value=10,
                max_value=50,
                avg_value=30.0,
                p5_value=15.0,
                p95_value=45.0,
                count=12,
                metric_name="response_time",
            ),
        )

        output = self.formatter.format_results([bucket])

        # Check that all three metric types are present
        assert "Connect Time:" in output
        assert "First Byte Time:" in output
        assert "Response Time:" in output


class TestCSVFormatter:
    """Test cases for CSVFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = CSVFormatter()

    def test_format_empty_results(self):
        """Test formatting empty results."""
        output = self.formatter.format_results([])

        # Should return header only
        lines = output.strip().split("\n")
        assert len(lines) == 1
        assert "pool_name,bucket_start,bucket_end,metric_type" in lines[0]

    def test_format_single_bucket_single_metric(self):
        """Test formatting a single bucket with one metric."""
        bucket = AggregatedBucket(
            pool_name="test_pool",
            bucket_start=1446249300000,
            bucket_end=1446249600000,
            connect_time_stats=TimingStats(
                min_value=1,
                max_value=5,
                avg_value=3.0,
                p5_value=1.5,
                p95_value=4.5,
                count=10,
                metric_name="connect_time",
            ),
        )

        output = self.formatter.format_results([bucket])
        lines = output.strip().split("\n")

        # Should have header + 1 data row
        assert len(lines) == 2

        # Check header
        header = lines[0]
        assert "pool_name" in header
        assert "metric_type" in header
        assert "min_ms" in header
        assert "max_ms" in header

        # Check data row
        data_row = lines[1]
        assert "test_pool" in data_row
        assert "connect_time" in data_row
        assert "1" in data_row  # min
        assert "5" in data_row  # max
        assert "3.0" in data_row  # avg
        assert "10" in data_row  # count

    def test_format_single_bucket_multiple_metrics(self):
        """Test formatting a single bucket with multiple metrics."""
        bucket = AggregatedBucket(
            pool_name="test_pool",
            bucket_start=1446249300000,
            bucket_end=1446249600000,
            connect_time_stats=TimingStats(
                min_value=1,
                max_value=5,
                avg_value=3.0,
                p5_value=1.5,
                p95_value=4.5,
                count=10,
                metric_name="connect_time",
            ),
            response_time_stats=TimingStats(
                min_value=10,
                max_value=50,
                avg_value=30.0,
                p5_value=15.0,
                p95_value=45.0,
                count=12,
                metric_name="response_time",
            ),
        )

        output = self.formatter.format_results([bucket])
        lines = output.strip().split("\n")

        # Should have header + 2 data rows (one per metric)
        assert len(lines) == 3

        # Check that both metrics are present
        csv_content = output
        assert "connect_time" in csv_content
        assert "response_time" in csv_content

    def test_format_multiple_buckets(self):
        """Test formatting multiple buckets."""
        bucket1 = AggregatedBucket(
            pool_name="pool_a",
            bucket_start=1446249300000,
            bucket_end=1446249600000,
            connect_time_stats=TimingStats(
                min_value=1,
                max_value=5,
                avg_value=3.0,
                p5_value=1.5,
                p95_value=4.5,
                count=10,
                metric_name="connect_time",
            ),
        )

        bucket2 = AggregatedBucket(
            pool_name="pool_b",
            bucket_start=1446249300000,
            bucket_end=1446249600000,
            response_time_stats=TimingStats(
                min_value=10,
                max_value=50,
                avg_value=30.0,
                p5_value=15.0,
                p95_value=45.0,
                count=12,
                metric_name="response_time",
            ),
        )

        output = self.formatter.format_results([bucket1, bucket2])
        lines = output.strip().split("\n")

        # Should have header + 2 data rows
        assert len(lines) == 3

        # Check that both pools are present
        csv_content = output
        assert "pool_a" in csv_content
        assert "pool_b" in csv_content

    def test_csv_format_values(self):
        """Test CSV value formatting and rounding."""
        bucket = AggregatedBucket(
            pool_name="test_pool",
            bucket_start=1446249300000,
            bucket_end=1446249600000,
            connect_time_stats=TimingStats(
                min_value=1,
                max_value=5,
                avg_value=3.123456,  # Should be rounded
                p5_value=1.789012,  # Should be rounded
                p95_value=4.567890,  # Should be rounded
                count=10,
                metric_name="connect_time",
            ),
        )

        output = self.formatter.format_results([bucket])

        # Check that values are properly rounded
        assert "3.12" in output  # avg_value rounded to 2 decimals
        assert "1.79" in output  # p5_value rounded to 2 decimals
        assert "4.57" in output  # p95_value rounded to 2 decimals

    def test_csv_iso_timestamps(self):
        """Test that CSV includes ISO timestamp format."""
        bucket = AggregatedBucket(
            pool_name="test_pool",
            bucket_start=1446249300000,
            bucket_end=1446249600000,
            connect_time_stats=TimingStats(
                min_value=1,
                max_value=5,
                avg_value=3.0,
                p5_value=1.5,
                p95_value=4.5,
                count=10,
                metric_name="connect_time",
            ),
        )

        output = self.formatter.format_results([bucket])

        # Check that ISO timestamps are present
        assert "2015-10-" in output  # Should contain the year and month
        # The exact format may vary based on timezone, but should contain date
