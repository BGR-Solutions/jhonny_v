# Architectural Decision Records (ADR)

This directory contains all architectural decisions made for the project, documented in MADR format.

## Format: MADR (Markdown Architectural Decision Records)

Each ADR should have the following structure:

```markdown
# ADR-NNN: [Title]

**Status**: [Proposed | Accepted | Deprecated | Superseded]

## Context

[What prompted this decision? What was the problem?]

## Decision

[What decision was made? (Declarative)]

## Consequences

### Positive
- Benefit 1
- Benefit 2

### Negative
- Risk 1
- Risk 2

## Compliance

[Does this comply with constitution/principles? Any dependencies on other ADRs?]
```

## Numbering

- Format: `001-title.md`, `002-title.md`, etc.
- Zero-padded 3-digit numbers
- Global scope (independent of milestones)
- Sequential ordering

## Index

- [ADR-001: PostgreSQL as Primary Database](./001-database-choice.md)

## How to Create an ADR

1. Create a new file: `docs/adr/NNN-your-title.md`
2. Fill in all 5 sections (Status, Context, Decision, Consequences, Compliance)
3. Use descriptive but concise language
4. Link related ADRs
5. Update this index when adding new ADRs

## References

- [MADR Format](https://adr.github.io/madr/)
- [ADR GitHub](https://github.com/adr)
