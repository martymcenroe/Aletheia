import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // Use jsdom for DOM simulation
    environment: 'jsdom',

    // Setup files to run before tests
    setupFiles: ['./tests/setup.js'],

    // Include only unit tests (exclude e2e)
    include: ['tests/unit/**/*.test.js'],

    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json'],
      include: ['extensions/**/*.js'],
      exclude: [
        'extensions/**/node_modules/**',
        'extensions/**/*.test.js'
      ],
      // Thresholds per ADR 0215
      thresholds: {
        statements: 70,
        branches: 60,
        functions: 70,
        lines: 70
      }
    },

    // Global test settings
    globals: true,

    // Reporter for CI
    reporters: ['verbose']
  }
});
