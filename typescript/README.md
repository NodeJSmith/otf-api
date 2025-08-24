# OTF API - TypeScript Library

[![npm version](https://badge.fury.io/js/otf-api-ts.svg)](https://badge.fury.io/js/otf-api-ts)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![Node.js 18+](https://img.shields.io/badge/node-18.0+-green.svg)](https://nodejs.org/)

A TypeScript/JavaScript API client for OrangeTheory Fitness APIs. This library provides type-safe access to OTF APIs for retrieving workouts, performance data, class schedules, studio information, and bookings.

**⚠️ Important**: This software is not affiliated with, endorsed by, or supported by Orangetheory Fitness. It may break if OrangeTheory changes their services.

## Features

- **Full Type Safety**: Generated TypeScript types from Python models
- **Comprehensive API Coverage**: Access workouts, bookings, member details, studio information
- **Authentication**: AWS Cognito integration with automatic token management
- **Multiple Cache Options**: Memory, localStorage, and file system caching
- **Browser & Node.js**: Works in both environments
- **Clean Architecture**: Consistent with Python library design

## Installation

### Using npm

```bash
npm install otf-api-ts
```

### Using yarn

```bash
yarn add otf-api-ts
```

### Using pnpm

```bash
pnpm add otf-api-ts
```

## Quick Start

### Basic Usage (Node.js)

```typescript
import { Otf } from 'otf-api-ts';

// Initialize with credentials
const otf = new Otf({
  email: 'your-email@example.com',
  password: 'your-password'
});

// Get member details
const member = await otf.members.getMemberDetail();
console.log(`Hello, ${member.first_name}!`);

// Get recent workouts
const workouts = await otf.workouts.getWorkouts({
  startDate: new Date('2024-01-01'),
  endDate: new Date('2024-01-31')
});
```

### Basic Usage (Browser)

```typescript
import { Otf, LocalStorageCache } from 'otf-api-ts';

const otf = new Otf({
  email: 'your-email@example.com',
  password: 'your-password',
  cache: new LocalStorageCache() // Use browser localStorage
});

// Same API as Node.js version
const member = await otf.members.getMemberDetail();
```

### Environment Variables (Node.js)

```typescript
// Set in your environment
// OTF_EMAIL=your-email@example.com
// OTF_PASSWORD=your-password

import { Otf } from 'otf-api-ts';

// Automatically uses process.env.OTF_EMAIL and process.env.OTF_PASSWORD
const otf = new Otf();
```

### Advanced Configuration

```typescript
import { Otf, FileCacheOptions, MemoryCache } from 'otf-api-ts';

const otf = new Otf({
  email: 'your-email@example.com',
  password: 'your-password',
  
  // Cache options
  cache: new MemoryCache({ maxSize: 1000 }),
  
  // Request timeout
  timeout: 30000,
  
  // Custom user agent
  userAgent: 'MyApp/1.0.0',
  
  // Debug mode
  debug: true
});
```

## API Overview

The library is organized into 4 main API domains:

### Bookings API

```typescript
// Get upcoming bookings
const bookings = await otf.bookings.getBookingsNew(
  new Date('2024-01-01'),
  new Date('2024-01-31')
);

// Get single booking
const booking = await otf.bookings.getBookingNew('booking-id');

// Book a class (if booking endpoints are available)
// const booking = await otf.bookings.bookClass('class-uuid');
```

### Members API

```typescript
// Get member profile
const member = await otf.members.getMemberDetail();
console.log(`Member: ${member.first_name} ${member.last_name}`);
console.log(`Home Studio: ${member.home_studio.name}`);

// Access nested data with full type safety
if (member.profile) {
  console.log(`Max HR: ${member.profile.formula_max_hr}`);
}
```

### Studios API

```typescript
// Get studio details
const studio = await otf.studios.getStudioDetail('studio-uuid');
console.log(`Studio: ${studio.name}`);
console.log(`Location: ${studio.location.address}`);

// Get studio services
const services = await otf.studios.getStudioServices('studio-uuid');
```

### Workouts API

```typescript
// Get performance summary
const performance = await otf.workouts.getPerformanceSummary('summary-id');
console.log(`Calories: ${performance.calories_burned}`);
console.log(`Splat Points: ${performance.splat_points}`);

// Get telemetry data
const telemetry = await otf.workouts.getTelemetry('summary-id', {
  maxDataPoints: 1000
});

// Get challenge tracker
const challenges = await otf.workouts.getChallengeTracker();
```

## Type Safety

All API responses are fully typed based on the Python Pydantic models:

```typescript
import type { MemberDetail, BookingV2, Workout } from 'otf-api-ts';

// Full IntelliSense support
const member: MemberDetail = await otf.members.getMemberDetail();
const homeStudio = member.home_studio; // Type: StudioDetail
const studioName = homeStudio.name;    // Type: string
const location = homeStudio.location;   // Type: StudioLocation

// Nullable fields are properly typed
const weight = member.weight;           // Type: number | null
```

## Authentication

### AWS Cognito Integration

```typescript
// Manual authentication
const auth = await otf.authenticate();
console.log(`Authenticated as: ${auth.email}`);

// Access tokens directly (for advanced usage)
const tokens = otf.getTokens();
if (tokens) {
  console.log(`Access Token: ${tokens.accessToken}`);
  console.log(`ID Token: ${tokens.idToken}`);
}

// Check authentication status
if (await otf.isAuthenticated()) {
  console.log('Ready to make API calls');
}
```

### Token Caching

```typescript
import { Otf, FileCacheOptions } from 'otf-api-ts';

// Tokens are automatically cached and reused
const otf = new Otf({
  email: 'your-email@example.com',
  password: 'your-password',
  cache: new FileCacheOptions({
    cacheDir: './cache',
    ttl: 3600000 // 1 hour in milliseconds
  })
});
```

## Caching Options

### Memory Cache (Default)
```typescript
import { MemoryCache } from 'otf-api-ts';

const otf = new Otf({
  cache: new MemoryCache({
    maxSize: 1000,      // Maximum number of items
    ttl: 300000        // 5 minutes TTL
  })
});
```

### Local Storage Cache (Browser)
```typescript
import { LocalStorageCache } from 'otf-api-ts';

const otf = new Otf({
  cache: new LocalStorageCache({
    keyPrefix: 'otf-api-',
    ttl: 300000
  })
});
```

### File System Cache (Node.js)
```typescript
import { FileCache } from 'otf-api-ts';

const otf = new Otf({
  cache: new FileCache({
    cacheDir: './cache',
    ttl: 300000
  })
});
```

## Development Setup

### Prerequisites

- Node.js 18 or higher
- npm, yarn, or pnpm

### Setting Up Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/NodeJSmith/otf-api.git
   cd otf-api/typescript
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Generate types from schema**
   ```bash
   npm run generate-types
   ```

4. **Run tests**
   ```bash
   npm test
   ```

5. **Build the library**
   ```bash
   npm run build
   ```

### Development Commands

#### Building
```bash
# Build TypeScript to JavaScript
npm run build

# Build in watch mode
npm run build:watch

# Clean build artifacts
npm run clean
```

#### Testing
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run specific test file
npm test -- members.test.ts

# Run with coverage
npm run test:coverage
```

#### Code Quality
```bash
# Lint with ESLint
npm run lint

# Fix linting issues
npm run lint:fix

# Type check
npm run type-check
```

#### Type Generation
```bash
# Generate TypeScript types from OpenAPI schema
npm run generate-types

# Validate generated types
npm run test:types
```

## Project Structure

```
typescript/
├── src/
│   ├── api/              # API client modules
│   │   ├── bookings.ts   # Booking operations
│   │   ├── members.ts    # Member operations
│   │   ├── studios.ts    # Studio operations
│   │   └── workouts.ts   # Workout operations
│   ├── auth/             # Authentication
│   │   ├── cognito.ts    # AWS Cognito client
│   │   └── token-auth.ts # Token management
│   ├── cache/            # Caching implementations
│   │   ├── memory-cache.ts
│   │   ├── local-storage-cache.ts
│   │   └── file-cache.ts
│   ├── client/           # HTTP client
│   ├── generated/        # Auto-generated types
│   │   └── types.ts      # Generated from Python models
│   ├── types/            # Custom TypeScript types
│   └── index.ts          # Main export
├── test/                 # Test suite
├── examples/             # Usage examples
└── package.json          # Package configuration
```

## Architecture

### Design Philosophy
The TypeScript library mirrors the Python library's architecture:
- Same clean field names (source of truth from Python models)
- Consistent API structure and method names
- Type-safe interfaces generated from Python Pydantic models

### Data Transformation
```
OrangeTheory API → TypeScript Client → Transform → Clean Python Field Names → Consumer
```

The library handles the messy OrangeTheory API field mapping internally:
```typescript
// Internal transformation (you don't see this)
{
  memberUUId: "123",      // OrangeTheory API
  firstName: "John"       // OrangeTheory API
}
↓
{
  member_uuid: "123",     // Clean Python field name
  first_name: "John"      // Clean Python field name
}
```

## Error Handling

```typescript
import { OtfError, AuthenticationError, RateLimitError } from 'otf-api-ts';

try {
  const member = await otf.members.getMemberDetail();
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Authentication failed:', error.message);
  } else if (error instanceof RateLimitError) {
    console.error('Rate limited:', error.retryAfter);
  } else if (error instanceof OtfError) {
    console.error('API error:', error.message);
  } else {
    console.error('Unexpected error:', error);
  }
}
```

## Examples

### Basic Workout Analytics
```typescript
const workouts = await otf.workouts.getWorkouts({
  startDate: new Date('2024-01-01'),
  endDate: new Date('2024-12-31')
});

const totalCalories = workouts.reduce((sum, w) => sum + (w.calories_burned || 0), 0);
const avgSplatPoints = workouts.reduce((sum, w) => sum + (w.splat_points || 0), 0) / workouts.length;

console.log(`Total Calories: ${totalCalories}`);
console.log(`Average Splat Points: ${avgSplatPoints.toFixed(1)}`);
```

### Studio Finder
```typescript
const studios = await otf.studios.getStudios();
const nearbyStudios = studios
  .filter(s => s.distance < 10) // Within 10 miles
  .sort((a, b) => a.distance - b.distance);

console.log('Nearby Studios:');
nearbyStudios.forEach(studio => {
  console.log(`${studio.name} - ${studio.distance} miles`);
});
```

## Contributing

### Code Standards
- Use TypeScript for all code
- Follow ESLint configuration
- Include comprehensive JSDoc comments
- Maintain 100% type coverage

### Adding New Features
1. Update the corresponding API class
2. Add proper TypeScript types
3. Include comprehensive tests
4. Update documentation
5. Ensure examples work

### Type Generation
The types are auto-generated from the Python Pydantic models. To add new types:

1. Add the model to Python library
2. Regenerate schema: `cd ../python && uv run python ../scripts/generate_openapi.py`
3. Regenerate types: `npm run generate-types`

## Troubleshooting

### Authentication Issues
```typescript
// Enable debug mode
const otf = new Otf({
  email: 'your-email',
  password: 'your-password',
  debug: true
});

// Check authentication
if (!(await otf.isAuthenticated())) {
  console.error('Authentication failed');
}
```

### CORS Issues (Browser)
```typescript
// Use a CORS proxy for development
const otf = new Otf({
  email: 'your-email',
  password: 'your-password',
  baseUrl: 'https://cors-anywhere.herokuapp.com/https://api.orangetheory.co'
});
```

### Rate Limiting
```typescript
// Add delays between requests
for (const workoutId of workoutIds) {
  const workout = await otf.workouts.getWorkout(workoutId);
  await new Promise(resolve => setTimeout(resolve, 500)); // 500ms delay
}
```

## API Reference

For complete API documentation, see:
- **Type Definitions**: `src/generated/types.ts`
- **Examples**: `examples/` directory
- **Tests**: `test/` directory for usage examples

## License

MIT License - see LICENSE file for details.

## Disclaimer

This project is not affiliated with, endorsed by, or supported by Orangetheory Fitness. Use at your own risk.