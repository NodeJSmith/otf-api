import { describe, it, expect, vi, beforeEach } from 'vitest';
import { generateHashDevice, DeviceSecretVerifierConfig } from '../../src/auth/device-utils';

// Mock the cognito-srp-helper module
vi.mock('cognito-srp-helper', () => ({
  createDeviceVerifier: vi.fn()
}));

// Import the mocked function after the mock is set up
import { createDeviceVerifier } from 'cognito-srp-helper';

describe('Device Utils', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('generateHashDevice', () => {
    it('should generate device hash successfully', () => {
      const mockDeviceVerifier = {
        DeviceRandomPassword: 'test-device-password',
        DeviceSecretVerifierConfig: {
          PasswordVerifier: 'test-password-verifier',
          Salt: 'test-salt'
        }
      };

      vi.mocked(createDeviceVerifier).mockReturnValue(mockDeviceVerifier);

      const result = generateHashDevice('test-device-group-key', 'test-device-key');

      expect(createDeviceVerifier).toHaveBeenCalledWith('test-device-key', 'test-device-group-key');
      expect(result).toEqual({
        devicePassword: 'test-device-password',
        deviceSecretVerifierConfig: {
          PasswordVerifier: 'test-password-verifier',
          Salt: 'test-salt'
        }
      });
    });

    it('should throw error when PasswordVerifier is missing', () => {
      const mockDeviceVerifier = {
        DeviceRandomPassword: 'test-device-password',
        DeviceSecretVerifierConfig: {
          PasswordVerifier: '',
          Salt: 'test-salt'
        }
      };

      vi.mocked(createDeviceVerifier).mockReturnValue(mockDeviceVerifier);

      expect(() => {
        generateHashDevice('test-device-group-key', 'test-device-key');
      }).toThrow('Failed to generate device verifier config');
    });

    it('should throw error when Salt is missing', () => {
      const mockDeviceVerifier = {
        DeviceRandomPassword: 'test-device-password',
        DeviceSecretVerifierConfig: {
          PasswordVerifier: 'test-password-verifier',
          Salt: ''
        }
      };

      vi.mocked(createDeviceVerifier).mockReturnValue(mockDeviceVerifier);

      expect(() => {
        generateHashDevice('test-device-group-key', 'test-device-key');
      }).toThrow('Failed to generate device verifier config');
    });

    it('should throw error when both PasswordVerifier and Salt are missing', () => {
      const mockDeviceVerifier = {
        DeviceRandomPassword: 'test-device-password',
        DeviceSecretVerifierConfig: {
          PasswordVerifier: '',
          Salt: ''
        }
      };

      vi.mocked(createDeviceVerifier).mockReturnValue(mockDeviceVerifier);

      expect(() => {
        generateHashDevice('test-device-group-key', 'test-device-key');
      }).toThrow('Failed to generate device verifier config');
    });

    it('should handle different device group keys and device keys', () => {
      const mockDeviceVerifier = {
        DeviceRandomPassword: 'different-device-password',
        DeviceSecretVerifierConfig: {
          PasswordVerifier: 'different-password-verifier',
          Salt: 'different-salt'
        }
      };

      vi.mocked(createDeviceVerifier).mockReturnValue(mockDeviceVerifier);

      const result = generateHashDevice('different-group-key', 'different-device-key');

      expect(createDeviceVerifier).toHaveBeenCalledWith('different-device-key', 'different-group-key');
      expect(result.devicePassword).toBe('different-device-password');
      expect(result.deviceSecretVerifierConfig.PasswordVerifier).toBe('different-password-verifier');
      expect(result.deviceSecretVerifierConfig.Salt).toBe('different-salt');
    });
  });

  describe('DeviceSecretVerifierConfig interface', () => {
    it('should have correct structure', () => {
      const config: DeviceSecretVerifierConfig = {
        PasswordVerifier: 'test-verifier',
        Salt: 'test-salt'
      };

      expect(config.PasswordVerifier).toBe('test-verifier');
      expect(config.Salt).toBe('test-salt');
    });
  });
});
