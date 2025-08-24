import { createDeviceVerifier } from 'cognito-srp-helper';

export interface DeviceSecretVerifierConfig {
  PasswordVerifier: string;
  Salt: string;
}

export function generateHashDevice(
  deviceGroupKey: string,
  deviceKey: string
): {
  devicePassword: string;
  deviceSecretVerifierConfig: DeviceSecretVerifierConfig;
} {
  const deviceVerifier = createDeviceVerifier(deviceKey, deviceGroupKey);
  
  if (!deviceVerifier.DeviceSecretVerifierConfig.PasswordVerifier || 
      !deviceVerifier.DeviceSecretVerifierConfig.Salt) {
    throw new Error('Failed to generate device verifier config');
  }
  
  return {
    devicePassword: deviceVerifier.DeviceRandomPassword,
    deviceSecretVerifierConfig: {
      PasswordVerifier: deviceVerifier.DeviceSecretVerifierConfig.PasswordVerifier,
      Salt: deviceVerifier.DeviceSecretVerifierConfig.Salt,
    },
  };
}