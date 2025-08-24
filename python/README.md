# OTF API - Python Library

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/otf-api.svg)](https://badge.fury.io/py/otf-api)
[![Documentation Status](https://readthedocs.org/projects/otf-api/badge/?version=stable)](https://otf-api.readthedocs.io/en/stable/)

An unofficial Python API client for OrangeTheory Fitness APIs. This library provides access to OTF APIs for retrieving workouts, performance data, class schedules, studio information, and bookings.

**⚠️ Important**: This software is not affiliated with, endorsed by, or supported by Orangetheory Fitness. It may break if OrangeTheory changes their services.

## Features

- **Comprehensive API Coverage**: Access workouts, bookings, member details, studio information
- **Clean Data Models**: Well-structured Pydantic models with proper typing
- **Authentication**: AWS Cognito integration with automatic token management
- **Caching**: Disk-based caching to reduce API calls
- **Rate Limiting**: Built-in request throttling
- **Type Safety**: Full type hints throughout the codebase

## Installation

### Using pip

```bash
pip install otf-api
```

### Using uv (recommended for development)

```bash
uv add otf-api
```

## Quick Start

### Basic Usage

```python
from otf_api import Otf

# Initialize with credentials
otf = Otf(email="your-email@example.com", password="your-password")

# Get member details
member = await otf.get_member_detail()
print(f"Hello, {member.first_name}!")

# Get recent workouts
workouts = await otf.get_workouts_by_date_range(
    start_date="2024-01-01",
    end_date="2024-01-31"
)
```

### Environment Variables

You can set credentials via environment variables:

```bash
export OTF_EMAIL="your-email@example.com"
export OTF_PASSWORD="your-password"
export OTF_LOG_LEVEL="INFO"  # Optional: DEBUG, INFO, WARNING, ERROR
```

Then initialize without parameters:

```python
from otf_api import Otf

otf = Otf()  # Automatically uses environment variables
```

### Advanced Authentication

```python
from otf_api import Otf, OtfUser

# Using OtfUser object
user = OtfUser(email="your-email@example.com", password="your-password")
otf = Otf(user=user)

# Using cached tokens (if available)
otf = Otf()  # Will use cached tokens if valid
```

## API Overview

The library is organized into 4 main API domains:

### Bookings API
```python
# Get upcoming bookings
bookings = await otf.get_bookings_by_date_range(
    start_date="2024-01-01",
    end_date="2024-01-31"
)

# Book a class
booking = await otf.book_class(class_uuid="class-123")

# Cancel a booking
await otf.cancel_booking(booking_id="booking-456")
```

### Members API
```python
# Get member profile
member = await otf.get_member_detail()

# Get membership information
membership = await otf.get_member_membership()

# Get purchase history
purchases = await otf.get_member_purchases()
```

### Studios API
```python
# Find studios near location
studios = await otf.get_studios_by_geo(
    latitude=40.7128,
    longitude=-74.0060,
    radius=10
)

# Get studio details
studio = await otf.get_studio_detail(studio_uuid="studio-123")
```

### Workouts API
```python
# Get workout history
workouts = await otf.get_workouts_by_date_range(
    start_date="2024-01-01",
    end_date="2024-01-31"
)

# Get performance summary
performance = await otf.get_performance_summary(summary_id="summary-123")

# Get challenge tracker data
challenges = await otf.get_challenge_tracker()
```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Setting Up Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/NodeJSmith/otf-api.git
   cd otf-api/python
   ```

2. **Install dependencies with uv**
   ```bash
   uv sync
   ```

3. **Install pre-commit hooks**
   ```bash
   uv run pre-commit install
   ```

4. **Verify installation**
   ```bash
   uv run pytest
   ```

### Development Commands

#### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/otf_api --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_filters.py

# Run single test
uv run pytest tests/test_filters.py::test_class_filter_string_to_date
```

#### Code Quality
```bash
# Lint and format with ruff
uv run ruff check --fix
uv run ruff format

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

#### Package Management
```bash
# Add a new dependency
uv add requests

# Add a development dependency
uv add --dev pytest

# Update dependencies
uv sync --upgrade
```

#### Schema Generation
```bash
# Generate OpenAPI schema from Python models
uv run python ../scripts/generate_openapi.py

# Validate schema generation
uv run pytest tests/test_schema_generation.py -v
```

## Project Structure

```
python/
├── src/otf_api/           # Main package source
│   ├── api/               # API client modules
│   │   ├── bookings/      # Booking operations
│   │   ├── members/       # Member operations
│   │   ├── studios/       # Studio operations
│   │   └── workouts/      # Workout operations
│   ├── auth/              # Authentication (AWS Cognito)
│   ├── models/            # Pydantic data models
│   │   ├── bookings/      # Booking-related models
│   │   ├── members/       # Member-related models
│   │   ├── studios/       # Studio-related models
│   │   └── workouts/      # Workout-related models
│   └── cache.py           # Caching utilities
├── tests/                 # Test suite
├── examples/              # Usage examples
└── pyproject.toml         # Package configuration
```

## Architecture

### Client Pattern
Each API domain follows this pattern:
- `*Api` class: High-level interface with business logic
- `*Client` class: Low-level HTTP client for raw API requests
- Models: Pydantic classes for request/response serialization

### Data Flow
```
OrangeTheory API → Client → API → Models (with validation_alias) → Clean Python Fields
```

### Key Dependencies
- **pydantic**: Data validation and serialization
- **httpx**: HTTP client for API requests
- **pycognito**: AWS Cognito authentication
- **diskcache**: Disk-based caching
- **pendulum**: Date/time handling

## Contributing

### Code Standards
- **Line length**: 120 characters
- **Docstring style**: Google format
- **Type hints**: Required for all public APIs
- **Import sorting**: Handled by ruff

### Testing Requirements
- All new features must have tests
- Maintain or improve test coverage
- Tests must pass in CI

### Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the full test suite
5. Submit a pull request

### Development Guidelines

#### Adding New API Endpoints
1. Add the endpoint to the appropriate `*Client` class
2. Add business logic to the corresponding `*Api` class
3. Create or update Pydantic models as needed
4. Add comprehensive tests
5. Update documentation

#### Model Design
- Use clean Python field names (snake_case)
- Map OrangeTheory API fields via `validation_alias`
- Include proper type hints and documentation
- Extend from `OtfItemBase` for consistency

## Troubleshooting

### Authentication Issues
```python
# Check if credentials are correct
try:
    otf = Otf(email="your-email", password="your-password")
    member = await otf.get_member_detail()
except Exception as e:
    print(f"Authentication failed: {e}")
```

### Rate Limiting
The library includes built-in rate limiting, but you may need to add delays for intensive usage:

```python
import asyncio

# Add delays between requests
for workout in workout_list:
    data = await otf.get_workout_detail(workout.id)
    await asyncio.sleep(0.5)  # 500ms delay
```

### Debugging
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or set via environment
# export OTF_LOG_LEVEL=DEBUG
```

## Documentation

- **Full API Documentation**: https://otf-api.readthedocs.io/en/stable/
- **Examples**: See `examples/` directory
- **Type Information**: The package includes `py.typed` for full type support

## License

MIT License - see LICENSE file for details.

## Disclaimer

This project is not affiliated with, endorsed by, or supported by Orangetheory Fitness. Use at your own risk.