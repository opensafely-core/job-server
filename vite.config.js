import legacy from "@vitejs/plugin-legacy";
import copy from "rollup-plugin-copy";

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
        main: "./assets/src/scripts/main.js",
        project_create: "./assets/src/scripts/project_create.js",
        workspace_create: "./assets/src/scripts/workspace_create.js",
        workspace_detail: "./assets/src/scripts/workspace_detail.js",
      },
      external: ["list.js"],
      output: {
        globals: {
          "list.js": "List",
        },
      },
    },
    outDir: "assets/dist",
    emptyOutDir: true,
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: "$env: " + process.env.NODE_ENV + ";",
      },
    },
  },
  plugins: [
    legacy({
      additionalLegacyPolyfills: ["regenerator-runtime/runtime"],
    }),
    copy({
      targets: [
        {
          src: "./node_modules/bootstrap/dist/js/bootstrap.bundle.min.*",
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
          src: "./assets/src/js/*",
          dest: "./assets/dist/js",
        },
      ],
      hook: "writeBundle",
    }),
  ],
};

export default config;
