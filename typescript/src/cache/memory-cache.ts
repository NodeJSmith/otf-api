import { Cache, CacheEntry, CacheConfig } from './types';

export class MemoryCache implements Cache {
  private store = new Map<string, CacheEntry>();
  private config: Required<CacheConfig>;
  private cleanupTimer?: NodeJS.Timeout;

  constructor(config: CacheConfig = {}) {
    this.config = {
      maxSize: config.maxSize ?? 1000,
      defaultTtl: config.defaultTtl ?? 3600,
      cleanupInterval: config.cleanupInterval ?? 300000, // 5 minutes
    };

    this.startCleanupTimer();
  }

  async get<T = any>(key: string): Promise<T | null> {
    const entry = this.store.get(key);
    
    if (!entry) {
      return null;
    }

    if (Date.now() > entry.expiresAt) {
      this.store.delete(key);
      return null;
    }

    return entry.value as T;
  }

  async set<T = any>(key: string, value: T, ttlSeconds?: number): Promise<void> {
    const ttl = ttlSeconds ?? this.config.defaultTtl;
    const now = Date.now();
    
    const entry: CacheEntry<T> = {
      value,
      expiresAt: now + (ttl * 1000),
      createdAt: now,
    };

    // Evict oldest entries if at capacity
    if (this.store.size >= this.config.maxSize) {
      this.evictOldest();
    }

    this.store.set(key, entry);
  }

  async delete(key: string): Promise<void> {
    this.store.delete(key);
  }

  async clear(): Promise<void> {
    this.store.clear();
  }

  async has(key: string): Promise<boolean> {
    const entry = this.store.get(key);
    if (!entry) return false;
    
    if (Date.now() > entry.expiresAt) {
      this.store.delete(key);
      return false;
    }
    
    return true;
  }

  private evictOldest(): void {
    let oldestKey: string | null = null;
    let oldestTime = Infinity;

    for (const [key, entry] of this.store.entries()) {
      if (entry.createdAt < oldestTime) {
        oldestTime = entry.createdAt;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.store.delete(oldestKey);
    }
  }

  private cleanup(): void {
    const now = Date.now();
    const keysToDelete: string[] = [];

    for (const [key, entry] of this.store.entries()) {
      if (now > entry.expiresAt) {
        keysToDelete.push(key);
      }
    }

    keysToDelete.forEach(key => this.store.delete(key));
  }

  private startCleanupTimer(): void {
    this.cleanupTimer = setInterval(() => {
      this.cleanup();
    }, this.config.cleanupInterval);

    // Clean up timer when process exits (Node.js only)
    if (typeof process !== 'undefined') {
      process.on('exit', () => {
        if (this.cleanupTimer) {
          clearInterval(this.cleanupTimer);
        }
      });
    }
  }
}