const configExtends = ["airbnb", "airbnb/hooks", "prettier"];
const plugins = ["prettier", "testing-library"];
const env = {
  browser: true,
};
const parserOptions = {
  ecmaVersion: 2020,
};

const rules = {
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
};

module.exports = {
  root: true,
  extends: configExtends,
  plugins,
  rules,
  env,
  parserOptions,

  overrides: [
    {
      files: ["*.ts", "*.tsx"],
      excludedFiles: ["*.js", "*.jsx"],
      extends: ["airbnb", "airbnb/hooks", "airbnb-typescript", "prettier"],
      rules: {
        ...rules,
        "react/react-in-jsx-scope": [0],
      },
      parserOptions: {
        ...parserOptions,
        project: "./tsconfig.json",
      },
    },
  ],
};
