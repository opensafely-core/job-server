import hljs from "highlight.js/lib/core";
import django from "highlight.js/lib/languages/django";
import slugify from "slugify";
import "highlight.js/styles/github-dark.css";
import "./_datatable";

hljs.registerLanguage("django", django);
hljs.highlightAll();

document.addEventListener("DOMContentLoaded", () => {
  const headings = document.querySelectorAll(
    '.prose :where(h2, h3):not(:where([class~="not-prose"] *))',
  );

  const toc = /** @type {HTMLUListElement} */ (
    document.getElementById("table-of-contents")
  );

  /**
   * @param {Element} heading - h2 or h3 from the prose content
   */
  function makeListItem(heading) {
    heading.id = slugify(heading.textContent, { lower: true, strict: true });

    const li = document.createElement("li");
    li.dataset.headingId = heading.id;

    const a = document.createElement("a");
    a.href = `#${heading.id}`;
    a.textContent = heading.textContent;

    li.appendChild(a);
    return li;
  }

  for (const heading of headings) {
    const li = makeListItem(heading);

    if (heading.tagName === "H2") {
      toc.appendChild(li);
      continue;
    }

    if (heading.tagName === "H3") {
      const parentH2 = heading.closest("section")?.querySelector("h2");
      if (!parentH2) continue;

      // Find the existing H2 entry in the TOC
      const parentEntry = toc.querySelector(
        `[data-heading-id="${parentH2.id}"]`,
      );
      if (!parentEntry) continue;

      // Append to existing sub-list or create a new one
      let subList = parentEntry.querySelector("ul");
      if (!subList)
        subList = parentEntry.appendChild(document.createElement("ul"));
      subList.appendChild(li);
    }
  }
});
