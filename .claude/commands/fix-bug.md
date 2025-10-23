# Task summary

Goal is to fix a known bug by following a systematic approach: reproduce, fix, validate.
You are the main facilitator for completing the bug fix.

## Bug Fix Strategy

Follow this three-phase approach:

### Phase 1: Reproduce the Bug
1. Gather bug details from the user:
   - What is the expected behavior?
   - What is the actual behavior?
   - Steps to reproduce
   - Any error messages or stack traces
2Confirm the bug is reproducible before proceeding

### Phase 2: Fix the Bug
1. Based on root cause analysis, develop a fix
2. Apply the fix to the codebase
3. Document what was changed and why in your tracking file

### Phase 3: Validate the Fix
1. Re-test the original reproduction steps
2. Verify the bug no longer occurs
3. Check for any side effects or regressions
4. Confirm with user that the fix resolves their issue

## Important Notes

- **No automated tests**: Creating automated tests is NOT in scope for this command
- Track progress in `temporary-files/bug-fix-progress.md`

## Workflow

1. Ask user for bug details if not already provided
2. Create tracking file `temporary-files/bug-fix-progress.md` with phases
3. Execute Phase 1: Reproduce
4. Execute Phase 2: Fix
5. Execute Phase 3: Validate
6. Create summary file with results
