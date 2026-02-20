// ESLint Flat Config for Aletheia browser extensions
// Migrated from .eslintrc.json per Issue #157 / LLD 1157
// Security plugins added per ADR 0213 - Adversarial Audit Philosophy

import js from "@eslint/js";
import globals from "globals";
import noUnsanitized from "eslint-plugin-no-unsanitized";
import security from "eslint-plugin-security";

export default [
  // Base recommended rules
  js.configs.recommended,

  // Browser extension configuration
  {
    files: ["extensions/**/*.js"],
    plugins: {
      "no-unsanitized": noUnsanitized,
      "security": security
    },
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.webextensions,
        // Explicit definitions ensure Chrome/Firefox APIs are available
        // even if globals.webextensions changes in future versions
        chrome: "readonly",
        browser: "readonly"
      }
    },
    rules: {
      // Migrated from .eslintrc.json
      "no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_"
        }
      ],
      "no-console": "off",
      "prefer-const": "error",

      // Security: Detect unsafe innerHTML/outerHTML/document.write usage
      "no-unsanitized/method": "error",
      "no-unsanitized/property": "error",

      // Security plugin rules (subset most relevant to browser extensions)
      "security/detect-object-injection": "warn",
      "security/detect-non-literal-regexp": "warn",
      "security/detect-unsafe-regex": "error",
      "security/detect-eval-with-expression": "error"
    }
  },

  // Chrome-specific overrides (if needed in future)
  {
    files: ["extensions/chrome/**/*.js"],
    // Chrome MV3 specific rules can be added here
  },

  // Firefox-specific overrides (if needed in future)
  {
    files: ["extensions/firefox/**/*.js"],
    // Firefox MV2 specific rules can be added here
  },

  // Test file configuration (Vitest + jsdom)
  {
    files: ["tests/**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        ...globals.node,
        ...globals.browser,
        // Vitest globals
        describe: "readonly",
        it: "readonly",
        expect: "readonly",
        beforeEach: "readonly",
        afterEach: "readonly",
        beforeAll: "readonly",
        afterAll: "readonly",
        vi: "readonly",
        // Node/Browser shared globals
        setTimeout: "readonly",
        clearTimeout: "readonly",
        setInterval: "readonly",
        clearInterval: "readonly",
        console: "readonly",
        window: "readonly",
        document: "readonly",
        globalThis: "readonly"
      }
    },
    rules: {
      // Relaxed rules for tests
      "no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_|^env$",
          caughtErrorsIgnorePattern: "^_"
        }
      ]
    }
  },

  // Static admin dashboard (browser JS, no extensions API)
  {
    files: ["static/**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "script",
      globals: {
        ...globals.browser,
        Chart: "readonly"
      }
    },
    rules: {
      "no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_"
        }
      ]
    }
  },

  // Hermes admin dashboard (Issue #400 — browser JS, Chart.js)
  {
    files: ["hermes/**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "script",
      globals: {
        ...globals.browser,
        Chart: "readonly"
      }
    },
    rules: {
      "no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_"
        }
      ]
    }
  },

  // Ignore patterns
  {
    ignores: [
      "node_modules/**",
      "dist/**",
      "coverage/**",
      ".git/**"
    ]
  }
];
