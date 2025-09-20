"""
NGINX Plus log parser for extracting upstream timing metrics.

This module provides functionality to parse NGINX Plus JSON log files and extract
upstream timing data for analysis.
"""

import json
import logging
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class UpstreamMetrics:
    """Represents timing metrics for a single upstream server."""

    pool_name: str
    server: str
    timestamp: int  # Unix milliseconds
    connect_time: Optional[int] = None  # milliseconds
    first_byte_time: Optional[int] = None  # milliseconds
    response_time: Optional[int] = None  # milliseconds


@dataclass
class LogEntry:
    """Represents a parsed log entry with timestamp and upstream metrics."""

    timestamp: int  # Unix milliseconds
    upstream_metrics: List[UpstreamMetrics]


class LogParser:
    """Parser for NGINX Plus JSON log files with upstream timing data."""

    def __init__(self):
        self.parsed_entries = 0
        self.skipped_entries = 0
        self.error_entries = 0

    def parse_log_file(self, file_path: str) -> Iterator[LogEntry]:
        """
        Parse a log file and yield LogEntry objects.

        Args:
            file_path: Path to the NGINX Plus JSON log file

        Yields:
            LogEntry: Parsed log entries with upstream timing data

        Raises:
            FileNotFoundError: If the log file doesn't exist
            IOError: If there are issues reading the file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        entry = self._parse_log_line(line)
                        if entry:
                            self.parsed_entries += 1
                            yield entry
                        else:
                            self.skipped_entries += 1
                    except Exception as e:
                        self.error_entries += 1
                        logger.warning(
                            f"Error parsing line {line_num} in {file_path}: {e}"
                        )
                        continue

        except FileNotFoundError:
            raise FileNotFoundError(f"Log file not found: {file_path}")
        except IOError as e:
            raise IOError(f"Error reading log file {file_path}: {e}")

    def _parse_log_line(self, line: str) -> Optional[LogEntry]:
        """
        Parse a single log line and extract upstream timing data.

        Args:
            line: JSON log line as string

        Returns:
            LogEntry if the line contains valid upstream data, None otherwise

        Raises:
            json.JSONDecodeError: If the line is not valid JSON
        """
        try:
            log_data = json.loads(line)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON: {e}", line, e.pos)

        # Extract timestamp
        timestamp = log_data.get('timestamp')
        if not isinstance(timestamp, int):
            logger.debug("Skipping entry: missing or invalid timestamp")
            return None

        # Extract upstream metrics from stream.upstreams
        upstream_metrics = []
        stream_data = log_data.get('stream', {})
        upstreams_data = stream_data.get('upstreams', {})

        for pool_name, pool_data in upstreams_data.items():
            if not isinstance(pool_data, dict):
                continue

            peers = pool_data.get('peers', [])
            if not isinstance(peers, list):
                continue

            for peer in peers:
                if not isinstance(peer, dict):
                    continue

                # Extract server identifier
                server = peer.get('server', 'unknown')

                # Extract timing metrics
                connect_time = self._extract_timing_metric(peer, 'connect_time')
                first_byte_time = self._extract_timing_metric(peer, 'first_byte_time')
                response_time = self._extract_timing_metric(peer, 'response_time')

                # Only create metrics entry if at least one timing value is present
                if any(t is not None for t in [connect_time, first_byte_time, response_time]):
                    upstream_metrics.append(
                        UpstreamMetrics(
                            pool_name=pool_name,
                            server=server,
                            timestamp=timestamp,
                            connect_time=connect_time,
                            first_byte_time=first_byte_time,
                            response_time=response_time,
                        )
                    )

        # Return LogEntry only if we have upstream metrics
        if upstream_metrics:
            return LogEntry(timestamp=timestamp, upstream_metrics=upstream_metrics)

        return None

    def _extract_timing_metric(self, peer_data: dict, metric_name: str) -> Optional[int]:
        """
        Extract a timing metric from peer data, handling various data types.

        Args:
            peer_data: Dictionary containing peer information
            metric_name: Name of the timing metric to extract

        Returns:
            Timing value in milliseconds, or None if not available/invalid
        """
        value = peer_data.get(metric_name)

        if value is None:
            return None

        # Handle different data types
        if isinstance(value, (int, float)):
            # Convert to int (milliseconds)
            return int(value) if value >= 0 else None

        # Skip invalid data types
        return None

    def get_parsing_stats(self) -> Dict[str, int]:
        """
        Get parsing statistics.

        Returns:
            Dictionary with parsing statistics
        """
        return {
            'parsed_entries': self.parsed_entries,
            'skipped_entries': self.skipped_entries,
            'error_entries': self.error_entries,
            'total_processed': self.parsed_entries + self.skipped_entries + self.error_entries
        }

    def reset_stats(self) -> None:
        """Reset parsing statistics counters."""
        self.parsed_entries = 0
        self.skipped_entries = 0
        self.error_entries = 0