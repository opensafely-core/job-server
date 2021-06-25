/**
 * @type {import('vite').UserConfig}
 */
const config = {
  base: "/static/",
  build: {
    manifest: true,
    rollupOptions: {
      input: {
        main: "./assets/src/scripts/main.js",
      },
    },
    outDir: "assets/dist",
    emptyOutDir: true,
  },
  plugins: [],
};

export default config;
