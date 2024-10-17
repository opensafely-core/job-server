import prettier from "eslint-plugin-prettier";
import testingLibrary from "eslint-plugin-testing-library";
import globals from "globals";
import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all,
});

export default [
  ...compat.extends("airbnb", "airbnb/hooks", "prettier"),
  {
    plugins: {
      prettier,
      "testing-library": testingLibrary,
    },

    languageOptions: {
      globals: {
        ...globals.browser,
      },

      ecmaVersion: 2020,
      sourceType: "module",
    },

    rules: {
      "prettier/prettier": "error",
      "react/jsx-props-no-spreading": "off",

      "react/jsx-sort-props": [
        "error",
        {
          ignoreCase: true,
          reservedFirst: true,
        },
      ],

      "react/function-component-definition": [
        2,
        {
          namedComponents: "function-declaration",
          unnamedComponents: "arrow-function",
        },
      ],

      "react/react-in-jsx-scope": [0],

      "import/order": [
        "error",
        {
          groups: [
            ["builtin", "external", "internal"],
            "parent",
            "sibling",
            "index",
          ],
          "newlines-between": "never",

          alphabetize: {
            order: "asc",
            caseInsensitive: true,
          },
        },
      ],

      "jsx-a11y/label-has-associated-control": [
        2,
        {
          inputComponents: ["Field"],
        },
      ],

      "import/no-unresolved": [
        "error",
        {
          ignore: ["wouter"],
        },
      ],

      "react/require-default-props": [
        2,
        {
          functions: "defaultArguments",
        },
      ],
    },
  },
];
