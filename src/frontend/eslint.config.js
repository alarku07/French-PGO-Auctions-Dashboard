import pluginVue from "eslint-plugin-vue";
import tseslint from "typescript-eslint";
import vueParser from "vue-eslint-parser";

export default tseslint.config(
  {
    ignores: ["dist/", "node_modules/", "*.min.js", "coverage/"],
  },
  ...pluginVue.configs["flat/recommended"],
  ...tseslint.configs.recommended,
  {
    // After spreading tseslint (which sets a global TypeScript parser), explicitly
    // re-assign vue-eslint-parser as the outer parser for .vue files so that
    // Vue template syntax is parsed correctly. The TypeScript parser handles
    // <script lang="ts"> blocks as the inner parser.
    files: ["**/*.vue"],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tseslint.parser,
        ecmaVersion: "latest",
        sourceType: "module",
      },
    },
  },
  {
    rules: {
      "vue/multi-word-component-names": "off",
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    },
  },
);
