import "@github/filter-input-element";
import TomSelect from "@remotedevforce/tom-select";
import hljs from "highlight.js/lib/core";
import json from "highlight.js/lib/languages/json";
import "highlight.js/styles/github.css";
import "../styles/staff-base.css";

hljs.registerLanguage("json", json);

const analysisRequest = document.getElementById("analysisRequest");

if (analysisRequest) {
  analysisRequest.textContent = JSON.stringify(
    JSON.parse(document.getElementById("analysisRequestData").textContent),
    null,
    2,
  );
}

hljs.highlightAll();

const tomSelectEls = document.querySelectorAll(`[data-tom-select]`);

const opts = {
  plugins: ["remove_button"],
  placeholder: "Search for an org",
  closeAfterSelect: true,
  optionClass: "tom-select__option",
  itemClass: "tom-select__item",
  wrapperClass: "tom-select__wrapper",
  controlClass: "tom-select__control",
  dropdownClass: "tom-select__dropdown",
  dropdownContentClass: "tom-select__dropdown-content",
  onDropdownOpen(dropdown) {
    dropdown.removeAttribute("style");
  },
  onDropdownClose(dropdown) {
    dropdown.removeAttribute("style");
  },
};

const newSelect = (body) => new TomSelect(body, opts);

if (tomSelectEls?.length) {
  [...tomSelectEls].map((node) => newSelect(node));
}
