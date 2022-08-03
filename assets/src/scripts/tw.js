import Screen from "@alpine-collective/toolkit-screen";
import Alpine from "alpinejs";
import "../styles/tw.css";

Alpine.plugin(Screen);

window.Alpine = Alpine;

Alpine.start();
