# OTF API - Monorepo

This repository contains both Python and TypeScript libraries for accessing the OrangeTheory Fitness API.

## Overview

- **Python Library** (`python/`): Source of truth with comprehensive Pydantic models
- **TypeScript Library** (`typescript/`): Auto-generated client with custom improvements
- **Shared Schema** (`schema/`): OpenAPI specification generated from Python models

## Quick Start

### Python Library
```bash
cd python
uv sync
uv run python -c "from otf_api import Otf; print('Python library ready!')"
```

### TypeScript Library  
```bash
cd typescript
npm install
npm run build
```

## Development

### Setup
```bash
# Install Python dependencies
npm run install:python

# Install TypeScript dependencies  
npm run install:typescript
```

### Building
```bash
# Build both libraries
npm run build

# Build individual libraries
npm run build:python
npm run build:typescript
```

### Testing
```bash
# Test both libraries
npm run test

# Test individual libraries
npm run test:python
npm run test:typescript
```

### Schema Generation & Sync
```bash
# Generate OpenAPI schema from Python models
npm run generate-schema

# Generate TypeScript types from schema
npm run generate-ts

# Full sync: schema -> types
npm run sync
```

### Linting
```bash
# Lint both codebases
npm run lint

# Lint individual codebases
npm run lint:python
npm run lint:typescript
```

## Structure

- `python/`: Python library (source of truth)
  - `src/otf_api/`: Main library code
  - `tests/`: Python tests
  - `examples/`: Usage examples
- `typescript/`: TypeScript library
  - `src/`: TypeScript source code
  - `src/generated/`: Auto-generated types
  - `test/`: TypeScript tests
- `schema/`: OpenAPI specifications
- `scripts/`: Build and generation scripts
- `docs/`: Documentation

## Releases

Both libraries maintain synchronized versions. Python is the source of truth for version numbers.

## Contributing

1. Make changes to Python models (source of truth)
2. Run `npm run sync` to update TypeScript types
3. Update TypeScript client code if needed
4. Test both libraries
5. Create PR

## Authentication

Both libraries support multiple authentication methods:
- Environment variables: `OTF_EMAIL` and `OTF_PASSWORD`
- Direct credentials
- Interactive prompts

See individual library READMEs for detailed usage instructions.