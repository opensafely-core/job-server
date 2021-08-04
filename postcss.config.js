/* eslint-disable import/no-extraneous-dependencies */
const autoprefixer = require("autoprefixer");
const cssnano = require("cssnano");
const path = require("path");
const url = require("postcss-url");

const options = {
  url: "inline",
  basePath: path.resolve("assets/src/styles"),
};

module.exports = ({ env }) => ({
  plugins:
    env === "production"
      ? [
          autoprefixer(),
          cssnano({
            preset: [
              "default",
              {
                colormin: false,
                discardComments: { removeAll: true },
              },
            ],
          }),
        ]
      : [url(options)],
});
