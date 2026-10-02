# Applications

This directory contains all applications in the monorepo.

## Structure

Each application should have its own subdirectory with:
- `src/` - Source code
- `tests/` - Test files
- `Dockerfile` - Container definition
- `package.json` or `requirements.txt` - Dependencies

## Examples

- `backend/` - REST API / GraphQL server
- `workers/` - Async job processors
- `cli/` - Command-line tools

## Getting Started

1. Create a new application directory: `mkdir -p apps/myapp/src`
2. Add source code and Dockerfile
3. Update the root `docker-compose.yml` to include your service
