"""
Tests for the time aggregator module.
"""

import pytest
from claude_logiq.log_parser import LogEntry, UpstreamMetrics
from claude_logiq.time_aggregator import TimeAggregator, TimingStats, AggregatedBucket


class TestTimeAggregator:
    """Test cases for TimeAggregator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.aggregator = TimeAggregator(bucket_duration_seconds=300)  # 5 minutes

    def test_initialization_valid_duration(self):
        """Test initializing aggregator with valid duration."""
        agg = TimeAggregator(600)  # 10 minutes
        assert agg.get_bucket_duration_seconds() == 600
        assert agg.get_bucket_duration_ms() == 600000

    def test_initialization_invalid_duration(self):
        """Test initializing aggregator with invalid duration."""
        with pytest.raises(ValueError, match="Bucket duration must be positive"):
            TimeAggregator(0)

        with pytest.raises(ValueError, match="Bucket duration must be positive"):
            TimeAggregator(-100)

    def test_get_bucket_start(self):
        """Test calculating bucket start timestamps."""
        # Test with 5-minute buckets (300 seconds = 300000 ms)
        agg = TimeAggregator(300)

        # Test timestamp alignment
        assert (
            agg._get_bucket_start(1446249499322) == 1446249300000
        )  # Rounded down to 5-min boundary
        assert agg._get_bucket_start(1446249600000) == 1446249600000  # Already aligned
        assert agg._get_bucket_start(1446249650000) == 1446249600000  # Same bucket

    def test_aggregate_empty_entries(self):
        """Test aggregating empty list of entries."""
        result = self.aggregator.aggregate_metrics([])
        assert result == []

    def test_aggregate_single_entry(self):
        """Test aggregating a single log entry."""
        # Create test data
        metrics = [
            UpstreamMetrics(
                pool_name="test_pool",
                server="server1",
                timestamp=1446249499322,
                connect_time=1,
                first_byte_time=2,
                response_time=3,
            )
        ]
        entry = LogEntry(timestamp=1446249499322, upstream_metrics=metrics)

        result = self.aggregator.aggregate_metrics([entry])

        assert len(result) == 1
        bucket = result[0]
        assert bucket.pool_name == "test_pool"
        assert bucket.bucket_start == 1446249300000  # Aligned to 5-minute boundary

        # Check statistics
        assert bucket.connect_time_stats is not None
        assert bucket.connect_time_stats.count == 1
        assert bucket.connect_time_stats.min_value == 1
        assert bucket.connect_time_stats.max_value == 1
        assert bucket.connect_time_stats.avg_value == 1.0

        assert bucket.first_byte_time_stats is not None
        assert bucket.first_byte_time_stats.count == 1
        assert bucket.first_byte_time_stats.min_value == 2

        assert bucket.response_time_stats is not None
        assert bucket.response_time_stats.count == 1
        assert bucket.response_time_stats.min_value == 3

    def test_aggregate_multiple_pools(self):
        """Test aggregating entries from multiple pools."""
        metrics1 = [
            UpstreamMetrics(
                pool_name="pool_a",
                server="server1",
                timestamp=1446249499322,
                connect_time=1,
            )
        ]
        metrics2 = [
            UpstreamMetrics(
                pool_name="pool_b",
                server="server2",
                timestamp=1446249499322,
                connect_time=2,
            )
        ]

        entries = [
            LogEntry(timestamp=1446249499322, upstream_metrics=metrics1),
            LogEntry(timestamp=1446249499322, upstream_metrics=metrics2),
        ]

        result = self.aggregator.aggregate_metrics(entries)

        assert len(result) == 2

        # Results should be sorted by pool name
        assert result[0].pool_name == "pool_a"
        assert result[1].pool_name == "pool_b"

    def test_aggregate_multiple_time_buckets(self):
        """Test aggregating entries across multiple time buckets."""
        metrics1 = [
            UpstreamMetrics(
                pool_name="test_pool",
                server="server1",
                timestamp=1446249499322,  # First bucket
                connect_time=1,
            )
        ]
        metrics2 = [
            UpstreamMetrics(
                pool_name="test_pool",
                server="server1",
                timestamp=1446249799322,  # Second bucket (5 minutes later)
                connect_time=2,
            )
        ]

        entries = [
            LogEntry(timestamp=1446249499322, upstream_metrics=metrics1),
            LogEntry(timestamp=1446249799322, upstream_metrics=metrics2),
        ]

        result = self.aggregator.aggregate_metrics(entries)

        assert len(result) == 2
        assert result[0].bucket_start == 1446249300000
        assert result[1].bucket_start == 1446249600000

    def test_partial_metrics(self):
        """Test aggregating entries with partial timing data."""
        metrics = [
            UpstreamMetrics(
                pool_name="test_pool",
                server="server1",
                timestamp=1446249499322,
                connect_time=1,
                first_byte_time=None,  # Missing
                response_time=3,
            ),
            UpstreamMetrics(
                pool_name="test_pool",
                server="server2",
                timestamp=1446249499322,
                connect_time=None,  # Missing
                first_byte_time=5,
                response_time=None,  # Missing
            ),
        ]
        entry = LogEntry(timestamp=1446249499322, upstream_metrics=metrics)

        result = self.aggregator.aggregate_metrics([entry])

        assert len(result) == 1
        bucket = result[0]

        # connect_time should have 1 sample (from server1)
        assert bucket.connect_time_stats is not None
        assert bucket.connect_time_stats.count == 1
        assert bucket.connect_time_stats.min_value == 1

        # first_byte_time should have 1 sample (from server2)
        assert bucket.first_byte_time_stats is not None
        assert bucket.first_byte_time_stats.count == 1
        assert bucket.first_byte_time_stats.min_value == 5

        # response_time should have 1 sample (from server1)
        assert bucket.response_time_stats is not None
        assert bucket.response_time_stats.count == 1
        assert bucket.response_time_stats.min_value == 3


class TestTimingStats:
    """Test cases for TimingStats calculation."""

    def test_calculate_timing_stats_single_value(self):
        """Test calculating statistics for a single value."""
        agg = TimeAggregator(300)
        stats = agg._calculate_timing_stats([10], "test_metric")

        assert stats.min_value == 10
        assert stats.max_value == 10
        assert stats.avg_value == 10.0
        assert stats.p5_value == 10.0
        assert stats.p95_value == 10.0
        assert stats.count == 1
        assert stats.metric_name == "test_metric"

    def test_calculate_timing_stats_multiple_values(self):
        """Test calculating statistics for multiple values."""
        agg = TimeAggregator(300)
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        stats = agg._calculate_timing_stats(values, "test_metric")

        assert stats.min_value == 1
        assert stats.max_value == 10
        assert stats.avg_value == 5.5
        assert stats.count == 10

        # Check percentiles are reasonable (quantiles can have different behavior)
        # P5 should be low, P95 should be high
        assert stats.p5_value < stats.avg_value < stats.p95_value
        assert stats.p5_value >= stats.min_value
        assert stats.p95_value <= stats.max_value

    def test_calculate_timing_stats_empty_list(self):
        """Test calculating statistics for empty list."""
        agg = TimeAggregator(300)

        with pytest.raises(
            ValueError, match="Cannot calculate statistics for empty list"
        ):
            agg._calculate_timing_stats([], "test_metric")

    def test_calculate_timing_stats_percentiles(self):
        """Test percentile calculations with known values."""
        agg = TimeAggregator(300)
        # Use a dataset where percentiles are predictable
        values = list(range(1, 101))  # 1 to 100

        stats = agg._calculate_timing_stats(values, "test_metric")

        assert stats.min_value == 1
        assert stats.max_value == 100
        assert stats.avg_value == 50.5

        # With 100 values, P5 should be around 5-6, P95 should be around 95-96
        assert 5 <= stats.p5_value <= 6
        assert 95 <= stats.p95_value <= 96


class TestAggregatedBucket:
    """Test cases for AggregatedBucket class."""

    def test_bucket_iso_timestamps(self):
        """Test ISO 8601 timestamp properties."""
        bucket = AggregatedBucket(
            pool_name="test_pool",
            bucket_start=1446249300000,  # 2015-10-30T21:35:00.000Z
            bucket_end=1446249600000,  # 2015-10-30T21:40:00.000Z
        )

        # Check that ISO timestamps are properly formatted
        start_iso = bucket.bucket_start_iso
        end_iso = bucket.bucket_end_iso

        assert "2015-10-" in start_iso  # Should contain year and month
        assert "2015-10-" in end_iso  # Should contain year and month
        assert start_iso < end_iso  # Start should be before end

    def test_bucket_with_stats(self):
        """Test bucket with timing statistics."""
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

        assert bucket.connect_time_stats is not None
        assert bucket.connect_time_stats.count == 10
        assert bucket.first_byte_time_stats is None
        assert bucket.response_time_stats is None
