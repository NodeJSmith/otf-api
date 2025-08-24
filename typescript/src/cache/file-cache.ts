import * as fs from 'fs/promises';
import * as path from 'path';
import { Cache, CacheEntry } from './types';

export class FileCache implements Cache {
  private cacheDir: string;

  constructor(cacheDir = '.otf-cache') {
    this.cacheDir = path.resolve(cacheDir);
  }

  async get<T = any>(key: string): Promise<T | null> {
    try {
      const filePath = this.getFilePath(key);
      const content = await fs.readFile(filePath, 'utf-8');
      const entry: CacheEntry<T> = JSON.parse(content);
      
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
    await this.ensureCacheDir();
    
    const entry: CacheEntry<T> = {
      value,
      expiresAt: Date.now() + (ttlSeconds * 1000),
      createdAt: Date.now(),
    };

    const filePath = this.getFilePath(key);
    await fs.writeFile(filePath, JSON.stringify(entry), 'utf-8');
  }

  async delete(key: string): Promise<void> {
    try {
      const filePath = this.getFilePath(key);
      await fs.unlink(filePath);
    } catch {
      // Ignore errors if file doesn't exist
    }
  }

  async clear(): Promise<void> {
    try {
      const files = await fs.readdir(this.cacheDir);
      await Promise.all(
        files.map(file => fs.unlink(path.join(this.cacheDir, file)))
      );
    } catch {
      // Ignore errors if directory doesn't exist
    }
  }

  async has(key: string): Promise<boolean> {
    return (await this.get(key)) !== null;
  }

  private async ensureCacheDir(): Promise<void> {
    try {
      await fs.mkdir(this.cacheDir, { recursive: true });
    } catch {
      // Ignore if directory already exists
    }
  }

  private getFilePath(key: string): string {
    const safeKey = key.replace(/[^a-zA-Z0-9-_]/g, '_');
    return path.join(this.cacheDir, `${safeKey}.json`);
  }
}