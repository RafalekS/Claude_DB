---
name: example-skill
description: Example skill template showing proper structure for Claude Code skills
allowed-tools: Read, Grep, Glob
---

# Example Skill

This skill demonstrates the proper structure for Claude Code skills.

## Purpose

This is an example skill template. Copy and customize it for your specific use case.

## Usage

Invoke this skill when you need to demonstrate skill structure or create a new skill.

## Features

- Proper YAML frontmatter with name and description
- Clear markdown structure
- Example sections for organization

## Step-by-Step Process

1. **Step 1**: Copy this template file
2. **Step 2**: Update the frontmatter with your skill's name and description
3. **Step 3**: Customize the content sections below

## Important Notes

- The `name` field is required (lowercase letters, numbers, and hyphens only, max 64 characters)
- The `description` field is required (max 1024 characters)
- The `allowed-tools` field is optional - restricts which tools Claude can use when this skill is active
- The description should specify both functionality and usage triggers

## Best Practices

- Keep skill names descriptive and specific
- Document when the skill should be invoked
- List any prerequisites or requirements
