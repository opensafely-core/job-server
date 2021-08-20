// Only used by Jest
module.exports = {
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
};
