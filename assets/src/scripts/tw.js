import Alpine from "alpinejs/packages/csp/dist/module.esm";
import Screen from "@alpine-collective/toolkit-screen/dist/module.esm";
import "../styles/tw.css";

Alpine.plugin(Screen);

document.addEventListener("alpine:init", () => {
  Alpine.data("header", function () {
    return {
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
        } else {
          return (this.showMainNav = !this.showMainNav);
        }
      },
      closeMainNav() {
        if (this.largerThanMd) {
          return (this.showMainNav = true);
        } else {
          this.showMainNav = false;
        }
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
        } else {
          this.showUserNav = true;
        }
      },
      closeUserNav() {
        if (this.largerThanMd) {
          return (this.showUserNav = false);
        } else {
          this.showUserNav = this.showUserNav;
        }
      },
    };
  });
});

window.Alpine = Alpine;
window.Alpine.start();

// Remove no-transition class after page load
document
  .querySelectorAll(".no-transition")
  .forEach((item) => item.classList.remove("no-transition"));
