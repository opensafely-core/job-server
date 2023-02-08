// eslint-disable-next-line import/prefer-default-export
export const wait = (amount = 0) =>
  // eslint-disable-next-line no-promise-executor-return
  new Promise((resolve) => setTimeout(resolve, amount));
