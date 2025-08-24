import { Cache } from '../cache/types';

export interface PreExtractedTokens {
  accessToken: string;
  idToken: string;
  refreshToken: string;
  deviceKey: string;
  deviceGroupKey: string;
  devicePassword: string;
  memberUuid: string;
}

export class TokenAuth {
  private tokens: PreExtractedTokens;
  private cache: Cache;

  constructor(tokens: PreExtractedTokens, cache: Cache) {
    this.tokens = tokens;
    this.cache = cache;
  }

  async initialize(): Promise<void> {
    // Save tokens to cache for future use
    await this.cache.set('tokens', {
      accessToken: this.tokens.accessToken,
      idToken: this.tokens.idToken,
      refreshToken: this.tokens.refreshToken,
    });

    await this.cache.set('device', {
      deviceKey: this.tokens.deviceKey,
      deviceGroupKey: this.tokens.deviceGroupKey,
      devicePassword: this.tokens.devicePassword,
    });
  }

  getAuthHeaders(): Record<string, string> {
    return {
      'Authorization': `Bearer ${this.tokens.idToken}`,
    };
  }

  isTokenValid(): boolean {
    try {
      const payload = JSON.parse(atob(this.tokens.accessToken.split('.')[1]));
      const exp = payload.exp * 1000; // Convert to milliseconds
      return Date.now() < exp - 60000; // 1 minute buffer
    } catch {
      return false;
    }
  }

  getMemberUuid(): string {
    return this.tokens.memberUuid;
  }
}