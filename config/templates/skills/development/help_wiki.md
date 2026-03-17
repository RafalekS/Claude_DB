---
name: help_wiki
description: Generate a complete, professional wiki-style help system for the current project by scanning code, documentation, and configuration. Generate comprehensive help documentation
---

# Help Wiki Generation Skill

## Objective

Create a comprehensive, professional, wiki-style help system for the current project. The output should resemble production-grade documentation typically found in mature software projects.

---

## Core Responsibilities

You MUST:

1. **Scan the entire project**
   - Source code (all languages)
   - Configuration files
   - Build scripts
   - Dependency manifests
   - Documentation (README, docs/, comments)

2. **Understand the project context**
   - Purpose and domain of the application
   - Architecture and design patterns
   - Key components and their relationships

3. **Extract implicit knowledge**
   - Infer functionality from code
   - Identify undocumented behavior
   - Detect common usage patterns

---

## Output Requirements

Generate a structured wiki-style help system with the following sections.

### 1. Overview
- Project name
- Purpose
- Key features
- Target users

### 2. Getting Started
- Installation steps
- Prerequisites
- Setup instructions
- First run example

### 3. Architecture
- High-level system design
- Component breakdown
- Data flow
- External dependencies

### 4. Code Structure
- Directory layout
- Key modules and files
- Responsibilities of each major component

### 5. Features & Functionality
For each feature:
- Description
- How it works
- Inputs/outputs
- Example usage

### 6. Configuration
- Config files and their locations
- All parameters and options
- Environment variables
- Default values and overrides

### 7. CLI / API Reference
If applicable:
- Commands
- Flags/options
- Endpoints
- Request/response formats

### 8. GUI (if applicable)
- Screens and layout
- User interactions
- Navigation flow

### 9. Workflows / Use Cases
- Common user scenarios
- Step-by-step usage flows

### 10. Troubleshooting
- Common errors
- Root causes
- Fixes

### 11. FAQ
- Concise answers to likely user questions

### 12. Development Guide
- How to build
- How to test
- Contribution guidelines

### 13. Advanced Topics
- Internals
- Performance considerations
- Extensibility

---

## Formatting Rules

- Use Markdown with clear hierarchy (#, ##, ###)
- Use code blocks for commands and examples
- Use tables where appropriate
- Keep sections modular and linkable

---

## Wiki Generation Strategy

You SHOULD:

1. Start with a global scan of the repository
2. Build a mental model of the system
3. Group related functionality
4. Generate documentation incrementally
5. Cross-reference sections where useful

---

## Tooling (Optional but Recommended)

You MAY use external tools to enhance output:

### Pandoc
- Convert Markdown to:
  - HTML
  - PDF
  - Static wiki formats

Example:

```
pandoc help.md -o help.html
pandoc help.md -o help.pdf
```

### Static Site Generators
- MkDocs
- Docusaurus
- Hugo

### Diagram Tools
- Mermaid (for architecture diagrams)

---

## Output Format Options

Generate one or more of the following:

1. **Single Markdown file** (default)
2. **Multi-file wiki structure**
   - /docs
   - /wiki
   - Section-based files

3. **Static site (if tools available)**

---

## Quality Requirements

- Be precise and technical
- Avoid vague descriptions
- Prefer concrete examples
- Ensure completeness over brevity
- Do not omit important components

---

## Constraints

- Do NOT hallucinate features not present in code
- Clearly mark assumptions
- If something is unclear, infer cautiously and state it

---

## Execution Trigger

When invoked:

1. Scan project
2. Analyze structure
3. Extract knowledge
4. Generate full help wiki
5. Output in Markdown (or requested format)

---

## End of Skill

