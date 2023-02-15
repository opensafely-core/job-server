module.exports = {
  root: true,
  extends: ["airbnb", "airbnb/hooks", "prettier"],
  plugins: ["prettier", "testing-library"],
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
  },
  env: {
    browser: true,
  },
  parserOptions: {
    ecmaVersion: 2020,
  },
};
