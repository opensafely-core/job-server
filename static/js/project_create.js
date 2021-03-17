const addForm = (name, event) => {
  // Get the existing total form count so we can set the correct prefix and
  // bump this count after adding the form
  const formIndex = $(`#id_${name}-TOTAL_FORMS`).val();

  /**
    * Construct a new form from the template.
    * In the template we've created a template form setting the id (really just
    * a counter for each form) to __prefix__ so we can set it here based on
    * counter in the FormSet's management form (id_{name}-TOTAL_FORMS above).
    */
  const newForm = $(`#${name}-forms .template`)
    .html()
    .replace(/__prefix__/g, formIndex);

  // Add the new form to the end of the forms
  $(`.${name}-form`).last().after(newForm);

  // Update the number of total forms
  $(`#id_${name}-TOTAL_FORMS`).val(parseInt(formIndex) + 1);

  event.preventDefault();
};

const removeRow = (name, event) => {
  const classes = [...event.target.classList].filter((c) => c.startsWith(name));

  if (classes.length < 1) {
    console.error(
      `no classes beginning with ${name} in remove button class list`
    );
    return;
  }

  const formId = classes[0];
  const form = document.getElementById(formId);

  // flip the <name>-DELETE checkbox to tell the formset we're deleting this
  // form from the formset
  const deleted = document.getElementById(`${formId}-DELETE`);
  deleted.setAttribute("value", "on");

  // hide the deleted form
  form.classList.add("d-none");

  event.preventDefault();
};

$(document).ready(() => {
  $("#add-researcher").click((event) => addForm("researcher", event));

  $(document).on("click", ".remove-researcher", (event) =>
    removeRow("researcher", event)
  );
});
