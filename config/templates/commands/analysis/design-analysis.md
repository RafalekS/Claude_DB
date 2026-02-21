# Design Analysis

Comprehensive design system and UI/UX analysis commands.

## Description

Evaluate design systems, CSS architecture, and UI implementation against best practices.

## Requirements

- `$ARGUMENTS` should specify the path and optionally the component type
- Format: `path [component-type]`

## Instructions

Choose the appropriate analysis type:

### 1. Analyze Design System
Evaluate alignment with atomic design principles:
- **Atoms**: Basic elements (buttons, inputs, labels)
- **Molecules**: Simple component groups
- **Organisms**: Complex UI sections
- **Templates**: Page layouts
- Review token naming conventions across CSS layers

### 2. Evaluate Design Quality
Grade design across categories (A-F scale):
- Color palette and contrast
- Layout and grid system
- Typography hierarchy
- Navigation and information architecture
- Accessibility compliance
- Spacing and alignment consistency

### 3. Audit Design Tokens
- Verify token hierarchy
- Check cross-platform consistency (web, mobile)
- Validate naming standardization
- Identify unused or duplicate tokens

### 4. Analyze CSS Architecture
- Review CSS organization and methodology
- Check token usage alignment
- Identify specificity problems
- Evaluate design system integration

### 5. Comprehensive Design Review
Combines all approaches to assess:
- Token structure and usage
- CSS architecture quality
- Component implementation
- Accessibility compliance
- Visual consistency
- User journey flows
- Interaction patterns

## Examples

```
/design-analysis src/components button
/design-analysis src/styles
/design-analysis . comprehensive
```

## Important Notes

- Provide prioritized improvement recommendations
- Include specific code/CSS examples
- Reference design system documentation when available
- Consider responsive design requirements

## Source

From https://github.com/kingler/n8n_agent/.claude/commands
