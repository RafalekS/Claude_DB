# Optimize Code

Optimize and improve code quality with specific focus areas.

## Description

Analyze code and provide optimization suggestions with before/after comparisons.

## Requirements

- `$ARGUMENTS` format: `path [mode] [focus]`
- **path**: Target code location
- **mode**: optimization mode (performance, readability, maintainability, all)
- **focus**: specific improvement areas

## Instructions

1. **Analyze the code** at the specified path
2. **Apply the optimization mode**:
   - **performance**: Focus on speed and efficiency
   - **readability**: Improve code clarity and documentation
   - **maintainability**: Enhance structure and modularity
   - **all**: Comprehensive optimization
3. **Emphasize the focus areas** if specified
4. **Provide detailed explanations** for each optimization
5. **Show before/after code comparisons**

## Optimization Checklist

### Performance
- [ ] Algorithm efficiency (time/space complexity)
- [ ] Unnecessary iterations or computations
- [ ] Memory allocation patterns
- [ ] Caching opportunities
- [ ] Lazy loading potential

### Readability
- [ ] Clear variable/function naming
- [ ] Appropriate comments and documentation
- [ ] Consistent formatting
- [ ] Logical code organization

### Maintainability
- [ ] Single responsibility principle
- [ ] DRY (Don't Repeat Yourself)
- [ ] Proper error handling
- [ ] Testability
- [ ] Dependency management

## Examples

```
/optimize-code src/utils performance
/optimize-code src/components/Form.tsx readability validation
/optimize-code src/ all
```

## Important Notes

- Preserve existing functionality when optimizing
- Explain trade-offs for each suggestion
- Consider backward compatibility
- Benchmark performance changes when possible

## Source

From https://github.com/kingler/n8n_agent/.claude/commands
