module.exports = {
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint'],
  extends: [
    'eslint:recommended'
  ],
  env: {
    node: true,
    es6: true,
  },
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
  },
  rules: {
    // Temporarily lenient rules during development
    '@typescript-eslint/no-unused-vars': 'off', // Allow unused vars during development
    '@typescript-eslint/no-explicit-any': 'off',
    'no-unused-vars': 'off', // Allow unused vars during development
    'no-constant-condition': 'off', // Allow constant conditions
    
    // Basic code quality rules (non-breaking)
    'no-console': 'off', // Allow console logs for this API library
    'prefer-const': 'warn', // Changed to warn instead of error
    'no-var': 'warn', // Changed to warn instead of error
    'no-undef': 'off', // TypeScript handles this
  },
  ignorePatterns: [
    'dist/',
    'node_modules/',
    'coverage/',
    '*.js', // Ignore JS files in the root
  ],
};