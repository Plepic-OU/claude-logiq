#!/bin/bash

FILE_PATH="$1"
EVENT_TYPE="$2"

# Validate FILE_PATH to prevent path traversal
if [[ "$FILE_PATH" == *".."* || ! -f "$FILE_PATH" ]]; then
    echo "Invalid FILE_PATH. Must be a regular file and not contain '..'. Skipping"
    exit 0
fi

# Only process Python files
if [[ "$FILE_PATH" != *.py ]]; then
    exit 0
fi

# Only process file modifications and creations
if [[ "$EVENT_TYPE" != "modify" && "$EVENT_TYPE" != "create" ]]; then
    exit 0
fi

echo "🔧 Formatting Python file with ruff: $FILE_PATH"

# Run ruff format on the modified file
if command -v .venv/bin/ruff &> /dev/null; then
    echo "Running: ruff format $FILE_PATH"
    .venv/bin/ruff format "$FILE_PATH" 2>&1
    RUFF_EXIT_CODE=$?
    if [[ $RUFF_EXIT_CODE -eq 0 ]]; then
        echo "✅ File formatted successfully"
    else
        echo "❌ Ruff format failed with exit code: $RUFF_EXIT_CODE" >&2
        exit 1
    fi
else
    echo "⚠️ ruff command not found. Please install ruff." >&2
    exit 1
fi