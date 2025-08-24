export * from './generated/types';
import type { components } from './generated/types';

// Re-export commonly used types with better names
export type Member = components['schemas']['MemberDetail'];
export type Studio = components['schemas']['StudioDetail']; 
export type Class = components['schemas']['OtfClass'];
export type Booking = components['schemas']['BookingV2'];
export type Workout = components['schemas']['Workout'];
export type Coach = components['schemas']['Coach'];
export type MemberDetail = components['schemas']['MemberDetail'];
export type StudioDetail = components['schemas']['StudioDetail'];
export type OtfClass = components['schemas']['OtfClass'];
export type BookingV2 = components['schemas']['BookingV2'];

// Export schema version for compatibility checking
export const SCHEMA_VERSION = '1.0.0';