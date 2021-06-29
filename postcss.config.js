module.exports = {
  plugins: [
    require("postcss-inline-svg"),
    require("autoprefixer"),
    require("cssnano")({
      preset: [
        "default",
        {
          colormin: false,
          discardComments: { removeAll: true },
        },
      ],
    }),
  ],
};
