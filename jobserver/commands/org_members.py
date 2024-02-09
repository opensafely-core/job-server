from django.db import transaction


@transaction.atomic()
def update_roles(*, member, by, roles):
    member.roles = roles
    member.save(update_fields=["roles"])
