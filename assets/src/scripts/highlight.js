import hljs from "highlight.js/lib/core";
import django from "highlight.js/lib/languages/django";
import "highlight.js/styles/github-dark.css";

hljs.registerLanguage("django", django);
hljs.highlightAll();
