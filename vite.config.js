/* eslint-disable import/no-extraneous-dependencies */
import legacy from "@vitejs/plugin-legacy";
import copy from "rollup-plugin-copy";
import { visualizer } from "rollup-plugin-visualizer";

/**
 * @type {import('vite').UserConfig}
 */
const config = {
  base: "/static/",
  build: {
    manifest: true,
    rollupOptions: {
      input: {
        index: "./assets/src/scripts/index.js",
        "application-form": "./assets/src/scripts/application-form.js",
        job_request_create: "./assets/src/scripts/job_request_create.js",
        main: "./assets/src/scripts/main.js",
        workspace_create: "./assets/src/scripts/workspace_create.js",
        "outputs-viewer": "./assets/src/scripts/outputs-viewer/index.jsx",
        tw: "./assets/src/scripts/tw.js",
      },
    },
    outDir: "assets/dist",
    emptyOutDir: true,
    sourcemap: "hidden",
  },
  clearScreen: false,
  css: { preprocessorOptions: { scss: { charset: false } } },
  plugins: [
    legacy({
      targets: ["chrome >= 81, not dead"],
    }),
    copy({
      targets: [
        {
          src: "./node_modules/bootstrap/dist/js/bootstrap.bundle.min.*",
          dest: "./assets/dist/vendor",
        },
        {
          src: "./node_modules/htmx.org/dist/htmx.min.js",
          dest: "./assets/dist/vendor",
        },
        {
          src: "./node_modules/jquery/dist/jquery.slim.min.*",
          dest: "./assets/dist/vendor",
        },
        {
          src: "./node_modules/list.js/dist/list.min.*",
          dest: "./assets/dist/vendor",
        },
        {
          src: "./node_modules/select2/dist/css/select2.min.css",
          dest: "./assets/dist/vendor",
        },
        {
          src: "./node_modules/select2/dist/js/select2.min.js",
          dest: "./assets/dist/vendor",
        },
        {
          src: "./node_modules/@ttskch/select2-bootstrap4-theme/dist/select2-bootstrap4.min.css",
          dest: "./assets/dist/vendor",
        },
        {
          src: "./node_modules/tablesorter/dist/js/jquery.tablesorter.min.js",
          dest: "./assets/dist/vendor/tablesorter",
        },
        {
          src: "./node_modules/tablesorter/dist/js/jquery.tablesorter.widgets.min.js",
          dest: "./assets/dist/vendor/tablesorter",
        },
        {
          src: "./node_modules/tablesorter/dist/css/theme.bootstrap_4.min.css",
          dest: "./assets/dist/vendor/tablesorter",
        },
        {
          src: "./node_modules/bs-custom-file-input/dist/bs-custom-file-input.min*",
          dest: "./assets/dist/vendor/bs-custom-file-input",
        },
        {
          src: "./assets/src/js/*",
          dest: "./assets/dist/js",
        },
      ],
      hook: "writeBundle",
    }),
    visualizer({
      filename: "assets/stats.html",
      brotliSize: true,
    }),
  ],
  test: {
    globals: true,
    environment: "jsdom",
    root: "./assets/src/scripts/outputs-viewer/",
    setupFiles: [
      "assets/src/scripts/outputs-viewer/__tests__/test-setup.js",
      "window-resizeto/polyfill",
    ],
    coverage: {
      provider: "c8",
      lines: 90,
      functions: 90,
      branches: 90,
      statements: -10,
    },
  },
};

export default config;
