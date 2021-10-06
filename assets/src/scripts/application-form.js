/* eslint-disable array-callback-return, no-param-reassign */
const content = document.getElementById("applicationForm");
const links = content.getElementsByTagName("a");

[...links].map((link) => {
  if (link.hostname !== window.location.hostname) {
    link.target = "_blank";
    link.rel = "noopener noreferrer";
  }
});
