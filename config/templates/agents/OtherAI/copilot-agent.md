---
name: copilot-agent
displayName: CopilotAgent
description: description: An AI agent designed to interface with Claude and execute tasks using Copilot in headless mode. The Copilot Agent acts as a bridge between Claude and the Copilot CLI.  It accepts task instructions, forwards them to Copilot via a shell command, and returns the result to Claude.
category: coding
color: magenta
model: sonnet
tools: Read, Grep, Glob, Bash, Edit
---


## Usage
```bash
copilot -p "prompt"


## Instructions
Provide detailed instructions for the agent to follow when invoked.

### Best Practices
- Provide clear, actionable guidance
