# Quality Assurance

Comprehensive QA commands for code quality, testing, performance, and security.

## Description

Perform various quality assurance tasks including static analysis, test generation, performance testing, and security scanning.

## Requirements

- `$ARGUMENTS` format: `[command] path [options]`
- **command**: analyze, generate-tests, performance, security
- **path**: Target code location

## Commands

### 1. analyze_code_quality
Static analysis against standard metrics and best practices:
- Code smells and anti-patterns
- Potential bugs and edge cases
- Complexity metrics (cyclomatic, cognitive)
- Code coverage gaps
- Documentation completeness

### 2. generate_tests
Create comprehensive unit tests:
- **Happy path scenarios**: Normal operation
- **Edge cases**: Boundary conditions
- **Error handling**: Exception paths
- **Mocking**: External dependencies
- Follow testing best practices (AAA pattern, isolation)

### 3. run_performance_tests
Analyze code performance:
- Identify bottlenecks
- Measure execution time
- Analyze memory usage
- Check resource utilization
- Suggest optimization opportunities

### 4. scan_security
Vulnerability scanning:
- **Injection vulnerabilities**: SQL, XSS, command injection
- **Authentication flaws**: Weak auth, session management
- **Data exposure**: Sensitive data leaks
- **Dependency vulnerabilities**: Known CVEs
- Remediation guidance for each finding

## Examples

```
/quality-assurance analyze src/
/quality-assurance generate-tests src/utils/helpers.ts
/quality-assurance performance src/api/
/quality-assurance security src/auth/
```

## Output Format

For each analysis, provide:
1. **Summary**: Overview of findings
2. **Details**: Specific issues with locations
3. **Severity**: Critical/High/Medium/Low ratings
4. **Recommendations**: Actionable fixes
5. **Code Examples**: Before/after when applicable

## Important Notes

- Prioritize findings by impact and exploitability
- Consider false positives in static analysis
- Generate tests that are maintainable and clear
- Security findings should include OWASP references

## Source

From https://github.com/kingler/n8n_agent/.claude/commands
