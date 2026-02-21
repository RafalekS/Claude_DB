# Project Initialization

Initialize and set up new or existing projects with standard structure.

## Description

Create new projects or enhance existing ones with proper structure, configuration, and documentation.

## Requirements

- `$ARGUMENTS` format: `[command] [type] [name]`
- **command**: init, init-existing, generate-structure, setup-dev
- **type**: Project type (react, node, python, etc.)
- **name**: Project name

## Commands

### 1. init_project
Create a new project with standard structure:
- Essential files and configurations
- Comprehensive README with setup guidance
- Standard directory structure
- Initial configuration files

### 2. init_existing_project
Analyze current project and create documentation:
- Identify gaps in structure
- Suggest improvements for industry standards
- Generate missing documentation
- Update configuration files

### 3. generate_project_structure
Build templated project structure:
- Standard directories (src, tests, docs, config)
- Starter files following best practices
- Framework-specific organization
- Sample code and tests

### 4. setup_development_environment
Configure development settings:
- Linting configuration (ESLint, Prettier, etc.)
- Testing setup (Jest, pytest, etc.)
- Build configuration
- Sample .env documentation
- Git hooks (husky, pre-commit)

## Examples

```
/project-init init react my-app
/project-init init-existing
/project-init generate-structure node api-server
/project-init setup-dev python
```

## Standard Project Structure

```
project/
├── src/           # Source code
├── tests/         # Test files
├── docs/          # Documentation
├── config/        # Configuration files
├── scripts/       # Build/deploy scripts
├── .github/       # GitHub workflows
├── README.md
├── .gitignore
├── .env.example
└── package.json / pyproject.toml / etc.
```

## Important Notes

- Follow framework-specific conventions
- Include CI/CD configuration templates
- Add appropriate license file
- Configure editor settings (.editorconfig, .vscode/)

## Source

From https://github.com/kingler/n8n_agent/.claude/commands
