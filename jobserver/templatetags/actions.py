from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag
def actions_row(name, actions):
    status = actions[name]["status"]

    needs = actions[name]["needs"]
    needs = ", ".join(f"<code>{n}</code>" for n in needs)

    row = f"""
        <td class="align-middle">

          <div class="btn-group-toggle" data-toggle="buttons">
            <label class="btn btn-outline-success">
              <input type="checkbox" name="requested_actions" value="{name}" /> Run
            </label>
          </div>

        </td>
        <td class="align-middle"><code>{name}</code></td>
        <td class="align-middle"><code>{needs}</code></td>
        <td class="align-middle">{status}</td>
    """

    return mark_safe(row)
