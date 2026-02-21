---
name: codex
description: Use when user asks to run Codex CLI (codex exec, codex resume) or references OpenAI Codex for code analysis, refactoring, or automated editing.
allowed-tools: Bash, Read
---

# Codex CLI Integration

Delegate code analysis, refactoring, and editing tasks to OpenAI Codex CLI.

## Prerequisites

- Codex CLI installed and in PATH
- Valid Codex credentials configured
- Verify with: `codex --version`

## Running a Task

1. **Request Model Choice**: `gpt-5-codex` or `gpt-5`
2. **Select Reasoning Effort**: `high`, `medium`, or `low`
3. **Choose Sandbox Mode**:
   - `read-only` - For analysis tasks
   - `workspace-write` - For editing tasks
   - `danger-full-access` - For network access

## Command Structure

```bash
codex exec --skip-git-repo-check --model MODEL --reasoning LEVEL --sandbox MODE "prompt" 2>/dev/null
```

**Important**: Always append `2>/dev/null` to suppress thinking tokens (stderr) to prevent context bloat.

## Resume Sessions

To continue a previous session:
```bash
echo "follow-up prompt" | codex exec --skip-git-repo-check resume --last 2>/dev/null
```

No additional flags during resume unless user specifies model/reasoning changes.

## Quick Reference

| Use Case | Sandbox Mode |
|----------|-------------|
| Code analysis | `read-only` |
| File edits | `workspace-write` |
| Network access | `danger-full-access` |

## Error Handling

- Stop on non-zero exit codes
- Request user permission before high-impact flags
- Summarize warnings and adjust approach

## Following Up

After each command:
1. Confirm next steps with user
2. Restate chosen parameters when proposing follow-ups

## Source

Clone from https://github.com/skills-directory/skill-codex
