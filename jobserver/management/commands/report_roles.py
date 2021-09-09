from django.core.management.base import BaseCommand

from ...authorization.utils import build_role_to_actions


class Command(BaseCommand):
    def handle(self, **kwargs):
        role_to_actions = build_role_to_actions()

        for role in sorted(role_to_actions, key=lambda role: role.__name__):
            role_name = role.__name__
            print(role_name)
            print("=" * len(role_name))
            print()
            print("can perform the following actions:")

            for action in sorted(
                role_to_actions[role], key=lambda action: action.__name__
            ):
                print(f"  * {action.__name__}")
                print(f"    => {action.__doc__}")
            print()
