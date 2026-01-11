import pytest
from django.contrib.auth import get_user_model
from django.db import connection

from jobserver.jobs.daily import dump_sanitised_db


@pytest.mark.django_db
def test_allowlist_tables_and_columns_exist():
    """Ensure every allow-listed table/column exists in the database."""

    job = dump_sanitised_db.Job()
    allowlist = job._load_allowlist(dump_sanitised_db.ALLOWLIST_PATH)

    with connection.cursor() as cur:
        for table, columns in allowlist.items():
            schema_name, table_name = job._normalize_table_name(table)
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                """,
                [schema_name, table_name],
            )
            rows = cur.fetchall()
            assert rows, f"Table {schema_name}.{table_name} from allow list not found"

            existing_cols = {row[0] for row in rows}
            missing = [col for col in columns if col not in existing_cols]
            assert not missing, (
                f"Table {schema_name}.{table_name} missing columns: {missing}"
            )


@pytest.mark.django_db
def test_create_safe_schema_scrubs_disallowed_columns():
    """Copying into the temp schema keeps allow-listed data and fakes everything else."""
    job = dump_sanitised_db.Job()
    user_model = get_user_model()
    user = user_model.objects.create(
        username="testuser",
        email="testuser@gmail.com",
        fullname="Real Name",
        password="secret",
        roles=[],
    )

    allowlist = {"jobserver_user": ["id", "username", "roles", "fullname"]}

    job._drop_temp_schema()
    try:
        job._create_safe_schema_and_copy(allowlist)

        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, email, password
                FROM "temp_scrubbed_schema"."jobserver_user"
                WHERE id = %s
                """,
                [user.id],
            )
            row = cur.fetchone()
        assert row is not None
        assert row[0] == user.id
        assert row[1] == user.username
        assert row[2].startswith("fake_jobserver_user_email_")
        assert row[3].startswith("fake_jobserver_user_password_")
    finally:
        job._drop_temp_schema()
