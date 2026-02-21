# Example Command Template

## Simple Command (No Arguments)

Perform a specific task when this command is invoked.

**Instructions:**
1. [First step]
2. [Second step]
3. [Third step]

**Important Notes:**
- No YAML frontmatter needed for commands
- The entire file content becomes the prompt
- Use clear, concise instructions
- Commands are invoked with `/command-name`

---

## Command with Arguments Template

Find and process $ARGUMENTS.

**Steps:**
1. Understand the $ARGUMENTS provided by the user
2. [Second step using $ARGUMENTS]
3. [Third step with results]

**Argument Usage:**
- Use `$ARGUMENTS` placeholder anywhere in the command
- Everything after the command name becomes $ARGUMENTS
- Example: `/process fix bug #123` → $ARGUMENTS = "fix bug #123"

**Best Practices:**
- Provide clear instructions on what $ARGUMENTS should contain
- Include validation steps for $ARGUMENTS
- Describe expected format and examples

**Example Usage:**
```
/command-name argument1 argument2
```

---

## Multi-Step Command Template

This command performs multiple complex steps.

**Step 1: Analysis**
- Analyze $ARGUMENTS or current context
- Identify key requirements
- Validate inputs

**Step 2: Processing**
- Process the identified requirements
- Apply necessary transformations
- Generate intermediate results

**Step 3: Output**
- Format and present results
- Provide summary
- Suggest next steps

**Success Criteria:**
- [ ] All inputs validated
- [ ] Processing completed without errors
- [ ] Results properly formatted
- [ ] User understands next steps

**Notes:**
- Commands can use markdown formatting
- Include checklists, code blocks, and other formatting
- Keep prompts focused and actionable
