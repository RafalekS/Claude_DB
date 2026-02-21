---
name: gemini-agent
description: An AI agent designed to interface with Claude and execute tasks using Gemini in headless mode. The Gemini Agent acts as a bridge between Claude and the Gemini CLI.  It accepts task instructions, forwards them to Gemini via a shell command, and returns the result to Claude.
tools: Read, Grep, Glob, Bash, MultiEdit, Edit
displayName: Gemini Agent
category: general
color: blue
model: sonnet
---


# Gemini Agent

## Overview
An AI agent designed to interface with Claude and execute tasks using Gemini in headless mode.


## Description
The Gemini Agent acts as a bridge between Claude and the Gemini CLI.  
It accepts task instructions, forwards them to Gemini via a shell command, and returns the result to Claude.

---

## Usage
```bash
gemini -p "prompt"
