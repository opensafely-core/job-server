/* eslint-disable array-callback-return, no-param-reassign */
const content = document.getElementById("applicationForm");
const links = content.getElementsByTagName("a");

[...links].map((link) => {
  if (link.hostname !== window.location.hostname) {
    link.target = "_blank";
    link.rel = "noopener noreferrer";
  }
});

// Select the textarea element.
const textAreaElement = document.getElementById("id_study_purpose");

// Select the character counter element.
const characterCounterElement = document.getElementById("character_counter");

// Select the element that shows the number of characters typed in the textarea.
const typedCharactersElement = document.getElementById("typed_characters");

// Define the maximum number of characters allowed.
const maximumCharacters = textAreaElement.getAttribute("max_length");

// Add a "keydown" event listener on the textarea element.
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
  //
  // Display the number of characters typed.
  typedCharactersElement.textContent = typedCharacters;

  /**
   * Change the character counter text colour to "orange" if the typed
   * characters number is between 200 to 250. If more, then change the colour to "red".
   */
  if (typedCharacters < 1400) {
    characterCounterElement.classList = "";
  } else if (typedCharacters >= 1400 && typedCharacters < 1450) {
    characterCounterElement.classList = "text-warning";
  } else if (typedCharacters >= 1450) {
    characterCounterElement.classList = "text-danger";
  }

  return undefined;
});
