# Introduction
This project is example project for showcasing Claude Code features.

#### Notable Claude features present
- `CLAUDE.md` - the master prompt
- `.claude/settings.json` - project settings, including edit hook and default permissions
- `.claude/ruff_format_hook.sh` - hook runnable that formats python files with ruff on edit
- `.claude/agents/` - Example sub agents
- `.claude/commands/` - Example slash commands

# How to use in your project
1. Run `claude` and then `/init` inside the project root directory.
2. Copy any of the above files you want into your project in the appropriate locations.


### MCP Servers
Use `claude mcp` command to add or remove Model Context Protocol (MCP) servers.

#### Context7 example
  * Optionally register in https://context7.com/ to get API key. Can be used with lower rate limits without one too.
  * Run `claude mcp add --transport http context7 https://mcp.context7.com/mcp --header "CONTEXT7_API_KEY: $CONTEXT7_API_KEY"`


# Running this project
* Make sure Python 3.12+ is installed
* Make sure `Astral uv` is installed (https://docs.astral.sh/uv/getting-started/installation/)
* Run `uv init`
* Use `uv run claude-logiq` command
* Example: `uv run claude-logiq --period PT5M --format grouped nginxplus_json_logs.txt`