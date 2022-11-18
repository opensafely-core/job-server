import AnchorJS from "anchor-js";
import hljs from "highlight.js/lib/core";
import django from "highlight.js/lib/languages/django";
import "highlight.js/styles/github-dark.css";

hljs.registerLanguage("django", django);
hljs.highlightAll();

const anchors = new AnchorJS();

document.addEventListener("DOMContentLoaded", () => {
  anchors.add('.prose :where(h2):not(:where([class~="not-prose"] *))');

  const ul = document.createElement("ul");
  document.getElementById("table-of-contents").appendChild(ul);

  anchors.elements.forEach((heading) =>
    ul.insertAdjacentHTML(
      "beforeend",
      `<li>
        <a href="#${heading.id}">
          ${heading.textContent}
        </a>
      </li>`
    )
  );
});
