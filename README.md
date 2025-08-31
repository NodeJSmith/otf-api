Simple API client for interacting with the OrangeTheory Fitness APIs.

Review the [documentation](https://otf-api.readthedocs.io/en/stable/).


This library allows access to the OrangeTheory API to retrieve workouts and performance data, class schedules, studio information, and bookings.

## Installation
```bash
pip install otf-api
```

## Overview

To use the API, you need to create an instance of the `Otf` class. This will authenticate you with the API and allow you to make requests. When the `Otf` object is created it automatically grabs your member details and home studio, to simplify the process of making requests.

You can either pass an `OtfUser` object to the `OtfClass` or you can pass nothing and allow it to prompt you for your username and password.

You can also export environment variables `OTF_EMAIL` and `OTF_PASSWORD` to get these from the environment.

```python
from otf_api import Otf, OtfUser

otf = Otf()

# OR

otf = Otf(user=OtfUser(<email_address>,<password>))

```

## OpenAPI Schema

This library generates OpenAPI 3.0.3 schema files from its Pydantic models, providing a machine-readable representation of the API structure and data models. These schemas are automatically generated during the build process and are available as build artifacts.

### What's Generated

The OpenAPI schema includes:
- All public Pydantic models from the `otf_api.models` module
- Complete type definitions with field descriptions and constraints
- Nested model references and relationships
- Both YAML (`openapi.yaml`) and JSON (`openapi.json`) formats

### Why It's Generated

The OpenAPI schema serves as a contract for other language implementations and tools:
- **TypeScript Implementation**: Used by [mphuff/otf-api-ts](https://github.com/mphuff/otf-api-ts) to generate type-safe TypeScript clients
- **API Documentation**: Provides machine-readable API documentation
- **Code Generation**: Enables automatic code generation for other programming languages
- **Integration Tools**: Supports IDE integrations and API testing tools

### Generating the Schema

To generate the OpenAPI schema locally:

```bash
# Install dependencies
uv sync

# Generate schema
uv run python scripts/generate_openapi.py
```

The schema files will be created in the `schema/` directory:
- `schema/openapi.yaml` - YAML format (recommended for readability)
- `schema/openapi.json` - JSON format (recommended for tooling)

### Schema Structure

The generated schema follows OpenAPI 3.0.3 specification with:
- **Info**: API metadata and version information
- **Components/Schemas**: All Pydantic models as reusable schema definitions
- **Field Names**: Uses snake_case field names to match Python usage
- **Type References**: Properly resolved nested model references

The schema represents the complete structure of public API objects documented in the user documentation, making it easy to build compatible clients in other languages.
