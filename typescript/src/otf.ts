import { Member } from 'otf-api-models';
import { OtfHttpClient } from './client/http-client';
import { OtfCognito, CognitoConfig } from './auth/cognito';
import { MembersApi } from './api/members';
import { WorkoutsApi } from './api/workouts';
import { BookingsApi } from './api/bookings';
import { StudiosApi } from './api/studios';
import { MemoryCache } from './cache/memory-cache';
import { LocalStorageCache } from './cache/local-storage-cache';
import { FileCache } from './cache/file-cache';
import { Cache } from './cache/types';
import { OtfConfig, DEFAULT_CONFIG } from './types/config';
import { NoCredentialsError } from './errors';

const COGNITO_CONFIG: CognitoConfig = {
  userPoolId: 'us-east-1_dYDxUeyL1',
  clientId: '1457d19r0pcjgmp5agooi0rb1b',
  identityPoolId: 'us-east-1:4943c880-fb02-4fd7-bc37-2f4c32ecb2a3',
  region: 'us-east-1',
};

/**
 * User credentials for OTF authentication
 */
export interface OtfUser {
  /** User's email address for OTF account */
  email: string;
  /** User's password (optional if using cached tokens) */
  password?: string;
}

/**
 * Main OrangeTheory Fitness API client
 * 
 * This is the primary entry point for all OTF API operations including member data,
 * workout statistics, class bookings, and studio information.
 * 
 * @example
 * ```typescript
 * import { Otf } from 'otf-api-ts';
 * 
 * const otf = new Otf({ email: 'user@example.com', password: 'password' });
 * await otf.initialize();
 * 
 * const member = await otf.member;
 * const workouts = await otf.workouts.getWorkouts();
 * ```
 */
export class Otf {
  /** API for member profile and membership operations */
  public members: MembersApi;
  /** API for workout data, stats, and challenge tracking */
  public workouts: WorkoutsApi;
  /** API for class booking and cancellation operations */
  public bookings: BookingsApi;
  /** API for studio information and services */
  public studios: StudiosApi;

  private client: OtfHttpClient;
  private cognito: OtfCognito;
  private cache: Cache;
  private _member: Member | null = null;

  /**
   * Creates a new OTF API client instance
   * 
   * @param user - User credentials (email required, password optional if using cached tokens)
   * @param config - Optional configuration overrides
   * @throws {NoCredentialsError} When email is not provided via user, config, or environment
   */
  constructor(user?: OtfUser, config: Partial<OtfConfig> = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };
    
    // Get credentials from user, environment, or config
    const email = user?.email || finalConfig.email || process.env.OTF_EMAIL;
    const password = user?.password || finalConfig.password || process.env.OTF_PASSWORD;
    
    if (!email) {
      throw new NoCredentialsError('Email is required for authentication');
    }

    // Initialize cache based on environment
    this.cache = this.createCache(finalConfig);
    
    // Initialize authentication
    this.cognito = new OtfCognito(email, password || null, this.cache, COGNITO_CONFIG);
    
    // Initialize HTTP client
    this.client = new OtfHttpClient(this.cognito, {
      maxRetries: finalConfig.maxRetries,
      baseDelay: 1000,
      maxDelay: 10000,
    }, finalConfig.timeout);

    // Initialize API modules (will be re-initialized after auth)
    this.members = new MembersApi(this.client, '');
    this.workouts = new WorkoutsApi(this.client, '');
    this.bookings = new BookingsApi(this.client, '');
    this.studios = new StudiosApi(this.client, '');
  }

  /**
   * Initializes authentication and sets up API modules
   * 
   * Must be called before using any API methods
   * 
   * @throws {AuthenticationError} When authentication fails
   */
  async initialize(): Promise<void> {
    await this.cognito.authenticate();
    
    // Re-initialize API modules with member UUID after authentication
    const memberUuid = this.cognito.getMemberUuid();
    this.members = new MembersApi(this.client, memberUuid);
    this.workouts = new WorkoutsApi(this.client, memberUuid);
    this.bookings = new BookingsApi(this.client, memberUuid);
    this.studios = new StudiosApi(this.client, memberUuid);
    
    // Set cross-references for complex operations
    this.workouts.setOtfInstance(this);
    this.studios.setOtfInstance(this);
  }

  /**
   * Gets the authenticated member's profile data
   * 
   * @returns Promise resolving to member profile with home studio and membership details
   */
  get member(): Promise<Member> {
    return this.getMember();
  }

  /**
   * Gets the authenticated member's profile data
   * 
   * @returns Promise resolving to member profile with home studio and membership details
   */
  async getMember(): Promise<Member> {
    if (!this._member) {
      this._member = await this.members.getMemberDetail();
    }
    return this._member;
  }

  /**
   * Refreshes the cached member profile data
   * 
   * @returns Promise resolving to updated member profile
   */
  async refreshMember(): Promise<Member> {
    this._member = await this.members.getMemberDetail();
    return this._member;
  }

  /**
   * Gets the authenticated member's UUID
   * 
   * @returns Promise resolving to member UUID string
   */
  get memberUuid(): Promise<string> {
    return this.getMember().then(member => member.member_uuid);
  }

  /**
   * Gets the member's home studio information
   * 
   * @returns Promise resolving to home studio details
   */
  get homeStudio(): Promise<any> {
    return this.getMember().then(member => member.home_studio);
  }

  /**
   * Gets the member's home studio UUID
   * 
   * @returns Promise resolving to home studio UUID string
   */
  get homeStudioUuid(): Promise<string> {
    return this.homeStudio.then(studio => studio.studio_uuid);
  }

  private createCache(config: OtfConfig): Cache {
    // Browser environment
    if (typeof window !== 'undefined') {
      try {
        return new LocalStorageCache('otf-api-');
      } catch {
        return new MemoryCache();
      }
    }
    
    // Node.js environment
    if (typeof process !== 'undefined') {
      return new FileCache(config.cacheDir);
    }
    
    // Fallback to memory cache
    return new MemoryCache();
  }
}