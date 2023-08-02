import path from "node:path";

export default ({ env }) => ({
  plugins: {
    "postcss-import": {},
    "tailwindcss/nesting": "postcss-nesting",
    tailwindcss: {},
    autoprefixer: {},
    "postcss-preset-env": {},
    "postcss-url":
      env !== "production"
        ? {
            url: "inline",
            basePath: path.resolve("assets/src/styles"),
          }
        : false,
  },
});
