# Project overview

This project is command line tool for analyzing nginxplus log files.
All input and output is text based, meant to be used in a terminal.

# Technologies used
- Python 3.11+
- Ruff for formatting (it runs as post hook in Claude automatically)
- Pytest for testing
- Astral UV (Python package manager and project tool)
- Bash tools

# Subagents
User subagents PROACTIVELY!
- log-structure-analyzer: Use for analyzing log file structure. Meant for development use.
- qa-validator: Use for validating development changes.
- cli-expert: Use when developing command line interface (CLI) related tasks.
- python-developer: Use for other development tasks, which are not connected to CLI.

# Project structure and important files

- `nginxplus_json_logs.txt`: example log file used for development and testing
- `pyproject.toml`: UV project configuration with dependencies and CLI entry point
- `src/claude_logiq/__init__.py`: Main CLI module with argparse interface

- `/src`: Source code for the project.
- `/tests`: Test files directory for the project.

# Running the CLI

Use UV to run the CLI tool:
- `uv run claude-logiq` - Run the main CLI
- `uv run claude-logiq --help` - Show help
- `uv run claude-logiq --version` - Show version

## `temporary-files`

When producing reports or other files, place them here, unless told otherwise.
Not commited into version control.

- `log-structure.md`: describes the structure of the log file
- `feature-docs.md`: the feature documentation file


