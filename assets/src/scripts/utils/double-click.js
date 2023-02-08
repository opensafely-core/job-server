import { wait } from "./wait";

// Ignore double-clicks on submit buttons
document
  .querySelectorAll(
    `input[type="submit"]:not(.btn--allow-double-click),
    button[type="submit"]:not(.btn--allow-double-click)`
  )
  .forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      // Wait for 1ms to trigger all button onClick events
      await wait(1);

      // Disable the button, wait 1s then reenable
      e.target.setAttribute("disabled", true);
      await wait(1000);
      e.target.removeAttribute("disabled");
    });
  });
