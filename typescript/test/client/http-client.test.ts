import { describe, it, expect, vi, beforeEach } from 'vitest';
import { OtfHttpClient } from '../../src/client/http-client';
import { OtfCognito } from '../../src/auth/cognito';

// Mock the HTTP client dependencies
vi.mock('../../src/auth/cognito');

describe('OtfHttpClient', () => {
  let client: OtfHttpClient;
  let mockCognito: vi.Mocked<OtfCognito>;

  beforeEach(() => {
    mockCognito = {
      getAccessToken: vi.fn().mockResolvedValue('test-access-token'),
      authenticate: vi.fn().mockResolvedValue(undefined),
    } as any;

    client = new OtfHttpClient(mockCognito, {
      maxRetries: 3,
      baseDelay: 100,
      maxDelay: 1000,
    }, 5000);
  });

  describe('constructor', () => {
    it('should create client with default retry config', () => {
      const defaultClient = new OtfHttpClient(mockCognito);
      expect(defaultClient).toBeDefined();
    });

    it('should create client with custom config', () => {
      expect(client).toBeDefined();
    });
  });

  describe('getBaseUrlForApiType', () => {
    it('should return correct base URL for default API', () => {
      const baseUrl = client.getBaseUrlForApiType('default');
      expect(baseUrl).toBe('https://api.orangetheory.co');
    });

    it('should return correct base URL for performance API', () => {
      const baseUrl = client.getBaseUrlForApiType('performance');
      expect(baseUrl).toBe('https://api.orangetheory.io');
    });

    it('should return correct base URL for telemetry API', () => {
      const baseUrl = client.getBaseUrlForApiType('telemetry');
      expect(baseUrl).toBe('https://api.yuzu.orangetheory.com');
    });
  });

  describe('request options validation', () => {
    it('should require method and path', () => {
      expect(() => {
        client.request({} as any);
      }).toThrow();
    });

    it('should accept valid request options', async () => {
      // Mock fetch to avoid actual HTTP calls
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: vi.fn().mockResolvedValue({ data: 'test' })
      } as any);

      const result = await client.request({
        method: 'GET',
        baseUrl: 'https://api.orangetheory.co',
        path: '/test'
      });

      expect(result).toBeDefined();
    });
  });
});