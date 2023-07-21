/* eslint-disable no-return-assign */
import Screen from "@alpine-collective/toolkit-screen/dist/module.esm";
import "@zachleat/details-utils";
import Alpine from "alpinejs/packages/csp/dist/module.esm";
import "../styles/tw.css";
import "./_alert";
import "./_plausible";
import "./utils/double-click";

Alpine.plugin(Screen);

document.addEventListener("alpine:init", () => {
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
