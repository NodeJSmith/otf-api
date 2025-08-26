import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { FileCache } from '../../src/cache/file-cache';
import * as fs from 'fs/promises';
import * as path from 'path';

// Mock fs/promises
vi.mock('fs/promises');
vi.mock('path');

describe('FileCache', () => {
  let fileCache: FileCache;
  let mockFs: any;
  let mockPath: any;

  beforeEach(() => {
    vi.clearAllMocks();
    
    mockFs = {
      readFile: vi.fn(),
      writeFile: vi.fn(),
      unlink: vi.fn(),
      readdir: vi.fn(),
      mkdir: vi.fn(),
    };

    mockPath = {
      resolve: vi.fn(),
      join: vi.fn(),
    };

    // Setup default mocks
    vi.mocked(fs.readFile).mockImplementation(mockFs.readFile);
    vi.mocked(fs.writeFile).mockImplementation(mockFs.writeFile);
    vi.mocked(fs.unlink).mockImplementation(mockFs.unlink);
    vi.mocked(fs.readdir).mockImplementation(mockFs.readdir);
    vi.mocked(fs.mkdir).mockImplementation(mockFs.mkdir);
    vi.mocked(path.resolve).mockImplementation(mockPath.resolve);
    vi.mocked(path.join).mockImplementation(mockPath.join);

    mockPath.resolve.mockReturnValue('/test/cache/dir');
    mockPath.join.mockImplementation((...args) => args.join('/'));

    fileCache = new FileCache('.test-cache');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('constructor', () => {
    it('should create FileCache with default cache directory', () => {
      const defaultCache = new FileCache();
      expect(defaultCache).toBeInstanceOf(FileCache);
    });

    it('should create FileCache with custom cache directory', () => {
      const customCache = new FileCache('/custom/cache/dir');
      expect(customCache).toBeInstanceOf(FileCache);
    });
  });

  describe('get', () => {
    it('should return cached value when file exists and not expired', async () => {
      const mockEntry = {
        value: { test: 'data' },
        expiresAt: Date.now() + 3600000, // 1 hour from now
        createdAt: Date.now(),
      };

      mockFs.readFile.mockResolvedValue(JSON.stringify(mockEntry));

      const result = await fileCache.get('test-key');

      expect(result).toEqual({ test: 'data' });
      expect(mockFs.readFile).toHaveBeenCalledWith('/test/cache/dir/test-key.json', 'utf-8');
    });

    it('should return null when file does not exist', async () => {
      mockFs.readFile.mockRejectedValue(new Error('File not found'));

      const result = await fileCache.get('nonexistent-key');

      expect(result).toBeNull();
    });

    it('should return null and delete file when entry is expired', async () => {
      const expiredEntry = {
        value: { test: 'data' },
        expiresAt: Date.now() - 1000, // 1 second ago
        createdAt: Date.now(),
      };

      mockFs.readFile.mockResolvedValue(JSON.stringify(expiredEntry));

      const result = await fileCache.get('expired-key');

      expect(result).toBeNull();
      expect(mockFs.unlink).toHaveBeenCalledWith('/test/cache/dir/expired-key.json');
    });

    it('should handle invalid JSON gracefully', async () => {
      mockFs.readFile.mockResolvedValue('invalid json');

      const result = await fileCache.get('invalid-key');

      expect(result).toBeNull();
    });
  });

  describe('set', () => {
    it('should save value to cache with default TTL', async () => {
      const testValue = { test: 'data' };
      const now = Date.now();

      await fileCache.set('test-key', testValue);

      expect(mockFs.mkdir).toHaveBeenCalledWith('/test/cache/dir', { recursive: true });
      expect(mockFs.writeFile).toHaveBeenCalledWith(
        '/test/cache/dir/test-key.json',
        expect.stringContaining('"test":"data"'),
        'utf-8'
      );

      const writeCall = mockFs.writeFile.mock.calls[0];
      const writtenData = JSON.parse(writeCall[1]);
      expect(writtenData.value).toEqual(testValue);
      expect(writtenData.expiresAt).toBeGreaterThan(now + 3599000); // Within 1 hour
      expect(writtenData.createdAt).toBeGreaterThanOrEqual(now);
    });

    it('should save value to cache with custom TTL', async () => {
      const testValue = { test: 'data' };
      const customTtl = 7200; // 2 hours

      await fileCache.set('test-key', testValue, customTtl);

      const writeCall = mockFs.writeFile.mock.calls[0];
      const writtenData = JSON.parse(writeCall[1]);
      expect(writtenData.expiresAt).toBeGreaterThan(Date.now() + (customTtl * 1000) - 1000);
    });

    it('should handle special characters in key names', async () => {
      await fileCache.set('test/key with spaces!@#', { data: 'value' });

      expect(mockFs.writeFile).toHaveBeenCalledWith(
        '/test/cache/dir/test_key_with_spaces___.json',
        expect.any(String),
        'utf-8'
      );
    });

    it('should handle mkdir errors gracefully', async () => {
      mockFs.mkdir.mockRejectedValue(new Error('Directory exists'));

      await expect(fileCache.set('test-key', { data: 'value' })).resolves.not.toThrow();
    });
  });

  describe('delete', () => {
    it('should delete existing file', async () => {
      await fileCache.delete('test-key');

      expect(mockFs.unlink).toHaveBeenCalledWith('/test/cache/dir/test-key.json');
    });

    it('should handle file not found gracefully', async () => {
      mockFs.unlink.mockRejectedValue(new Error('File not found'));

      await expect(fileCache.delete('nonexistent-key')).resolves.not.toThrow();
    });
  });

  describe('clear', () => {
    it('should delete all cache files', async () => {
      const mockFiles = ['file1.json', 'file2.json', 'file3.json'];
      mockFs.readdir.mockResolvedValue(mockFiles);

      await fileCache.clear();

      expect(mockFs.readdir).toHaveBeenCalledWith('/test/cache/dir');
      expect(mockFs.unlink).toHaveBeenCalledTimes(3);
      expect(mockFs.unlink).toHaveBeenCalledWith('/test/cache/dir/file1.json');
      expect(mockFs.unlink).toHaveBeenCalledWith('/test/cache/dir/file2.json');
      expect(mockFs.unlink).toHaveBeenCalledWith('/test/cache/dir/file3.json');
    });

    it('should handle directory not found gracefully', async () => {
      mockFs.readdir.mockRejectedValue(new Error('Directory not found'));

      await expect(fileCache.clear()).resolves.not.toThrow();
    });

    it('should handle empty directory', async () => {
      mockFs.readdir.mockResolvedValue([]);

      await fileCache.clear();

      expect(mockFs.readdir).toHaveBeenCalledWith('/test/cache/dir');
      expect(mockFs.unlink).not.toHaveBeenCalled();
    });
  });

  describe('has', () => {
    it('should return true when key exists and not expired', async () => {
      const mockEntry = {
        value: { test: 'data' },
        expiresAt: Date.now() + 3600000,
        createdAt: Date.now(),
      };

      mockFs.readFile.mockResolvedValue(JSON.stringify(mockEntry));

      const result = await fileCache.has('test-key');

      expect(result).toBe(true);
    });

    it('should return false when key does not exist', async () => {
      mockFs.readFile.mockRejectedValue(new Error('File not found'));

      const result = await fileCache.has('nonexistent-key');

      expect(result).toBe(false);
    });

    it('should return false when key is expired', async () => {
      const expiredEntry = {
        value: { test: 'data' },
        expiresAt: Date.now() - 1000,
        createdAt: Date.now(),
      };

      mockFs.readFile.mockResolvedValue(JSON.stringify(expiredEntry));

      const result = await fileCache.has('expired-key');

      expect(result).toBe(false);
    });
  });

  describe('private methods', () => {
    it('should ensure cache directory exists', async () => {
      await fileCache.set('test-key', { data: 'value' });

      expect(mockFs.mkdir).toHaveBeenCalledWith('/test/cache/dir', { recursive: true });
    });

    it('should generate safe file paths', async () => {
      await fileCache.set('test/key with spaces!@#', { data: 'value' });

      expect(mockFs.writeFile).toHaveBeenCalledWith(
        '/test/cache/dir/test_key_with_spaces___.json',
        expect.any(String),
        'utf-8'
      );
    });
  });
});
