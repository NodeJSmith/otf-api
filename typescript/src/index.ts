export { Otf } from './otf';
export type { OtfUser } from './otf';
export type { OtfConfig } from './types/config';
export * from './errors';

// Export API classes for documentation
export { MembersApi } from './api/members';
export { WorkoutsApi } from './api/workouts';
export { BookingsApi } from './api/bookings';
export { StudiosApi } from './api/studios';

// Export types and interfaces
export type { StudioLocation, StudioService } from './api/studios';
export type { ZoneTimeMinutes, HeartRate, WorkoutWithTelemetry } from './api/workouts';

// Re-export types from local models
export type * from './models';