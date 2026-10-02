# ADR-001: PostgreSQL as Primary Database

**Status**: Accepted

## Context

v0.1 infrastructure requires a reliable, production-grade database for storing application data. The team needed to choose between multiple options (PostgreSQL, MySQL, MongoDB) considering reliability, ACID compliance, JSON support, and ecosystem maturity.

## Decision

We chose **PostgreSQL 15** as the primary database for all applications in v0.1.

**Rationale**:
- ACID compliance ensures data integrity
- Excellent JSON/JSONB support for flexible schemas
- Mature ecosystem with strong community support
- Docker image widely available and well-maintained
- Performance suitable for v0.1 scale

## Consequences

### Positive
- Strong consistency guarantees (ACID)
- Flexible data modeling with JSON support
- Excellent query optimization capabilities
- Built-in replication and backup tools
- Large community and extensive documentation

### Negative
- Requires database client libraries in applications
- Vertical scaling limitations (eventual need for sharding)
- Operational overhead for backup/recovery management
- Connection pooling configuration needed for high-concurrency

## Compliance

✅ Aligns with Infrastructure Core principle (v0.1 milestone)  
✅ Follows 12-factor app guidelines (external data store)  
✅ No conflicts with other ADRs

**Related**:
- ISSUE-101: Monorepo Base Structure
- ISSUE-102: v0.1 Observability Phase 2 (database metrics)

**Next Steps**:
- ADR-002: Redis for Caching Strategy (coming soon)
- ADR-003: RabbitMQ for Async Tasks (coming soon)
