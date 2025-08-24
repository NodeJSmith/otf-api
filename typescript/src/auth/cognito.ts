import {
  CognitoIdentityProviderClient,
  InitiateAuthCommand,
  InitiateAuthCommandOutput,
  RespondToAuthChallengeCommand,
  ConfirmDeviceCommand,
} from '@aws-sdk/client-cognito-identity-provider';
import {
  CognitoIdentityClient, 
  GetIdCommand,
  GetCredentialsForIdentityCommand,
} from '@aws-sdk/client-cognito-identity';
import { 
  createSecretHash, 
  createSrpSession, 
  signSrpSession, 
  wrapInitiateAuth, 
  wrapAuthChallenge,
  createDeviceVerifier
} from 'cognito-srp-helper';
import { generateHashDevice } from './device-utils';
import { Cache } from '../cache/types';

export interface CognitoConfig {
  userPoolId: string;
  clientId: string;
  clientSecret?: string;
  identityPoolId: string;
  region: string;
}

export interface TokenSet {
  accessToken: string;
  idToken: string;
  refreshToken: string;
}

export interface DeviceMetadata {
  deviceKey: string;
  deviceGroupKey: string;
  devicePassword: string;
}

export interface AwsCredentials {
  accessKeyId: string;
  secretAccessKey: string;
  sessionToken: string;
}

export class OtfCognito {
  private config: CognitoConfig;
  private idpClient: CognitoIdentityProviderClient;
  private idClient: CognitoIdentityClient;
  private cache: Cache;
  
  private tokens: TokenSet | null = null;
  private deviceMetadata: DeviceMetadata | null = null;
  private username: string;
  
  constructor(
    username: string,
    password: string | null,
    cache: Cache,
    config: CognitoConfig
  ) {
    this.config = config;
    this.username = username;
    this.cache = cache;
    
    this.idpClient = new CognitoIdentityProviderClient({
      region: config.region,
    });
    
    this.idClient = new CognitoIdentityClient({
      region: config.region,
    });
  }

  async authenticate(): Promise<void> {
    // Try cached tokens first
    await this.loadFromCache();
    
    if (this.tokens && this.isTokenValid()) {
      return;
    }
    
    // If no valid tokens, try password authentication
    const password = process.env.OTF_PASSWORD;
    if (password) {
      await this.authenticateWithPassword(password);
      return;
    }
    
    throw new Error('Authentication required - no valid cached tokens and no password provided');
  }

  async authenticateWithPassword(password: string): Promise<void> {
    const secretHash = this.config.clientSecret 
      ? createSecretHash(this.username, this.config.clientId, this.config.clientSecret)
      : undefined;
    
    const srpSession = createSrpSession(this.username, password, this.config.userPoolId, false);

    // Step 1: InitiateAuth with SRP_A
    const initiateAuthCommand = new InitiateAuthCommand(
      wrapInitiateAuth(srpSession, {
        ClientId: this.config.clientId,
        AuthFlow: 'USER_SRP_AUTH',
        AuthParameters: {
          CHALLENGE_NAME: 'SRP_A',
          USERNAME: this.username,
          ...(secretHash && { SECRET_HASH: secretHash }),
        },
      })
    );

    const initiateAuthResponse = await this.idpClient.send(initiateAuthCommand);
    
    if (initiateAuthResponse.ChallengeName !== 'PASSWORD_VERIFIER') {
      throw new Error(`Expected PASSWORD_VERIFIER challenge, got: ${initiateAuthResponse.ChallengeName}`);
    }

    // Step 2: Respond to PASSWORD_VERIFIER challenge
    const signedSrpSession = signSrpSession(srpSession, initiateAuthResponse);
    
    const respondToChallengeCommand = new RespondToAuthChallengeCommand(
      wrapAuthChallenge(signedSrpSession, {
        ClientId: this.config.clientId,
        ChallengeName: 'PASSWORD_VERIFIER',
        ChallengeResponses: {
          USERNAME: this.username,
          ...(secretHash && { SECRET_HASH: secretHash }),
        },
      })
    );

    const authResponse = await this.idpClient.send(respondToChallengeCommand);
    await this.handleAuthResponse(authResponse);
  }

  async refreshTokens(): Promise<void> {
    if (!this.tokens?.refreshToken || !this.deviceMetadata?.deviceKey) {
      throw new Error('Cannot refresh - missing refresh token or device key');
    }

    const command = new InitiateAuthCommand({
      ClientId: this.config.clientId,
      AuthFlow: 'REFRESH_TOKEN_AUTH',
      AuthParameters: {
        REFRESH_TOKEN: this.tokens.refreshToken,
        DEVICE_KEY: this.deviceMetadata.deviceKey,
      },
    });

    const response = await this.idpClient.send(command);
    await this.handleAuthResponse(response);
  }

  async getAwsCredentials(): Promise<AwsCredentials> {
    if (!this.tokens?.idToken) {
      throw new Error('ID token required for AWS credentials');
    }

    const providerKey = `cognito-idp.${this.config.region}.amazonaws.com/${this.config.userPoolId}`;
    
    const getIdCommand = new GetIdCommand({
      IdentityPoolId: this.config.identityPoolId,
      Logins: {
        [providerKey]: this.tokens.idToken,
      },
    });

    const identity = await this.idClient.send(getIdCommand);
    
    const getCredsCommand = new GetCredentialsForIdentityCommand({
      IdentityId: identity.IdentityId!,
      Logins: {
        [providerKey]: this.tokens.idToken,
      },
    });

    const creds = await this.idClient.send(getCredsCommand);
    
    return {
      accessKeyId: creds.Credentials!.AccessKeyId!,
      secretAccessKey: creds.Credentials!.SecretKey!,
      sessionToken: creds.Credentials!.SessionToken!,
    };
  }

  getAuthHeaders(): Record<string, string> {
    if (!this.tokens?.idToken) {
      throw new Error('Not authenticated - no ID token available');
    }
    
    return {
      'Authorization': `Bearer ${this.tokens.idToken}`,
    };
  }

  getMemberUuid(): string {
    if (!this.tokens?.idToken) {
      throw new Error('Not authenticated - no ID token available');
    }
    
    try {
      const payload = JSON.parse(atob(this.tokens.idToken.split('.')[1]));
      return payload['cognito:username'];
    } catch (error) {
      throw new Error('Failed to extract member UUID from ID token');
    }
  }

  getEmail(): string {
    if (!this.tokens?.idToken) {
      throw new Error('Not authenticated - no ID token available');
    }
    
    try {
      const payload = JSON.parse(atob(this.tokens.idToken.split('.')[1]));
      return payload['email'];
    } catch (error) {
      throw new Error('Failed to extract email from ID token');
    }
  }

  private async loadFromCache(): Promise<void> {
    const cachedTokens = await this.cache.get('tokens');
    const cachedDevice = await this.cache.get('device');
    
    if (cachedTokens) {
      this.tokens = cachedTokens as TokenSet;
    }
    
    if (cachedDevice) {
      this.deviceMetadata = cachedDevice as DeviceMetadata;
    }
  }

  private async saveToCache(): Promise<void> {
    if (this.tokens) {
      const ttl = this.getTokenExpirationSeconds();
      await this.cache.set('tokens', this.tokens, ttl);
    }
    
    if (this.deviceMetadata) {
      await this.cache.set('device', this.deviceMetadata);
    }
  }

  private async handleAuthResponse(response: InitiateAuthCommandOutput): Promise<void> {
    const authResult = response.AuthenticationResult;
    if (!authResult?.AccessToken || !authResult.IdToken) {
      throw new Error('Invalid authentication response');
    }

    this.tokens = {
      accessToken: authResult.AccessToken,
      idToken: authResult.IdToken,
      refreshToken: authResult.RefreshToken || this.tokens?.refreshToken || '',
    };

    // Handle device metadata - set from response or keep existing cached values
    if (authResult.NewDeviceMetadata) {
      this.deviceMetadata = {
        deviceKey: authResult.NewDeviceMetadata.DeviceKey || '',
        deviceGroupKey: authResult.NewDeviceMetadata.DeviceGroupKey || '',
        devicePassword: '',
      };
      
      // Generate device password for future use but don't confirm device yet
      // Based on Python implementation, device confirmation may not be required
      if (this.deviceMetadata.deviceKey && this.deviceMetadata.deviceGroupKey) {
        try {
          const { devicePassword } = generateHashDevice(
            this.deviceMetadata.deviceGroupKey,
            this.deviceMetadata.deviceKey
          );
          this.deviceMetadata.devicePassword = devicePassword;
        } catch (error) {
          console.warn('Failed to generate device password:', error);
        }
      }
    }

    await this.saveToCache();
  }

  private async confirmDevice(): Promise<void> {
    if (!this.deviceMetadata || !this.tokens?.accessToken) {
      return;
    }

    const { devicePassword, deviceSecretVerifierConfig } = generateHashDevice(
      this.deviceMetadata.deviceGroupKey,
      this.deviceMetadata.deviceKey
    );

    this.deviceMetadata.devicePassword = devicePassword;

    const command = new ConfirmDeviceCommand({
      AccessToken: this.tokens.accessToken,
      DeviceKey: this.deviceMetadata.deviceKey,
      DeviceSecretVerifierConfig: deviceSecretVerifierConfig,
      DeviceName: this.getDeviceName(),
    });

    await this.idpClient.send(command);
    await this.saveToCache();
  }

  private isTokenValid(): boolean {
    if (!this.tokens?.accessToken) return false;
    
    try {
      const payload = JSON.parse(atob(this.tokens.accessToken.split('.')[1]));
      const exp = payload.exp * 1000; // Convert to milliseconds
      return Date.now() < exp - 60000; // 1 minute buffer
    } catch {
      return false;
    }
  }

  private getTokenExpirationSeconds(): number {
    if (!this.tokens?.accessToken) return 3600; // Default 1 hour
    
    try {
      const payload = JSON.parse(atob(this.tokens.accessToken.split('.')[1]));
      return payload.exp - Math.floor(Date.now() / 1000);
    } catch {
      return 3600;
    }
  }

  private getDeviceName(): string {
    if (typeof window !== 'undefined') {
      return `browser-${navigator.userAgent.slice(0, 50)}`;
    }
    return `node-${process.platform}-${process.arch}`;
  }
}