export function classNames(...classes: (string | null | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

export function scrollToTop() {
  if ("scrollRestoration" in window.history) {
    window.history.scrollRestoration = "manual";
  }
  window.scroll({
    top: 0,
    left: 0,
    behavior: "auto",
  });
}

export function delay(ms: number) {
  // eslint-disable-next-line no-promise-executor-return
  return new Promise((res) => setTimeout(res, ms));
}
