import hljs from "highlight.js/lib/core";
import django from "highlight.js/lib/languages/django";
import slugify from "slugify";
import "highlight.js/styles/github-dark.css";
import "./_datatable";

hljs.registerLanguage("django", django);
hljs.highlightAll();

document.addEventListener("DOMContentLoaded", () => {
  const anchors = document.querySelectorAll(
    '.prose :where(h2, h3):not(:where([class~="not-prose"] *))',
  );

  const ul = document.getElementById("table-of-contents");

  anchors.forEach((heading) => {
    // eslint-disable-next-line no-param-reassign
    heading.id = `${slugify(heading.textContent, {
      lower: true,
      strict: true,
    })}`;

    if (heading.tagName === "H3") {
      return ul.querySelector("li:last-of-type ul").insertAdjacentHTML(
        "beforeend",
        `<li>
          <a href="#${heading.id}">
            ${heading.textContent}
          </a>
        </li>`,
      );
    }

    return ul.insertAdjacentHTML(
      "beforeend",
      `<li>
        <a href="#${heading.id}">
          ${heading.textContent}
        </a>
        ${heading.parentElement.querySelector("h3") ? `<ul></ul>` : ""}
      </li>`,
    );
  });
});
