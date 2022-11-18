import AnchorJS from "anchor-js";
import hljs from "highlight.js/lib/core";
import django from "highlight.js/lib/languages/django";
import "highlight.js/styles/github-dark.css";

hljs.registerLanguage("django", django);
hljs.highlightAll();

const anchors = new AnchorJS();
anchors.add(".prose h2:not([data-anchor=ignore]");

function addNavItem(ul, href, text) {
  const listItem = document.createElement("li");
  const anchorItem = document.createElement("a");
  const textNode = document.createTextNode(text);

  anchorItem.href = href;
  ul.appendChild(listItem);
  listItem.appendChild(anchorItem);
  anchorItem.appendChild(textNode);
}

function generateTableOfContents(els) {
  let anchoredElText;
  let anchoredElHref;
  const ul = document.createElement("ul");

  document.getElementById("table-of-contents").appendChild(ul);

  els.map((_, i) => {
    anchoredElText = els[i].textContent;
    anchoredElHref = els[i]
      .querySelector(".anchorjs-link")
      .getAttribute("href");
    return addNavItem(
      ul,
      anchoredElHref,
      anchoredElText,
      "toc-li-".concat(els[i].tagName)
    );
  });
}

generateTableOfContents(anchors.elements);
