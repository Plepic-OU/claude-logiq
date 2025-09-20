"""
Output formatters for upstream timing analysis results.

This module provides different output formats for the analyzed timing data,
including human-readable grouped format and machine-readable CSV format.
"""

import csv
from abc import ABC, abstractmethod
from io import StringIO
from typing import List

from .time_aggregator import AggregatedBucket, TimingStats


class OutputFormatter(ABC):
    """Abstract base class for output formatters."""

    @abstractmethod
    def format_results(self, buckets: List[AggregatedBucket]) -> str:
        """
        Format the aggregated results for output.

        Args:
            buckets: List of aggregated buckets to format

        Returns:
            Formatted output string
        """
        pass


class GroupedFormatter(OutputFormatter):
    """Formatter for human-readable grouped output."""

    def format_results(self, buckets: List[AggregatedBucket]) -> str:
        """
        Format results in a human-readable grouped format.

        Args:
            buckets: List of aggregated buckets to format

        Returns:
            Formatted output string with grouped sections
        """
        if not buckets:
            return "No upstream timing data found in the log file.\n"

        output = StringIO()
        output.write("NGINX Plus Upstream Timing Analysis\n")
        output.write("=" * 50 + "\n\n")

        # Group buckets by pool name
        pools = {}
        for bucket in buckets:
            if bucket.pool_name not in pools:
                pools[bucket.pool_name] = []
            pools[bucket.pool_name].append(bucket)

        # Format each pool
        for pool_name, pool_buckets in pools.items():
            output.write(f"Upstream Pool: {pool_name}\n")
            output.write("-" * 30 + "\n")

            for bucket in pool_buckets:
                output.write(f"Time Bucket: {bucket.bucket_start_iso} - {bucket.bucket_end_iso}\n")

                # Format timing statistics
                if bucket.connect_time_stats:
                    output.write("  Connect Time:\n")
                    output.write(self._format_timing_stats(bucket.connect_time_stats, indent="    "))

                if bucket.first_byte_time_stats:
                    output.write("  First Byte Time:\n")
                    output.write(self._format_timing_stats(bucket.first_byte_time_stats, indent="    "))

                if bucket.response_time_stats:
                    output.write("  Response Time:\n")
                    output.write(self._format_timing_stats(bucket.response_time_stats, indent="    "))

                output.write("\n")

            output.write("\n")

        return output.getvalue()

    def _format_timing_stats(self, stats: TimingStats, indent: str = "") -> str:
        """
        Format timing statistics for display.

        Args:
            stats: TimingStats object to format
            indent: Indentation string for each line

        Returns:
            Formatted statistics string
        """
        lines = [
            f"{indent}Min: {stats.min_value}ms\n",
            f"{indent}Max: {stats.max_value}ms\n",
            f"{indent}Avg: {stats.avg_value:.2f}ms\n",
            f"{indent}P5:  {stats.p5_value:.2f}ms\n",
            f"{indent}P95: {stats.p95_value:.2f}ms\n",
            f"{indent}Count: {stats.count} samples\n"
        ]
        return "".join(lines)


class CSVFormatter(OutputFormatter):
    """Formatter for machine-readable CSV output."""

    def format_results(self, buckets: List[AggregatedBucket]) -> str:
        """
        Format results in CSV format.

        Args:
            buckets: List of aggregated buckets to format

        Returns:
            CSV formatted output string
        """
        if not buckets:
            return "pool_name,bucket_start,bucket_end,metric_type,min_ms,max_ms,avg_ms,p5_ms,p95_ms,count\n"

        output = StringIO()
        writer = csv.writer(output)

        # Write header
        header = [
            'pool_name', 'bucket_start', 'bucket_end', 'metric_type',
            'min_ms', 'max_ms', 'avg_ms', 'p5_ms', 'p95_ms', 'count'
        ]
        writer.writerow(header)

        # Write data rows
        for bucket in buckets:
            base_row = [
                bucket.pool_name,
                bucket.bucket_start_iso,
                bucket.bucket_end_iso
            ]

            # Add rows for each metric type that has data
            if bucket.connect_time_stats:
                row = base_row + self._format_stats_for_csv(bucket.connect_time_stats, "connect_time")
                writer.writerow(row)

            if bucket.first_byte_time_stats:
                row = base_row + self._format_stats_for_csv(bucket.first_byte_time_stats, "first_byte_time")
                writer.writerow(row)

            if bucket.response_time_stats:
                row = base_row + self._format_stats_for_csv(bucket.response_time_stats, "response_time")
                writer.writerow(row)

        return output.getvalue()

    def _format_stats_for_csv(self, stats: TimingStats, metric_type: str) -> List:
        """
        Format timing statistics for CSV output.

        Args:
            stats: TimingStats object to format
            metric_type: Type of metric (connect_time, first_byte_time, response_time)

        Returns:
            List of formatted values for CSV row
        """
        return [
            metric_type,
            stats.min_value,
            stats.max_value,
            round(stats.avg_value, 2),
            round(stats.p5_value, 2),
            round(stats.p95_value, 2),
            stats.count
        ]


class OutputFormatterFactory:
    """Factory class for creating output formatters."""

    @staticmethod
    def create_formatter(format_type: str) -> OutputFormatter:
        """
        Create an output formatter of the specified type.

        Args:
            format_type: Type of formatter ('grouped' or 'csv')

        Returns:
            OutputFormatter instance

        Raises:
            ValueError: If format_type is not supported
        """
        if format_type == 'grouped':
            return GroupedFormatter()
        elif format_type == 'csv':
            return CSVFormatter()
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

    @staticmethod
    def get_supported_formats() -> List[str]:
        """Get list of supported format types."""
        return ['grouped', 'csv']