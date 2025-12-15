# Root Cause Finder

Find the root cause of a GitHub issue and produce a failing test that demonstrates the bug.

## Input

$ARGUMENTS - GitHub issue URL or issue number (e.g., `#123` or `https://github.com/owner/repo/issues/123`)

## Workflow

### Phase 1: Understand the Issue

1. Fetch the GitHub issue details using `gh issue view`
2. Extract key information:
   - Issue title and description
   - Expected behavior
   - Actual behavior
   - Steps to reproduce (if provided)
   - Error messages or stack traces
   - Any linked code references
3. Summarize the bug in clear terms

### Phase 2: Investigate the Codebase

1. Based on the issue details, identify:
   - Which components/modules are likely involved
   - Entry points for the reported behavior
   - Related error handling code
2. Search the codebase for:
   - Functions/methods mentioned in the issue
   - Error messages from the issue
   - Related functionality
3. Trace the execution path that leads to the bug
4. Document findings as you investigate

### Phase 3: Root Cause Analysis

1. Identify the exact location where the bug occurs
2. Explain WHY the bug happens (not just WHERE)
3. Consider:
   - Edge cases not handled
   - Incorrect assumptions in the code
   - Missing validation
   - Logic errors
   - Race conditions or state issues
4. Document the root cause clearly

### Phase 4: Create Failing Test

1. Write a test that:
   - Directly exercises the buggy code path
   - Fails with the current implementation
   - Will pass once the bug is fixed
   - Has a clear, descriptive name indicating the bug
2. Follow project testing conventions (pytest)
3. Place the test in the appropriate test file under `/tests`
4. Run the test to confirm it fails
5. Document what the test is verifying

## Output

Create a summary file at `temporary-files/root-cause-analysis.md` containing:

1. **Issue Summary**: Brief description of the reported bug
2. **Investigation Findings**: What was discovered during codebase exploration
3. **Root Cause**: Clear explanation of why the bug occurs
4. **Affected Code**: File paths and line numbers of buggy code
5. **Failing Test**: Path to the created test file and test name
6. **Suggested Fix**: Brief description of how to fix the bug (do NOT implement the fix)

## Important Notes

- Do NOT fix the bug - only identify the root cause and create a failing test
- The failing test is the deliverable - it must fail with current code
- Be thorough in investigation - don't jump to conclusions
- If the issue lacks reproduction steps, note assumptions made
- If unable to reproduce, document what was tried and why it didn't work

## Example Usage

```
/root-cause-finder #42
/root-cause-finder https://github.com/owner/repo/issues/42
```
