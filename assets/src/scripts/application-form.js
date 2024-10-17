const content = document?.getElementById("applicationForm");
const links = content?.getElementsByTagName("a");

if (links?.length) {
  [...links].map((link) => {
    if (link.hostname !== window.location.hostname) {
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    }
  });
}

// Find all character count instances
const characterCounts = document?.querySelectorAll("[data-character-count]");

characterCounts?.forEach((formGroup) => {
  // Select the textarea element
  const textAreaElement = formGroup.parentElement.querySelector("textarea");

  // Select the maximum amount of characters
  const maximumCharacters = textAreaElement.getAttribute("maxlength");

  // Select the character counter element.
  const characterCounterElement = formGroup.querySelector(
    "[data-character-counter]",
  );

  // Select the element that shows the number of characters typed in the textarea.
  const typedCharactersElement = formGroup.querySelector(
    "[data-typed-characters]",
  );

  textAreaElement.addEventListener("keyup", () => {
    // Count the number of characters typed.
    const typedCharacters = textAreaElement.value.length;

    /**
     * Check if the typed characters is more than allowed characters limit.
     * If yes, then return false.
     */
    if (typedCharacters > maximumCharacters) {
      return false;
    }

    typedCharactersElement.textContent = typedCharacters;

    /**
     * Change the character counter text colour to "orange" if the typed
     * characters number is between 1400 to 1450. If more, then change the
     * colour to "red".
     */
    if (typedCharacters >= 1400 && typedCharacters < 1450) {
      characterCounterElement.classList.remove("text-bn-ribbon-800");
      return characterCounterElement.classList.add("text-bn-sun-800");
    }

    if (typedCharacters >= 1450) {
      characterCounterElement.classList.remove("text-bn-sun-800");
      return characterCounterElement.classList.add("text-bn-ribbon-800");
    }

    return characterCounterElement.classList.remove(
      ...characterCounterElement.classList,
    );
  });
});
