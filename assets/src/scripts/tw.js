import Screen from "@alpine-collective/toolkit-screen";
import Alpine from "alpinejs";
import "../styles/tw.css";

Alpine.plugin(Screen);

window.Alpine = Alpine;

Alpine.start();

// Remove no-transition class after page load
document
  .querySelectorAll(".no-transition")
  .forEach((item) => item.classList.remove("no-transition"));
