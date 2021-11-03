/** @type {import('@jest/types').Config.InitialOptions} */
module.exports = async () => ({
  collectCoverageFrom: [
    "**/*.{js,jsx}",
    "!**/node_modules/**",
    "!**/vendor/**",
    "!<rootDir>/assets/src/scripts/outputs-viewer/tests/*",
    "!<rootDir>/assets/src/scripts/outputs-viewer/index.jsx",
    "!<rootDir>/assets/src/scripts/outputs-viewer/context/FilesProvider.jsx",
  ],
  coverageThreshold: {
    global: {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: -10,
    },
  },
  moduleNameMapper: {
    "\\.(css|jpg|png|scss)$":
      "<rootDir>/assets/src/scripts/outputs-viewer/tests/empty-module.js",
  },
  roots: ["<rootDir>/assets/src/scripts/outputs-viewer"],
  setupFilesAfterEnv: [
    "window-resizeto/polyfill",
    "<rootDir>/assets/src/scripts/outputs-viewer/tests/jest-setup.js",
  ],
  testEnvironment: "jest-environment-jsdom",
  transform: {
    "^.+\\.(t|j)sx?$": [
      "@swc/jest",
      {
        sourceMaps: true,
      },
    ],
  },
});
