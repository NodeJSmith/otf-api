import { Cache, CacheEntry } from './types';

export class LocalStorageCache implements Cache {
  private prefix: string;

  constructor(prefix = 'otf-api-') {
    this.prefix = prefix;
    
    if (typeof window === 'undefined' || !window.localStorage) {
      throw new Error('LocalStorage not available');
    }
  }

  async get<T = any>(key: string): Promise<T | null> {
    try {
      const item = localStorage.getItem(this.getKey(key));
      if (!item) return null;

      const entry: CacheEntry<T> = JSON.parse(item);
      
      if (Date.now() > entry.expiresAt) {
        await this.delete(key);
        return null;
      }

      return entry.value;
    } catch {
      return null;
    }
  }

  async set<T = any>(key: string, value: T, ttlSeconds = 3600): Promise<void> {
    const entry: CacheEntry<T> = {
      value,
      expiresAt: Date.now() + (ttlSeconds * 1000),
      createdAt: Date.now(),
    };

    try {
      localStorage.setItem(this.getKey(key), JSON.stringify(entry));
    } catch (error) {
      // Handle quota exceeded errors
      console.warn('LocalStorage quota exceeded, clearing cache', error);
      await this.clear();
      localStorage.setItem(this.getKey(key), JSON.stringify(entry));
    }
  }

  async delete(key: string): Promise<void> {
    localStorage.removeItem(this.getKey(key));
  }

  async clear(): Promise<void> {
    const keys: string[] = [];
    
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith(this.prefix)) {
        keys.push(key);
      }
    }

    keys.forEach(key => localStorage.removeItem(key));
  }

  async has(key: string): Promise<boolean> {
    return (await this.get(key)) !== null;
  }

  private getKey(key: string): string {
    return `${this.prefix}${key}`;
  }
}