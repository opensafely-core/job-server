/* eslint-disable no-return-assign */
import Screen from "@alpine-collective/toolkit-screen/dist/module.esm";
import Alpine from "alpinejs/packages/csp/dist/module.esm";
import "../styles/tw.css";

Alpine.plugin(Screen);

document.addEventListener("alpine:init", () => {
  Alpine.data("header", () => ({
    get largerThanMd() {
      return this.$screen("md");
    },

    showMainNav: false,
    get isMainNavOpen() {
      if (this.largerThanMd) {
        return true;
      }
      return this.showMainNav;
    },
    clickMainNav() {
      if (this.largerThanMd) {
        this.showMainNav = true;
      }
      return (this.showMainNav = !this.showMainNav);
    },
    closeMainNav() {
      if (this.largerThanMd) {
        return (this.showMainNav = true);
      }
      return (this.showMainNav = false);
    },

    showUserNav: false,
    get isUserNavOpen() {
      if (!this.largerThanMd) {
        return true;
      }
      return this.showUserNav;
    },
    clickUserNav() {
      if (this.largerThanMd) {
        return (this.showUserNav = !this.showUserNav);
      }
      return (this.showUserNav = true);
    },
    closeUserNav() {
      if (this.largerThanMd) {
        return (this.showUserNav = false);
      }
      return null;
    },
  }));

  Alpine.data("dropdown", () => ({
    open: false,

    init() {
      this.$refs.dialogue.classList.add("hidden");
    },

    trigger: {
      "@click": function () {
        this.open = !this.open;
        this.$refs.dialogue.classList.toggle("hidden");
        this.$refs.dialogue.setAttribute("aria-expanded", this.open);
      },
    },
  }));
});

window.Alpine = Alpine;
window.Alpine.start();

if (document.location.hostname === "jobs.opensafely.org") {
  const script = document.createElement("script");
  script.defer = true;
  script.setAttribute("data-domain", "jobs.opensafely.org");
  script.id = "plausible";
  script.src = "https://plausible.io/js/plausible.compat.js";

  document.head.appendChild(script);
}
