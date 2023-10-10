import TomSelect from "@remotedevforce/tom-select";
import "./multiselect.css";

const multiselectElements = document.querySelectorAll(`[data-multiselect]`);

const newSelect = (body, opts) => new TomSelect(body, opts);

if (multiselectElements?.length) {
  [...multiselectElements].map((node) => {
    const opts = {
      maxItems: node?.dataset?.maxItems,
      plugins: ["remove_button"],
      placeholder: node?.dataset?.placeholder,
      closeAfterSelect: true,
      optionClass: "multiselect__option",
      itemClass: "multiselect__item",
      wrapperClass: "multiselect__wrapper",
      controlClass: "multiselect__control",
      dropdownClass: "multiselect__dropdown",
      dropdownContentClass: "multiselect__dropdown-content",
      onDropdownOpen(dropdown) {
        dropdown.removeAttribute("style");
      },
      onDropdownClose(dropdown) {
        dropdown.removeAttribute("style");
      },
    };

    return newSelect(node, opts);
  });
}
