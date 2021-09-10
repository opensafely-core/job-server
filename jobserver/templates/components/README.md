# Form Component Templates

Django forms provide ways to render a form instance out to HTML (`.as_p`, etc), but none of these options provide a way for us to customise the HTML to our liking.
They also hide how the HTML is generated under several layers of abstraction.
They also mix validation and presentation, reducing [Locality of Behaviour](https://htmx.org/essays/locality-of-behaviour/).
Many Django form libraries suffer from the same problems.

Instead we're using a light touch approach by abstracting out some form fields.
The aim is tread the fine line between too many abstractions and hand typing the HTML for all forms.


## Usage
Components live in the `jobserver/templates/components` directory and are included like so:

    {% include "components/form_roles.html" with field=form.roles label="Roles" name="roles" %}


Each component expects 3 variables to be passed in:

* `field`: the Field instance from your form.
* `label`: a text label.
* `name`: the field name used in your form.


## Creating a New Component
Try to only do this when there are 3 or more examples of a field.

1. Create a new file in `jobserver/templates/components`.
1. Copy an existing use of the field you're abstracting to your new template
1. Use `field` to access the Field object for things like error checking, value, etc
1. Use `label` to make the `<label>` content configurable.
1. Use `name` to build the contents of the `id` attribute on the `<input>` tag, like so `id_{{ name }}`, use the same method with the `for` attribute on the `<label>` tag.
1. Use `name` for the contents of the `<input>`s `name` attribute.
