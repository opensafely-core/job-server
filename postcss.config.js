module.exports = {
  plugins: [
    require('autoprefixer'),
    require('cssnano')({
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
