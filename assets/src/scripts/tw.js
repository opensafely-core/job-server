/* eslint-disable no-return-assign */
import Screen from "@alpine-collective/toolkit-screen/dist/module.esm";
import Alpine from "alpinejs/packages/csp/dist/module.esm";
import "../styles/tw.css";
import "./utils/double-click";
import "./_alert";
import "./_plausible";

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
      // eslint-disable-next-line func-names
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
