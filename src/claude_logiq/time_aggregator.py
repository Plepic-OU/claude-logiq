"""
Time-based aggregation for upstream timing metrics.

This module provides functionality to group upstream timing data by time buckets
and calculate statistical metrics for analysis.
"""

import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .log_parser import LogEntry, UpstreamMetrics


@dataclass
class TimingStats:
    """Statistical metrics for timing data."""

    min_value: int
    max_value: int
    avg_value: float
    p5_value: float
    p95_value: float
    count: int
    metric_name: str


@dataclass
class AggregatedBucket:
    """Represents aggregated metrics for a time bucket and upstream pool."""

    pool_name: str
    bucket_start: int  # Unix milliseconds
    bucket_end: int  # Unix milliseconds
    connect_time_stats: Optional[TimingStats] = None
    first_byte_time_stats: Optional[TimingStats] = None
    response_time_stats: Optional[TimingStats] = None

    @property
    def bucket_start_iso(self) -> str:
        """Get bucket start time as ISO 8601 string."""
        return datetime.fromtimestamp(self.bucket_start / 1000).isoformat()

    @property
    def bucket_end_iso(self) -> str:
        """Get bucket end time as ISO 8601 string."""
        return datetime.fromtimestamp(self.bucket_end / 1000).isoformat()


class TimeAggregator:
    """Aggregates upstream timing metrics into time buckets."""

    def __init__(self, bucket_duration_seconds: float):
        """
        Initialize the time aggregator.

        Args:
            bucket_duration_seconds: Duration of each time bucket in seconds
        """
        self.bucket_duration_ms = int(bucket_duration_seconds * 1000)
        if self.bucket_duration_ms <= 0:
            raise ValueError("Bucket duration must be positive")

    def aggregate_metrics(self, log_entries: List[LogEntry]) -> List[AggregatedBucket]:
        """
        Aggregate log entries into time buckets and calculate statistics.

        Args:
            log_entries: List of parsed log entries

        Returns:
            List of aggregated buckets with statistical metrics
        """
        if not log_entries:
            return []

        # Group metrics by pool and time bucket
        bucket_data = self._group_by_buckets(log_entries)

        # Calculate statistics for each bucket
        aggregated_buckets = []
        for (pool_name, bucket_start), metrics_list in bucket_data.items():
            bucket = self._create_aggregated_bucket(
                pool_name, bucket_start, metrics_list
            )
            if bucket:
                aggregated_buckets.append(bucket)

        # Sort by pool name, then by bucket start time
        aggregated_buckets.sort(key=lambda b: (b.pool_name, b.bucket_start))

        return aggregated_buckets

    def _group_by_buckets(
        self, log_entries: List[LogEntry]
    ) -> Dict[Tuple[str, int], List[UpstreamMetrics]]:
        """
        Group upstream metrics by pool name and time bucket.

        Args:
            log_entries: List of parsed log entries

        Returns:
            Dictionary mapping (pool_name, bucket_start) to list of metrics
        """
        bucket_data = defaultdict(list)

        for entry in log_entries:
            for metric in entry.upstream_metrics:
                bucket_start = self._get_bucket_start(metric.timestamp)
                key = (metric.pool_name, bucket_start)
                bucket_data[key].append(metric)

        return bucket_data

    def _get_bucket_start(self, timestamp_ms: int) -> int:
        """
        Calculate the start timestamp of the bucket containing the given timestamp.

        Args:
            timestamp_ms: Timestamp in milliseconds

        Returns:
            Bucket start timestamp in milliseconds
        """
        return (timestamp_ms // self.bucket_duration_ms) * self.bucket_duration_ms

    def _create_aggregated_bucket(
        self, pool_name: str, bucket_start: int, metrics_list: List[UpstreamMetrics]
    ) -> Optional[AggregatedBucket]:
        """
        Create an aggregated bucket with statistical metrics.

        Args:
            pool_name: Name of the upstream pool
            bucket_start: Bucket start timestamp in milliseconds
            metrics_list: List of upstream metrics in this bucket

        Returns:
            AggregatedBucket with calculated statistics, or None if no valid metrics
        """
        bucket_end = bucket_start + self.bucket_duration_ms

        # Collect timing values by metric type
        connect_times = []
        first_byte_times = []
        response_times = []

        for metric in metrics_list:
            if metric.connect_time is not None:
                connect_times.append(metric.connect_time)
            if metric.first_byte_time is not None:
                first_byte_times.append(metric.first_byte_time)
            if metric.response_time is not None:
                response_times.append(metric.response_time)

        # Calculate statistics for each metric type
        connect_stats = (
            self._calculate_timing_stats(connect_times, "connect_time")
            if connect_times
            else None
        )
        first_byte_stats = (
            self._calculate_timing_stats(first_byte_times, "first_byte_time")
            if first_byte_times
            else None
        )
        response_stats = (
            self._calculate_timing_stats(response_times, "response_time")
            if response_times
            else None
        )

        # Only create bucket if we have at least one metric with data
        if any(
            stats is not None
            for stats in [connect_stats, first_byte_stats, response_stats]
        ):
            return AggregatedBucket(
                pool_name=pool_name,
                bucket_start=bucket_start,
                bucket_end=bucket_end,
                connect_time_stats=connect_stats,
                first_byte_time_stats=first_byte_stats,
                response_time_stats=response_stats,
            )

        return None

    def _calculate_timing_stats(
        self, values: List[int], metric_name: str
    ) -> TimingStats:
        """
        Calculate statistical metrics for a list of timing values.

        Args:
            values: List of timing values in milliseconds
            metric_name: Name of the metric being calculated

        Returns:
            TimingStats with calculated statistics
        """
        if not values:
            raise ValueError("Cannot calculate statistics for empty list")

        sorted_values = sorted(values)
        count = len(sorted_values)

        # Basic statistics
        min_value = min(sorted_values)
        max_value = max(sorted_values)
        avg_value = statistics.mean(sorted_values)

        # Calculate percentiles using simpler index-based approach
        if count == 1:
            p5_value = p95_value = float(sorted_values[0])
        elif count == 2:
            p5_value = float(sorted_values[0])
            p95_value = float(sorted_values[1])
        else:
            # Use index-based percentile calculation to stay within data bounds
            p5_index = max(0, int(0.05 * (count - 1)))
            p95_index = min(count - 1, int(0.95 * (count - 1)))
            p5_value = float(sorted_values[p5_index])
            p95_value = float(sorted_values[p95_index])

        return TimingStats(
            min_value=min_value,
            max_value=max_value,
            avg_value=avg_value,
            p5_value=p5_value,
            p95_value=p95_value,
            count=count,
            metric_name=metric_name,
        )

    def get_bucket_duration_ms(self) -> int:
        """Get the bucket duration in milliseconds."""
        return self.bucket_duration_ms

    def get_bucket_duration_seconds(self) -> float:
        """Get the bucket duration in seconds."""
        return self.bucket_duration_ms / 1000.0
