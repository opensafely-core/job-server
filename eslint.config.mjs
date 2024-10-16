import pluginJs from "@eslint/js";
import pluginReact from "eslint-plugin-react";
import globals from "globals";
import eslintPluginPrettierRecommended from "eslint-plugin-prettier/recommended";
import jsxA11y from "eslint-plugin-jsx-a11y";

export default [
  {
    files: ["**/*.{js,mjs,cjs,jsx}"],
    settings: {
      react: {
        version: "detect",
      },
    },
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.nodeBuiltin,
      },
    },
  },
  jsxA11y.flatConfigs.recommended,
  pluginJs.configs.recommended,
  pluginReact.configs.flat.recommended,
  eslintPluginPrettierRecommended,
  {
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
      "jsx-a11y/label-has-associated-control": [
        2,
        {
          inputComponents: ["Field"],
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
