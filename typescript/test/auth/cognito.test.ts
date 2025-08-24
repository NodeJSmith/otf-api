import { describe, it, expect, vi, beforeEach } from 'vitest';
import { OtfCognito, CognitoConfig } from '../../src/auth/cognito';
import { MemoryCache } from '../../src/cache/memory-cache';

// Mock the cognito-srp-helper module
vi.mock('cognito-srp-helper', () => ({
  createSrpSession: vi.fn().mockReturnValue({
    step1: vi.fn().mockResolvedValue({
      ChallengeName: 'PASSWORD_VERIFIER',
      ChallengeParameters: {
        SRP_B: 'test-srp-b',
        SALT: 'test-salt',
        SECRET_BLOCK: 'test-secret-block'
      }
    }),
    step2: vi.fn().mockResolvedValue({
      AuthenticationResult: {
        AccessToken: 'test-access-token',
        IdToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjb2duaXRvOnVzZXJuYW1lIjoidGVzdC11dWlkIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIn0.test-signature',
        RefreshToken: 'test-refresh-token'
      }
    })
  }),
  createSecretHash: vi.fn().mockReturnValue('test-secret-hash'),
  createDeviceVerifier: vi.fn().mockReturnValue({
    DeviceRandomPassword: 'test-device-password',
    DeviceSecretVerifierConfig: {
      PasswordVerifier: 'test-verifier',
      Salt: 'test-salt'
    }
  })
}));

describe('OtfCognito', () => {
  let cognito: OtfCognito;
  let mockCache: MemoryCache;
  
  const testConfig: CognitoConfig = {
    userPoolId: 'us-east-1_test',
    clientId: 'test-client-id',
    identityPoolId: 'us-east-1:test-identity-pool',
    region: 'us-east-1'
  };

  beforeEach(() => {
    mockCache = new MemoryCache();
    cognito = new OtfCognito('test@example.com', 'password', mockCache, testConfig);
  });

  describe('constructor', () => {
    it('should create cognito instance with email and password', () => {
      expect(cognito).toBeDefined();
    });

    it('should create cognito instance without password for token-based auth', () => {
      const tokenCognito = new OtfCognito('test@example.com', null, mockCache, testConfig);
      expect(tokenCognito).toBeDefined();
    });
  });

  describe('authenticate', () => {
    it('should authenticate with password when available', async () => {
      await expect(cognito.authenticate()).resolves.not.toThrow();
    });

    it('should authenticate with cached tokens when password not provided', async () => {
      const tokenCognito = new OtfCognito('test@example.com', null, mockCache, testConfig);
      
      // Mock cached tokens
      await mockCache.set('cognito_access_token', 'cached-access-token');
      await mockCache.set('cognito_id_token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjb2duaXRvOnVzZXJuYW1lIjoidGVzdC11dWlkIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIn0.test-signature');
      await mockCache.set('cognito_refresh_token', 'cached-refresh-token');
      
      await expect(tokenCognito.authenticate()).resolves.not.toThrow();
    });
  });

  describe('getMemberUuid', () => {
    it('should extract member UUID from ID token', async () => {
      await cognito.authenticate();
      const memberUuid = cognito.getMemberUuid();
      expect(memberUuid).toBe('test-uuid');
    });
  });

  describe('getEmail', () => {
    it('should extract email from ID token', async () => {
      await cognito.authenticate();
      const email = cognito.getEmail();
      expect(email).toBe('test@example.com');
    });
  });
});