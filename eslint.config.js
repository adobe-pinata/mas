import js from "@eslint/js";
import pluginN from "eslint-plugin-n";

export default [
  js.configs.recommended,
  pluginN.configs["flat/recommended"],
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
    },
    rules: {
      "no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      // AIO Runtime deps (@adobe/*) are not installed locally; skip resolution checks
      "n/no-missing-import": "off",
      "n/no-missing-require": "off",
      // process.exit() is intentional in test/integration scripts
      "n/no-process-exit": "off",
      // fetch is widely supported; AIO Runtime Node version may differ from local engines range
      "n/no-unsupported-features/node-builtins": "off",
    },
  },
  // Playwright evaluate() callbacks run in browser context — document/window are valid there
  {
    files: [
      "apps/experience-qa/server/services/browser.js",
      "apps/experience-qa/server/services/language-detector.js",
    ],
    languageOptions: {
      globals: { document: "readonly", window: "readonly" },
    },
  },
  {
    ignores: ["dist/", "local-storage/", "node_modules/"],
  },
];
