const isLoggedIn = document.head.querySelector(`meta[name="is_logged_in"]`);
const isStaff = document.head.querySelector(`meta[name="is_staff"]`);

if (document.location.hostname === "jobs.opensafely.org") {
  const script = document.createElement("script");
  script.defer = true;
  script.setAttribute("data-domain", "jobs.opensafely.org");
  script.id = "plausible";
  script.src = "https://plausible.io/js/script.pageview-props.js";

  if (isLoggedIn) {
    script.setAttribute("event-is_logged_in", isLoggedIn.content);
  }

  if (isStaff) {
    script.setAttribute("event-is_staff", isStaff.content);
  }

  document.head.appendChild(script);
}
