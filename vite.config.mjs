/* eslint-disable import/no-extraneous-dependencies */
import react from "@vitejs/plugin-react-swc";
import liveReload from "vite-plugin-live-reload";
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
        "analysis-request-detail":
          "./assets/src/scripts/analysis-request-detail.js",
        "application-form": "./assets/src/scripts/application-form.js",
        "outputs-viewer": "./assets/src/scripts/outputs-viewer/index.jsx",
        "sign-off-repo": "./assets/src/scripts/sign-off-repo.js",
        "staff-base": "./assets/src/scripts/staff-base.js",
        base: "./assets/src/scripts/base.js",
        components: "./assets/src/scripts/components.js",
        interactive: "assets/src/scripts/interactive/main.jsx",
        job_request_create: "./assets/src/scripts/job_request_create.js",
        multiselect: "./templates/_components/multiselect/multiselect.js",
        workspace_create: "./assets/src/scripts/workspace_create.js",
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
    liveReload("templates/**/*.html"),
    react(),
    viteStaticCopy({
      targets: [
        {
          src: "./node_modules/htmx.org/dist/htmx.min.js",
          dest: "vendor",
        },
      ],
    }),
  ],
  test: {
    globals: true,
    environment: "jsdom",
    root: "./assets/src/scripts/outputs-viewer/",
    setupFiles: ["__tests__/test-setup.js"],
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
