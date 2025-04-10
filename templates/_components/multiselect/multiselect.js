import TomSelect from "tom-select";

const multiselectElements = document.querySelectorAll(`[data-multiselect]`);

const newSelect = (body, opts) => new TomSelect(body, opts);

if (multiselectElements?.length) {
  [...multiselectElements].map((node) => {
    const opts = {
      maxItems: node?.dataset?.maxItems,
      plugins: ["remove_button"],
      placeholder: node?.dataset?.placeholder,
      closeAfterSelect: true,
      optionClass:
        "border-y border-slate-200 -mt-[1px] cursor-pointer text-slate-800 text-[0.95rem] font-medium py-0.5 px-4 [&.active]:bg-oxford-50",
      itemClass:
        "bg-oxford-50 border border-oxford-300 rounded-lg flex flex-row text-[0.9rem] font-medium gap-1 py-0.5 px-2",
      wrapperClass: "relative",
      controlClass: `
        flex flex-row flex-wrap gap-2
        [&_input]:bg-white [&_input]:border [&_input]:border-slate-300 [&_input]:rounded-lg [&_input]:shadow-xs [&_input]:text-slate-900 [&_input]:text-sm [&_input]:py-2 [&_input]:px-3 [&_input]:w-full
      `,
      dropdownClass:
        "bg-white border border-slate-300 border-t-0 shadow-md h-auto max-h-[20rem] overflow-y-auto py-1 absolute w-full z-100",
      onDropdownOpen(/** @type {HTMLDivElement} */ dropdown) {
        dropdown.removeAttribute("style");
        dropdown.classList.add("block");
        dropdown.classList.remove("hidden");
      },
      onDropdownClose(/** @type {HTMLDivElement} */ dropdown) {
        dropdown.removeAttribute("style");
        dropdown.classList.remove("block");
        dropdown.classList.add("hidden");
      },
      onInitialize() {
        node.classList.add("sr-only");
      },
    };

    return newSelect(node, opts);
  });
}
