# Issue Templates & Guidelines

This directory guides how to document issues and problems in the project.

## Issue Types

### Bug Report
Use for unexpected behavior or failures.

**Template**:
```markdown
## Description
[Brief description of the bug]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- OS: [macOS/Linux/Windows]
- Docker Version: [e.g., 24.0]
- Branch: [feature/xxx]
```

### Feature Request
Use for new functionality or enhancements.

**Template**:
```markdown
## Description
[What is needed and why]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Related Issues
[Link to related issues]
```

### Documentation
Use for missing or unclear documentation.

**Template**:
```markdown
## Topic
[What needs documentation]

## Current State
[What exists now, if anything]

## Proposed Content
[Outline of what should be documented]
```

## Guidelines

1. **Be specific**: Include exact error messages, logs, commands used
2. **Be reproducible**: Provide steps anyone can follow
3. **Link context**: Reference ADRs, milestones, related issues
4. **Use labels**: Tag issues appropriately (bug, feature, documentation, etc.)
5. **Close when done**: Update issue status when resolved

## Tracking

Issues are tracked in the GitHub Issues tab. Reference them in commits as `ISSUE-XXX` (e.g., `ISSUE-101`).
