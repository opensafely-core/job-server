const expandBtns = [...document.querySelectorAll(`[data-expander-button]`)];

expandBtns.map((btn) =>
  btn.addEventListener("click", () => {
    const id = btn.getAttribute("data-expander-button");
    const list = document.querySelector(`[data-expander-list=${id}]`);
    const isAriaExpanded = list.getAttribute("aria-expanded") === "true";

    list.setAttribute("aria-expanded", `${!isAriaExpanded}`);
    list.classList.toggle("hidden");
  }),
);
