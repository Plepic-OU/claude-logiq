---
name: review-pull-request
description: Review current branch changes compared to main branch. Use when the user wants a code review of their branch before merging, including quality assessment, bug detection, and improvement suggestions.
---

# Review Pull Request

Review current branch changes compared to main branch.

## What it does

1. Analyzes git diff between current branch and main branch
2. Reviews code changes for:
   - Code quality and best practices
   - Potential bugs or issues
   - Adherence to project conventions
   - Performance considerations
   - Test coverage
3. Provides structured feedback with specific line references
4. Suggests improvements where applicable

## Prerequisites

- Current branch should be checked out
- Changes should be committed to the branch
- Main branch should exist as comparison base

## Output

The review will provide:
- Summary of changes by file and type
- Code quality assessment
- Specific issues found with file:line references
- Suggestions for improvements
- Overall readiness assessment for merge
