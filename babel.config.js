// Only used by Jest
module.exports = {
  env: {
    test: {
      presets: ["@babel/preset-env", "@babel/preset-react"],
      plugins: [
        // Fix for import.meta.env.VITE_SENTRY_DSN,
        () => ({
          visitor: {
            MetaProperty(path) {
              path.replaceWithSourceString("process");
            },
          },
        }),
      ],
    },
  },
};
