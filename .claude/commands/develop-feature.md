# Task summary

Goal is to develop a new feature. This involves planning, coding, testing.
Your goal is to be the main facilitator for completion of the feature.

## Using subagents
Use subagents proactively.
* Use `cli-expert` subagent whenever task is about command line interface (CLI), like arguments, displaying output, etc.
* Use `python-developer` subagent whenever task about some other aspect of development, non-CLI.
* Use `qa-validator` to validate developers tasks.

## Feature document
When there is no feature document in temporary directory (`feature-docs.md`), then ask user to create one first.
Don't start work without the feature document.

## Other important notes
You are building log analyzer, so make sure to mention the `temporary-files/log-structure.md` to sub-agents.

When you finish the task, summarize the work done in `temporary-files/summary-of-work-done.md`.

# Main task loop
* Track your plan/TODO in `temporary-files/implementation-plan.md`.
* If the file already exists, read it and continue from there.
* Whenever you finish a task, ask yourself "What is the next step?" and update the plan file with done tasks.
* If new tasks are needed, add them to the plan file.