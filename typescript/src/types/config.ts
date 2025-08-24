export interface OtfConfig {
  email?: string;
  password?: string;
  logLevel?: 'debug' | 'info' | 'warn' | 'error';
  logRawResponses?: boolean;
  cacheDir?: string;
  timeout?: number;
  maxRetries?: number;
}

export interface ApiEndpoints {
  main: string;
  io: string; 
  telemetry: string;
}

export const DEFAULT_CONFIG: Required<OtfConfig> = {
  email: '',
  password: '',
  logLevel: 'info',
  logRawResponses: false,
  cacheDir: '.otf-cache',
  timeout: 20000,
  maxRetries: 3,
};

export const API_ENDPOINTS: ApiEndpoints = {
  main: 'https://api.orangetheory.co',
  io: 'https://api.orangetheory.io',
  telemetry: 'https://api.yuzu.orangetheory.com',
};