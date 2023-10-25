import { wait } from "./wait";

// Ignore double-clicks on submit buttons
document
  .querySelectorAll(
    `input[type="submit"]:not(.btn--allow-double-click),
    button[type="submit"]:not(.btn--allow-double-click)`,
  )
  .forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      if (e.target instanceof HTMLElement) {
        // Wait for 1ms to trigger all button onClick events
        await wait(1);

        // Disable the button
        e.target.setAttribute("disabled", "true");
        e.target.classList.add(
          "!cursor-not-allowed",
          "!bg-slate-300",
          "!border-slate-300",
          "!text-slate-800",
        );

        await wait(30000);
        e.target.removeAttribute("disabled");
        e.target.classList.remove(
          "!cursor-not-allowed",
          "!bg-slate-300",
          "!border-slate-300",
          "!text-slate-800",
        );
      }
    });
  });
