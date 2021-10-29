# import sys

# from django.core.management import call_command
# from django.core.management.base import BaseCommand


# # multiple call_command lines

# class Command(BaseCommand):
#     help = ""  # noqa: A003

#     def handle(self, *args, **options):
#         usernames = get_admins()

#         try:
#             ensure_admins(usernames)
#         except Exception as e:
#             print(str(e), file=sys.stderr)
#             sys.exit(1)
