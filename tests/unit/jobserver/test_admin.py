from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from jobserver.admin import UserAdmin
from jobserver.models import User

from ...factories import UserFactory


def test_useradmin_approve_users(rf):
    UserFactory.create_batch(5)

    # only work with a subset of created users to ensure we don't somehow
    # address all users
    users = User.objects.order_by("pk")[:2]

    user_admin = UserAdmin(model=User, admin_site=AdminSite())

    request = rf.get("/")
    request.user = UserFactory(is_superuser=True)

    response = user_admin.approve_users(request, users)

    assert response.status_code == 302

    base = reverse("approve-users")
    query = [f"user={u.pk}" for u in users]
    url = f"{base}?{'&'.join(query)}"
    assert response.url == url
