# Infrastructure

This directory contains all infrastructure configuration and Docker orchestration.

## Files

- `docker-compose.yml` - Base configuration (networks, volumes, defaults)
- `docker-compose.core.yml` - Core services (PostgreSQL, Redis, RabbitMQ)

## Core Services

### PostgreSQL 15
- **Purpose**: Primary database
- **Port**: 5432 (configurable via `DB_PORT`)
- **Health Check**: `pg_isready`

### Redis 7
- **Purpose**: Cache, sessions, pub/sub
- **Port**: 6379
- **Health Check**: `redis-cli ping`

### RabbitMQ 3.12
- **Purpose**: Message broker for async tasks
- **Ports**: 5672 (AMQP), 15672 (Management UI)
- **Health Check**: REST API aliveness test

## Usage

Start all services:
```bash
docker compose -f docker-compose.yml -f docker-compose.core.yml up -d --pull always
```

Check service health:
```bash
docker compose ps
```

Stop services:
```bash
docker compose down
```

View logs:
```bash
docker compose logs -f postgres  # or redis, rabbitmq
```
