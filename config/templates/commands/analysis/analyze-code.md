# Analyze Code

Perform comprehensive code analysis on the specified path.

## Description

Analyze code to identify code smells, potential bugs, architectural issues, and provide improvement recommendations.

## Requirements

- `$ARGUMENTS` should contain the target directory or file path
- Optional: specify analysis depth (shallow, medium, deep)

## Instructions

1. **Examine the target code** at the specified path
2. **Identify code quality issues**:
   - Code smells and anti-patterns
   - Potential bugs and edge cases
   - Security vulnerabilities
   - Performance bottlenecks
3. **Analyze architecture**:
   - Design pattern usage
   - Coupling and cohesion
   - SOLID principles adherence
4. **Generate recommendations** with practical code examples

## Examples

```
/analyze-code src/components
/analyze-code src/utils/helpers.ts deep
```

## Important Notes

- Provide before/after code comparisons where applicable
- Prioritize issues by severity (critical, high, medium, low)
- Include actionable suggestions, not just observations
- Consider the project's existing patterns and conventions

## Source

From https://github.com/kingler/n8n_agent/.claude/commands
