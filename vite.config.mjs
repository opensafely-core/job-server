/* eslint-disable import/no-extraneous-dependencies */
import legacy from "@vitejs/plugin-legacy";
import react from "@vitejs/plugin-react-swc";
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
        "application-form": "./assets/src/scripts/application-form.js",
        "analysis-request-detail":
          "./assets/src/scripts/analysis-request-detail.js",
        "outputs-viewer": "./assets/src/scripts/outputs-viewer/index.jsx",
        components: "./assets/src/scripts/components.js",
        index: "./assets/src/scripts/index.js",
        interactive: "assets/src/scripts/interactive/main.jsx",
        job_request_create: "./assets/src/scripts/job_request_create.js",
        main: "./assets/src/scripts/main.js",
        staff: "./assets/src/scripts/staff.js",
        tw: "./assets/src/scripts/tw.js",
        workspace_create: "./assets/src/scripts/workspace_create.js",
        "sign-off-repo": "./assets/src/scripts/sign-off-repo.js",
        "staff-tw": "./assets/src/scripts/staff-tw.js",
      },
    },
    outDir: "assets/dist",
    emptyOutDir: true,
  },
  server: {
    origin: "http://localhost:5173",
  },
  clearScreen: false,
  plugins: [
    react(),
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
    setupFiles: ["__tests__/test-setup.js", "window-resizeto/polyfill"],
    exclude: [
      "__tests__/test-setup.js",
      "__tests__/test-utils.jsx",
      "__tests__/__mocks__/*",
      "__tests__/helpers/*",
    ],
    coverage: {
      provider: "v8",
      lines: 90,
      functions: 90,
      branches: 90,
      statements: -10,
    },
  },
};

export default config;
