import argparse
import os
import sys
from pathlib import Path
from typing import Optional

try:
    import isodate
except ImportError:
    print(
        "Error: isodate package not found. Please install with: pip install isodate",
        file=sys.stderr,
    )
    sys.exit(1)


def validate_iso8601_duration(duration_str: str) -> Optional[str]:
    """
    Validate ISO 8601 duration format and return error message if invalid.

    Args:
        duration_str: The duration string to validate (e.g., 'PT5M', 'PT1H')

    Returns:
        None if valid, error message string if invalid
    """
    # Check for obvious negative duration patterns first
    if "-" in duration_str:
        return f"Duration must be positive (negative durations not allowed): {duration_str}"

    try:
        duration = isodate.parse_duration(duration_str)
        if duration.total_seconds() <= 0:
            return f"Duration must be positive, got: {duration_str}"
        return None
    except isodate.ISO8601Error as e:
        # Provide more user-friendly error messages
        return f"Invalid ISO 8601 duration format: '{duration_str}'. Use formats like PT5M, PT1H, P1D"
    except Exception as e:
        return f"Error parsing duration '{duration_str}': {e}"


def validate_log_file_path(file_path: str) -> Optional[str]:
    """
    Validate that the log file path exists and is readable.

    Args:
        file_path: Path to the log file

    Returns:
        None if valid, error message string if invalid
    """
    path = Path(file_path)

    if not path.exists():
        return f"Log file does not exist: {file_path}"

    if not path.is_file():
        return f"Path is not a file: {file_path}"

    if not os.access(path, os.R_OK):
        return f"Log file is not readable: {file_path}"

    return None


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Claude LogIQ - NGINX Plus log analysis tool for upstream timing metrics aggregation",
        epilog="""
Examples:
  %(prog)s --period PT5M nginxplus_json_logs.txt
    Analyze logs with 5-minute time periods, output in grouped format

  %(prog)s --period PT1H --format csv access.log
    Analyze logs with 1-hour periods, output in CSV format

  %(prog)s --period PT30S /var/log/nginx/plus.json
    Analyze logs with 30-second periods from absolute path

ISO 8601 Duration Examples:
  PT1M     - 1 minute
  PT5M     - 5 minutes
  PT30M    - 30 minutes
  PT1H     - 1 hour
  PT2H     - 2 hours
  P1D      - 1 day

For more information on ISO 8601 duration format:
https://en.wikipedia.org/wiki/ISO_8601#Durations
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--version", action="version", version="claude-logiq 0.1.0")

    parser.add_argument(
        "--period",
        required=True,
        metavar="DURATION",
        help="Time period for aggregation in ISO 8601 duration format (e.g., PT5M for 5 minutes, PT1H for 1 hour)",
    )

    parser.add_argument(
        "--format",
        choices=["grouped", "csv"],
        default="grouped",
        help="Output format (default: %(default)s). 'grouped' provides human-readable sections, 'csv' provides machine-readable data",
    )

    parser.add_argument(
        "log_file_path",
        metavar="LOG_FILE_PATH",
        help="Path to the NGINX Plus JSON log file to analyze",
    )

    return parser


def main() -> None:
    """Main entry point for the CLI application."""
    parser = create_parser()
    args = parser.parse_args()

    # Validate ISO 8601 duration
    duration_error = validate_iso8601_duration(args.period)
    if duration_error:
        print(f"Error: {duration_error}", file=sys.stderr)
        print("\nUse --help to see valid duration format examples.", file=sys.stderr)
        sys.exit(1)

    # Validate log file path
    file_error = validate_log_file_path(args.log_file_path)
    if file_error:
        print(f"Error: {file_error}", file=sys.stderr)
        sys.exit(1)

    # Parse the duration for internal use
    try:
        parsed_duration = isodate.parse_duration(args.period)
        duration_seconds = parsed_duration.total_seconds()
    except Exception as e:
        print(f"Error: Failed to parse duration: {e}", file=sys.stderr)
        sys.exit(1)

    # Process the log file
    try:
        from .log_parser import LogParser
        from .time_aggregator import TimeAggregator
        from .output_formatter import OutputFormatterFactory

        # Initialize components
        parser = LogParser()
        aggregator = TimeAggregator(duration_seconds)
        formatter = OutputFormatterFactory.create_formatter(args.format)

        # Parse log entries
        print("Parsing log file...", file=sys.stderr)
        log_entries = list(parser.parse_log_file(args.log_file_path))

        # Get parsing statistics
        stats = parser.get_parsing_stats()
        print(
            f"Parsed {stats['parsed_entries']} entries, skipped {stats['skipped_entries']}, errors {stats['error_entries']}",
            file=sys.stderr,
        )

        if not log_entries:
            print(
                "No valid log entries found with upstream timing data.", file=sys.stderr
            )
            sys.exit(1)

        # Aggregate metrics
        print("Aggregating metrics...", file=sys.stderr)
        aggregated_buckets = aggregator.aggregate_metrics(log_entries)

        if not aggregated_buckets:
            print("No upstream timing data found after aggregation.", file=sys.stderr)
            sys.exit(1)

        # Format and output results
        output = formatter.format_results(aggregated_buckets)
        print(output)

    except ImportError as e:
        print(
            f"Error: Failed to import log processing components: {e}", file=sys.stderr
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error: Log processing failed: {e}", file=sys.stderr)
        sys.exit(1)
