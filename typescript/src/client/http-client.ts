// TODO: Import correct signature utilities when implementing SigV4
import { OtfCognito, AwsCredentials } from '../auth/cognito';
import { 
  OtfRequestError, 
  RetryableOtfRequestError,
  AlreadyBookedError,
  BookingAlreadyCancelledError,
  OutsideSchedulingWindowError,
  ResourceNotFoundError 
} from '../errors';

export interface RequestOptions {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  baseUrl: string;
  path: string;
  params?: Record<string, any>;
  headers?: Record<string, string>;
  body?: any;
  requiresSigV4?: boolean;
}

export interface WorkoutRequestOptions {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  path: string;
  params?: Record<string, any>;
  headers?: Record<string, string>;
  body?: any;
  apiType?: 'default' | 'performance' | 'telemetry';
}

export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
}

export class OtfHttpClient {
  private cognito: OtfCognito;
  private retryConfig: RetryConfig;
  private timeout: number;

  // API Base URLs from Python implementation
  private static readonly API_BASE_URLS = {
    default: 'https://api.orangetheory.co',
    performance: 'https://api.orangetheory.io', 
    telemetry: 'https://api.yuzu.orangetheory.com',
  };

  constructor(
    cognito: OtfCognito,
    retryConfig: RetryConfig = { maxRetries: 3, baseDelay: 1000, maxDelay: 10000 },
    timeout = 20000
  ) {
    this.cognito = cognito;
    this.retryConfig = retryConfig;
    this.timeout = timeout;
  }

  async request<T = any>(options: RequestOptions): Promise<T> {
    return this.retryRequest(options, 0);
  }

  async workoutRequest<T = any>(options: WorkoutRequestOptions): Promise<T> {
    const baseUrl = this.getBaseUrlForApiType(options.apiType || 'default');
    const headers = this.getHeadersForApiType(options.apiType || 'default', options.headers);
    
    return this.request<T>({
      ...options,
      baseUrl,
      headers,
    });
  }

  getBaseUrlForApiType(apiType: 'default' | 'performance' | 'telemetry'): string {
    return OtfHttpClient.API_BASE_URLS[apiType];
  }

  private getHeadersForApiType(apiType: 'default' | 'performance' | 'telemetry', customHeaders?: Record<string, string>): Record<string, string> {
    const headers = { ...customHeaders };
    
    if (apiType === 'performance') {
      // Add koji headers for performance API (from Python implementation)
      headers['koji-member-id'] = this.cognito.getMemberUuid();
      headers['koji-member-email'] = this.cognito.getEmail();
    }
    
    return headers;
  }

  private async retryRequest<T>(options: RequestOptions, attempt: number): Promise<T> {
    try {
      return await this.executeRequest<T>(options);
    } catch (error) {
      if (attempt >= this.retryConfig.maxRetries || !this.isRetryableError(error)) {
        throw error;
      }

      const delay = Math.min(
        this.retryConfig.baseDelay * Math.pow(2, attempt),
        this.retryConfig.maxDelay
      );
      
      await this.sleep(delay);
      return this.retryRequest(options, attempt + 1);
    }
  }

  private async executeRequest<T>(options: RequestOptions): Promise<T> {
    const url = new URL(options.path, options.baseUrl);
    
    // Add query parameters
    if (options.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    // Build headers
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'User-Agent': 'otf-api-ts/1.0.0',
      ...options.headers,
    };

    // Add authentication
    const authHeaders = this.cognito.getAuthHeaders();
    Object.assign(headers, authHeaders);

    // Build request
    const requestInit: RequestInit = {
      method: options.method,
      headers,
      signal: AbortSignal.timeout(this.timeout),
    };

    if (options.body && options.method !== 'GET') {
      requestInit.body = JSON.stringify(options.body);
    }

    // Handle SigV4 signing if required
    if (options.requiresSigV4) {
      await this.signRequest(url, requestInit);
    }

    const response = await fetch(url.toString(), requestInit);
    
    if (!response.ok) {
      await this.handleHttpError(response, url);
    }

    return this.parseResponse<T>(response);
  }

  private async signRequest(url: URL, requestInit: RequestInit): Promise<void> {
    // TODO: Implement AWS SigV4 signing
    // This requires the @aws-sdk/signature-v4 package
    throw new Error('SigV4 signing not yet implemented');
  }

  private async parseResponse<T>(response: Response): Promise<T> {
    const text = await response.text();
    
    if (!text) {
      if (response.status === 200) {
        return null as T;
      }
      throw new OtfRequestError('Empty response from API');
    }

    try {
      const data = JSON.parse(text);
      
      // Check for logical errors in successful responses
      if (this.isErrorResponse(data)) {
        this.handleLogicalError(data);
      }
      
      return data;
    } catch (error) {
      throw new OtfRequestError('Invalid JSON response', error as Error);
    }
  }

  private async handleHttpError(response: Response, url: URL): Promise<void> {
    let errorData: any = {};
    
    try {
      const text = await response.text();
      if (text) {
        errorData = JSON.parse(text);
      }
    } catch {
      // Ignore JSON parse errors for error responses
    }

    const path = url.pathname;
    const code = errorData.code;
    const errorCode = errorData.data?.errorCode;
    const message = errorData.message || errorData.data?.message || response.statusText;

    // Map specific error patterns from Python implementation
    if (response.status === 404) {
      throw new ResourceNotFoundError(`Resource not found: ${path}`);
    }

    // Booking-specific errors
    if (path.match(/^\/v1\/bookings\/me/)) {
      if (code === 'BOOKING_CANCELED') {
        throw new BookingAlreadyCancelledError(message);
      }
      if (code === 'BOOKING_ALREADY_BOOKED') {
        throw new AlreadyBookedError();
      }
    }

    // Legacy booking errors
    if (path.match(/^\/member\/members\/.*?\/bookings/)) {
      if (code === 'NOT_AUTHORIZED' && message?.startsWith('This class booking has been cancelled')) {
        throw new ResourceNotFoundError('Booking was already cancelled');
      }
      if (errorCode === '603') {
        throw new AlreadyBookedError();
      }
      if (errorCode === '602') {
        throw new OutsideSchedulingWindowError();
      }
    }

    // Determine if error is retryable
    const ErrorClass = response.status >= 500 ? RetryableOtfRequestError : OtfRequestError;
    throw new ErrorClass(`HTTP ${response.status}: ${message}`, undefined, undefined, response);
  }

  private handleLogicalError(data: any): void {
    const status = data.Status || data.status;
    
    if (typeof status === 'number' && (status < 200 || status >= 300)) {
      throw new OtfRequestError(`API error: ${JSON.stringify(data)}`);
    }
  }

  private isErrorResponse(data: any): boolean {
    // Check for common error response patterns
    return (
      (data.Status && (data.Status < 200 || data.Status >= 300)) ||
      (data.status && (data.status < 200 || data.status >= 300)) ||
      (data.error !== undefined) ||
      (data.code && data.message)
    );
  }

  private isRetryableError(error: any): boolean {
    return (
      error instanceof RetryableOtfRequestError ||
      (error instanceof OtfRequestError && error.response?.status && error.response.status >= 500) ||
      error.name === 'AbortError' ||
      error.name === 'TimeoutError'
    );
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}