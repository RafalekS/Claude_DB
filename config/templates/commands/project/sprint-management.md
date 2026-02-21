# Sprint Management

Agile sprint planning, story management, and progress tracking commands.

## Description

Manage sprints including initialization, story creation, analysis, decomposition, and progress tracking.

## Requirements

- `$ARGUMENTS` format: `[command] [options]`
- **command**: init, stories, analyze, decompose, track

## Commands

### 1. init_sprint
Initialize a new sprint:
- Define sprint goals and objectives
- Set sprint duration (typically 1-2 weeks)
- Establish team capacity
- Identify sprint commitments

### 2. generate_sprint_stories
Create user stories aligned with project priorities:
- Write clear user story format (As a... I want... So that...)
- Define acceptance criteria
- Assign story points (Fibonacci: 1, 2, 3, 5, 8, 13)
- Map dependencies between stories

### 3. analyze_stories
Review sprint stories for quality:
- Verify INVEST criteria (Independent, Negotiable, Valuable, Estimable, Small, Testable)
- Identify missing details or ambiguities
- Flag potential implementation challenges
- Suggest refinements

### 4. decompose_stories
Break down complex stories into tasks:
- Create technical tasks with effort estimates
- Provide implementation guidance for complex items
- Identify high-risk tasks requiring extra attention
- Suggest task sequencing

### 5. track_sprint_implementation
Monitor sprint progress:
- Review completed vs remaining work
- Identify blockers and risks
- Calculate burndown metrics
- Recommend sprint adjustments if needed

## Examples

```
/sprint-management init 2-week "Implement user authentication"
/sprint-management stories auth-feature
/sprint-management analyze
/sprint-management decompose US-123
/sprint-management track
```

## Story Template

```markdown
## [US-XXX] Story Title

**As a** [user type]
**I want** [functionality]
**So that** [benefit]

### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

### Story Points: X
### Dependencies: US-YYY, US-ZZZ
```

## Important Notes

- Keep stories small enough to complete in one sprint
- Ensure acceptance criteria are testable
- Consider definition of done for all stories
- Track velocity for future sprint planning

## Source

From https://github.com/kingler/n8n_agent/.claude/commands
