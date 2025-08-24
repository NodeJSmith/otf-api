import { vi } from 'vitest';

// Mock environment variables for testing
process.env.OTF_EMAIL = 'test@example.com';
process.env.OTF_PASSWORD = 'testpassword';

// Mock console methods to reduce noise in test output
vi.spyOn(console, 'log').mockImplementation(() => {});
vi.spyOn(console, 'warn').mockImplementation(() => {});
vi.spyOn(console, 'error').mockImplementation(() => {});