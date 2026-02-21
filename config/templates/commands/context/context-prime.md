# Context Prime

Analyze project structure and status to build comprehensive context.

## Description

Systematically examine a software project's structure, status, and organization to understand the codebase before working on tasks.

## Requirements

- Project should have a README.md
- Optional: /.context directory with status files
- Git repository recommended

## Instructions

1. **Read the README.md** file for project overview
2. **Examine context files** in /.context directory (if exists)
3. **Review file structure** using `git ls-files` or directory listing
4. **Analyze project patterns** and organization

## Output Format

Provide analysis in these five sections:

### 1. Project Overview
- Purpose and description
- Main technologies and frameworks
- Key dependencies

### 2. Current Status
- Development stage (alpha, beta, production)
- Recent changes or active work areas
- Known issues or limitations

### 3. Key Components
- Main modules and their responsibilities
- Entry points and core files
- Configuration files

### 4. File Structure Insights
- Directory organization patterns
- Naming conventions
- Code organization style

### 5. Next Steps/Recommendations
- Suggested improvements
- Missing documentation
- Potential refactoring opportunities

## Examples

```
/context-prime
/context-prime src/
```

## Important Notes

- Focus on understanding before making changes
- Identify any inconsistencies in project structure
- Note any missing or outdated documentation

## Source

From https://github.com/kingler/n8n_agent/.claude/commands
