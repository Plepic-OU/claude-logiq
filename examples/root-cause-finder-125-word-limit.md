# Root Cause Finder

Analyze a GitHub issue to identify the root cause and create a failing test.

## Input
GitHub issue: $ARGUMENTS (URL or issue number)

## Process

1. **Fetch Issue**: Use `gh issue view` to get issue details (title, body, comments)
2. **Analyze Symptoms**: Extract error messages, reproduction steps, expected vs actual behavior
3. **Investigate Codebase**: Search for relevant code paths mentioned in the issue
4. **Identify Root Cause**: Determine the specific code location and condition causing the bug
5. **Create Failing Test**: Write a pytest test that reproduces the bug and fails

## Output
- Root cause summary in `temporary-files/root-cause-analysis.md`
- Failing test file in `tests/` directory

## Requirements
- Test MUST fail when run (demonstrating the bug exists)
- Test follows project conventions (pytest, AAA pattern)
