import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { LocalStorageCache } from '../../src/cache/local-storage-cache';

describe('LocalStorageCache', () => {
  let localStorageCache: LocalStorageCache;
  let mockLocalStorage: {
    getItem: ReturnType<typeof vi.fn>;
    setItem: ReturnType<typeof vi.fn>;
    removeItem: ReturnType<typeof vi.fn>;
    clear: ReturnType<typeof vi.fn>;
    key: ReturnType<typeof vi.fn>;
    length: number;
  };

  beforeEach(() => {
    // Mock localStorage
    mockLocalStorage = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
      key: vi.fn(),
      length: 0,
    };

    // Mock window object
    Object.defineProperty(global, 'window', {
      value: {
        localStorage: mockLocalStorage,
      },
      writable: true,
      configurable: true,
    });

    // Also mock global localStorage for direct access
    Object.defineProperty(global, 'localStorage', {
      value: mockLocalStorage,
      writable: true,
      configurable: true,
    });

    localStorageCache = new LocalStorageCache('test-prefix-');
  });

  afterEach(() => {
    vi.clearAllMocks();
    // Reset window and localStorage to undefined
    Object.defineProperty(global, 'window', {
      value: undefined,
      writable: true,
      configurable: true,
    });
    Object.defineProperty(global, 'localStorage', {
      value: undefined,
      writable: true,
      configurable: true,
    });
  });

  describe('constructor', () => {
    it('should create LocalStorageCache with default prefix', () => {
      // Re-setup window for this test
      Object.defineProperty(global, 'window', {
        value: { localStorage: mockLocalStorage },
        writable: true,
        configurable: true,
      });
      Object.defineProperty(global, 'localStorage', {
        value: mockLocalStorage,
        writable: true,
        configurable: true,
      });
      
      const defaultCache = new LocalStorageCache();
      expect(defaultCache).toBeInstanceOf(LocalStorageCache);
    });

    it('should create LocalStorageCache with custom prefix', () => {
      // Re-setup window for this test
      Object.defineProperty(global, 'window', {
        value: { localStorage: mockLocalStorage },
        writable: true,
        configurable: true,
      });
      Object.defineProperty(global, 'localStorage', {
        value: mockLocalStorage,
        writable: true,
        configurable: true,
      });
      
      const customCache = new LocalStorageCache('custom-prefix-');
      expect(customCache).toBeInstanceOf(LocalStorageCache);
    });

    it('should throw error when localStorage is not available', () => {
      Object.defineProperty(global, 'window', {
        value: undefined,
        writable: true,
        configurable: true,
      });
      Object.defineProperty(global, 'localStorage', {
        value: undefined,
        writable: true,
        configurable: true,
      });

      expect(() => {
        new LocalStorageCache();
      }).toThrow('LocalStorage not available');
    });

    it('should throw error when window is not available', () => {
      Object.defineProperty(global, 'window', {
        value: undefined,
        writable: true,
        configurable: true,
      });
      Object.defineProperty(global, 'localStorage', {
        value: undefined,
        writable: true,
        configurable: true,
      });

      expect(() => {
        new LocalStorageCache();
      }).toThrow('LocalStorage not available');
    });
  });

  describe('get', () => {
    it('should return cached value when item exists and not expired', async () => {
      const mockEntry = {
        value: { test: 'data' },
        expiresAt: Date.now() + 3600000, // 1 hour from now
        createdAt: Date.now(),
      };

      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(mockEntry));

      const result = await localStorageCache.get('test-key');

      expect(result).toEqual({ test: 'data' });
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('test-prefix-test-key');
    });

    it('should return null when item does not exist', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);

      const result = await localStorageCache.get('nonexistent-key');

      expect(result).toBeNull();
    });

    it('should return null and delete item when entry is expired', async () => {
      const expiredEntry = {
        value: { test: 'data' },
        expiresAt: Date.now() - 1000, // 1 second ago
        createdAt: Date.now(),
      };

      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(expiredEntry));

      const result = await localStorageCache.get('expired-key');

      expect(result).toBeNull();
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('test-prefix-expired-key');
    });

    it('should handle invalid JSON gracefully', async () => {
      mockLocalStorage.getItem.mockReturnValue('invalid json');

      const result = await localStorageCache.get('invalid-key');

      expect(result).toBeNull();
    });

    it('should handle JSON parse errors gracefully', async () => {
      mockLocalStorage.getItem.mockReturnValue('{"invalid": json}');

      const result = await localStorageCache.get('invalid-key');

      expect(result).toBeNull();
    });
  });

  describe('set', () => {
    it('should save value to localStorage with default TTL', async () => {
      const testValue = { test: 'data' };
      const now = Date.now();

      await localStorageCache.set('test-key', testValue);

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'test-prefix-test-key',
        expect.stringContaining('"test":"data"')
      );

      const setCall = mockLocalStorage.setItem.mock.calls[0];
      const writtenData = JSON.parse(setCall[1]);
      expect(writtenData.value).toEqual(testValue);
      expect(writtenData.expiresAt).toBeGreaterThan(now + 3599000); // Within 1 hour
      expect(writtenData.createdAt).toBeGreaterThanOrEqual(now);
    });

    it('should save value to localStorage with custom TTL', async () => {
      const testValue = { test: 'data' };
      const customTtl = 7200; // 2 hours

      await localStorageCache.set('test-key', testValue, customTtl);

      const setCall = mockLocalStorage.setItem.mock.calls[0];
      const writtenData = JSON.parse(setCall[1]);
      expect(writtenData.expiresAt).toBeGreaterThan(Date.now() + (customTtl * 1000) - 1000);
    });

    it('should handle quota exceeded error by clearing cache and retrying', async () => {
      const testValue = { test: 'data' };
      const quotaError = new Error('QuotaExceededError');
      
      // First call fails with quota error, second succeeds
      mockLocalStorage.setItem
        .mockImplementationOnce(() => { throw quotaError; })
        .mockImplementationOnce(() => undefined);

      // Mock clear method to return keys
      mockLocalStorage.length = 3;
      mockLocalStorage.key
        .mockReturnValueOnce('test-prefix-key1')
        .mockReturnValueOnce('test-prefix-key2')
        .mockReturnValueOnce('other-key')
        .mockReturnValueOnce(null);

      await localStorageCache.set('test-key', testValue);

      // The first call fails, then clear is called, then the second call succeeds
      expect(mockLocalStorage.setItem).toHaveBeenCalledTimes(2);
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('test-prefix-key1');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('test-prefix-key2');
      expect(mockLocalStorage.removeItem).not.toHaveBeenCalledWith('other-key');
    });

    it('should handle other setItem errors', async () => {
      const testValue = { test: 'data' };
      const otherError = new Error('Other error');
      
      // Both calls fail with the same error
      mockLocalStorage.setItem
        .mockImplementationOnce(() => { throw otherError; })
        .mockImplementationOnce(() => { throw otherError; });

      // The error should be thrown after clearing cache fails
      await expect(localStorageCache.set('test-key', testValue)).rejects.toThrow('Other error');
    });
  });

  describe('delete', () => {
    it('should remove item from localStorage', async () => {
      await localStorageCache.delete('test-key');

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('test-prefix-test-key');
    });
  });

  describe('clear', () => {
    it('should remove all items with matching prefix', async () => {
      // Mock localStorage to have some items
      mockLocalStorage.length = 4;
      mockLocalStorage.key
        .mockReturnValueOnce('test-prefix-key1')
        .mockReturnValueOnce('other-prefix-key2')
        .mockReturnValueOnce('test-prefix-key3')
        .mockReturnValueOnce('test-prefix-key4')
        .mockReturnValueOnce(null);

      await localStorageCache.clear();

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('test-prefix-key1');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('test-prefix-key3');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('test-prefix-key4');
      expect(mockLocalStorage.removeItem).not.toHaveBeenCalledWith('other-prefix-key2');
    });

    it('should handle empty localStorage', async () => {
      mockLocalStorage.length = 0;

      await localStorageCache.clear();

      expect(mockLocalStorage.removeItem).not.toHaveBeenCalled();
    });

    it('should handle localStorage with no matching keys', async () => {
      mockLocalStorage.length = 2;
      mockLocalStorage.key
        .mockReturnValueOnce('other-prefix-key1')
        .mockReturnValueOnce('different-prefix-key2')
        .mockReturnValueOnce(null);

      await localStorageCache.clear();

      expect(mockLocalStorage.removeItem).not.toHaveBeenCalled();
    });
  });

  describe('has', () => {
    it('should return true when key exists and not expired', async () => {
      const mockEntry = {
        value: { test: 'data' },
        expiresAt: Date.now() + 3600000,
        createdAt: Date.now(),
      };

      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(mockEntry));

      const result = await localStorageCache.has('test-key');

      expect(result).toBe(true);
    });

    it('should return false when key does not exist', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);

      const result = await localStorageCache.has('nonexistent-key');

      expect(result).toBe(false);
    });

    it('should return false when key is expired', async () => {
      const expiredEntry = {
        value: { test: 'data' },
        expiresAt: Date.now() - 1000,
        createdAt: Date.now(),
      };

      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(expiredEntry));

      const result = await localStorageCache.has('expired-key');

      expect(result).toBe(false);
    });
  });

  describe('private methods', () => {
    it('should generate correct keys with prefix', () => {
      // Test the private getKey method indirectly through public methods
      localStorageCache.delete('test-key');

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('test-prefix-test-key');
    });

    it('should handle different prefixes correctly', () => {
      // Re-setup window for this test
      Object.defineProperty(global, 'window', {
        value: { localStorage: mockLocalStorage },
        writable: true,
        configurable: true,
      });
      Object.defineProperty(global, 'localStorage', {
        value: mockLocalStorage,
        writable: true,
        configurable: true,
      });
      
      const customCache = new LocalStorageCache('custom-');
      customCache.delete('test-key');

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('custom-test-key');
    });
  });

  describe('error handling', () => {
    it('should handle localStorage.getItem throwing an error', async () => {
      mockLocalStorage.getItem.mockImplementation(() => {
        throw new Error('Storage error');
      });

      const result = await localStorageCache.get('test-key');

      expect(result).toBeNull();
    });

    it('should handle localStorage.setItem throwing an error during clear', async () => {
      const testValue = { test: 'data' };
      const quotaError = new Error('QuotaExceededError');
      
      mockLocalStorage.setItem
        .mockImplementationOnce(() => { throw quotaError; })
        .mockImplementationOnce(() => { throw quotaError; });
      mockLocalStorage.length = 1;
      mockLocalStorage.key.mockReturnValue('test-prefix-key1');
      mockLocalStorage.removeItem.mockImplementation(() => {
        throw new Error('Remove error');
      });

      // The error should be thrown after clearing cache fails
      await expect(localStorageCache.set('test-key', testValue)).rejects.toThrow('QuotaExceededError');
    });
  });
});
