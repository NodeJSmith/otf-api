import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TokenAuth, PreExtractedTokens } from '../../src/auth/token-auth';
import { Cache } from '../../src/cache/types';

describe('TokenAuth', () => {
  let mockCache: Cache;
  let tokenAuth: TokenAuth;
  let tokens: PreExtractedTokens;

  beforeEach(() => {
    mockCache = {
      get: vi.fn(),
      set: vi.fn(),
      delete: vi.fn(),
      clear: vi.fn(),
      has: vi.fn(),
    };

    tokens = {
      accessToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjk5OTk5OTk5OTl9.test-signature',
      idToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjb2duaXRvOnVzZXJuYW1lIjoidGVzdC11dWlkIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIn0.test-signature',
      refreshToken: 'test-refresh-token',
      deviceKey: 'test-device-key',
      deviceGroupKey: 'test-device-group-key',
      devicePassword: 'test-device-password',
      memberUuid: 'test-member-uuid',
    };

    tokenAuth = new TokenAuth(tokens, mockCache);
  });

  describe('constructor', () => {
    it('should create TokenAuth instance with tokens and cache', () => {
      expect(tokenAuth).toBeInstanceOf(TokenAuth);
    });
  });

  describe('initialize', () => {
    it('should save tokens to cache', async () => {
      await tokenAuth.initialize();

      expect(mockCache.set).toHaveBeenCalledWith('tokens', {
        accessToken: tokens.accessToken,
        idToken: tokens.idToken,
        refreshToken: tokens.refreshToken,
      });

      expect(mockCache.set).toHaveBeenCalledWith('device', {
        deviceKey: tokens.deviceKey,
        deviceGroupKey: tokens.deviceGroupKey,
        devicePassword: tokens.devicePassword,
      });
    });

    it('should handle cache errors gracefully', async () => {
      mockCache.set.mockRejectedValue(new Error('Cache error'));

      await expect(tokenAuth.initialize()).rejects.toThrow('Cache error');
    });
  });

  describe('getAuthHeaders', () => {
    it('should return authorization headers with ID token', () => {
      const headers = tokenAuth.getAuthHeaders();

      expect(headers).toEqual({
        'Authorization': `Bearer ${tokens.idToken}`,
      });
    });

    it('should return different headers for different tokens', () => {
      const differentTokens: PreExtractedTokens = {
        ...tokens,
        idToken: 'different-id-token',
      };
      const differentTokenAuth = new TokenAuth(differentTokens, mockCache);

      const headers = differentTokenAuth.getAuthHeaders();

      expect(headers).toEqual({
        'Authorization': 'Bearer different-id-token',
      });
    });
  });

  describe('isTokenValid', () => {
    it('should return true for valid token', () => {
      // Token with expiration far in the future
      const validTokens: PreExtractedTokens = {
        ...tokens,
        accessToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjk5OTk5OTk5OTl9.test-signature',
      };
      const validTokenAuth = new TokenAuth(validTokens, mockCache);

      expect(validTokenAuth.isTokenValid()).toBe(true);
    });

    it('should return false for expired token', () => {
      // Token with expiration in the past
      const expiredTokens: PreExtractedTokens = {
        ...tokens,
        accessToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjF9.test-signature',
      };
      const expiredTokenAuth = new TokenAuth(expiredTokens, mockCache);

      expect(expiredTokenAuth.isTokenValid()).toBe(false);
    });

    it('should return false for invalid token format', () => {
      const invalidTokens: PreExtractedTokens = {
        ...tokens,
        accessToken: 'invalid-token-format',
      };
      const invalidTokenAuth = new TokenAuth(invalidTokens, mockCache);

      expect(invalidTokenAuth.isTokenValid()).toBe(false);
    });

    it('should return false for token expiring within 1 minute', () => {
      // Token expiring in 30 seconds (less than 1 minute buffer)
      const expiringSoon = Math.floor(Date.now() / 1000) + 30;
      const expiringTokens: PreExtractedTokens = {
        ...tokens,
        accessToken: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOi${expiringSoon}9.test-signature`,
      };
      const expiringTokenAuth = new TokenAuth(expiringTokens, mockCache);

      expect(expiringTokenAuth.isTokenValid()).toBe(false);
    });
  });

  describe('getMemberUuid', () => {
    it('should return member UUID from tokens', () => {
      expect(tokenAuth.getMemberUuid()).toBe('test-member-uuid');
    });

    it('should return different UUID for different tokens', () => {
      const differentTokens: PreExtractedTokens = {
        ...tokens,
        memberUuid: 'different-member-uuid',
      };
      const differentTokenAuth = new TokenAuth(differentTokens, mockCache);

      expect(differentTokenAuth.getMemberUuid()).toBe('different-member-uuid');
    });
  });

  describe('PreExtractedTokens interface', () => {
    it('should have correct structure', () => {
      const testTokens: PreExtractedTokens = {
        accessToken: 'test-access',
        idToken: 'test-id',
        refreshToken: 'test-refresh',
        deviceKey: 'test-device-key',
        deviceGroupKey: 'test-device-group-key',
        devicePassword: 'test-device-password',
        memberUuid: 'test-member-uuid',
      };

      expect(testTokens.accessToken).toBe('test-access');
      expect(testTokens.idToken).toBe('test-id');
      expect(testTokens.refreshToken).toBe('test-refresh');
      expect(testTokens.deviceKey).toBe('test-device-key');
      expect(testTokens.deviceGroupKey).toBe('test-device-group-key');
      expect(testTokens.devicePassword).toBe('test-device-password');
      expect(testTokens.memberUuid).toBe('test-member-uuid');
    });
  });
});
