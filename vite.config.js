/* eslint-disable import/no-extraneous-dependencies */
import legacy from "@vitejs/plugin-legacy";
import { viteStaticCopy } from "vite-plugin-static-copy";

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
        components: "./assets/src/scripts/components.js",
        job_request_create: "./assets/src/scripts/job_request_create.js",
        main: "./assets/src/scripts/main.js",
        "outputs-viewer": "./assets/src/scripts/outputs-viewer/index.jsx",
        staff: "./assets/src/scripts/staff.js",
        tw: "./assets/src/scripts/tw.js",
        workspace_create: "./assets/src/scripts/workspace_create.js",
      },
    },
    outDir: "assets/dist",
    emptyOutDir: true,
  },
  clearScreen: false,
  plugins: [
    legacy({
      targets: ["chrome >= 81, not dead"],
    }),
    viteStaticCopy({
      targets: [
        {
          src: "./node_modules/bootstrap/dist/js/bootstrap.bundle.min.*",
          dest: "vendor",
        },
        {
          src: "./node_modules/htmx.org/dist/htmx.min.js",
          dest: "vendor",
        },
        {
          src: "./node_modules/jquery/dist/jquery.slim.min.*",
          dest: "vendor",
        },
        {
          src: "./node_modules/list.js/dist/list.min.*",
          dest: "vendor",
        },
        {
          src: "./node_modules/select2/dist/css/select2.min.css",
          dest: "vendor",
        },
        {
          src: "./node_modules/select2/dist/js/select2.min.js",
          dest: "vendor",
        },
        {
          src: "./node_modules/@ttskch/select2-bootstrap4-theme/dist/select2-bootstrap4.min.css",
          dest: "vendor",
        },
        {
          src: "./node_modules/tablesorter/dist/js/jquery.tablesorter.min.js",
          dest: "vendor/tablesorter",
        },
        {
          src: "./node_modules/tablesorter/dist/js/jquery.tablesorter.widgets.min.js",
          dest: "vendor/tablesorter",
        },
        {
          src: "./node_modules/tablesorter/dist/css/theme.bootstrap_4.min.css",
          dest: "vendor/tablesorter",
        },
        {
          src: "./node_modules/bs-custom-file-input/dist/bs-custom-file-input.min*",
          dest: "vendor/bs-custom-file-input",
        },
        {
          src: "./assets/src/js/*",
          dest: "js",
        },
      ],
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
