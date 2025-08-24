import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'dist/',
        'docs/',
        'examples/',
        '**/*.test.ts',
        '**/*.spec.ts',
        'src/types/',
        'src/cache/types.ts',
        'src/errors.ts'
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    },
    setupFiles: ['./test/setup.ts'],
    include: ['test/**/*.test.ts', 'src/**/*.test.ts'],
    exclude: ['node_modules/', 'dist/', 'examples/']
  }
});