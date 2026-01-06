// ESLint Flat Config for Aletheia browser extensions
// Migrated from .eslintrc.json per Issue #157 / LLD 1157

import js from "@eslint/js";
import globals from "globals";

export default [
  // Base recommended rules
  js.configs.recommended,

  // Browser extension configuration
  {
    files: ["extensions/**/*.js"],
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
      "prefer-const": "error"
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
