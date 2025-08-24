export interface Cache {
  get<T = any>(key: string): Promise<T | null>;
  set<T = any>(key: string, value: T, ttlSeconds?: number): Promise<void>;
  delete(key: string): Promise<void>;
  clear(): Promise<void>;
  has(key: string): Promise<boolean>;
}

export interface CacheEntry<T = any> {
  value: T;
  expiresAt: number;
  createdAt: number;
}

export interface CacheConfig {
  maxSize?: number;
  defaultTtl?: number;
  cleanupInterval?: number;
}