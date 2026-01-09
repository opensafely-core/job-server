import json

import pytest

from jobserver.jobs.daily import dump_sanitised_db


class StubCursor:
    def __init__(self, rows):
        self._rows = rows
        self.executed = []

    def execute(self, sql, params):
        self.executed.append((sql, params))

    def fetchall(self):
        return self._rows


class RecordingCursor:
    def __init__(self):
        self.executed = []

    def execute(self, sql):
        self.executed.append(sql)


@pytest.fixture
def job():
    return dump_sanitised_db.Job()


def test_load_allowlist_success(tmp_path, job):
    path = tmp_path / "allow_list.json"
    path.write_text(
        json.dumps({"users": ["id", "email"], "jobs": ["id"]}), encoding="utf-8"
    )

    allowlist = job._load_allowlist(str(path))

    assert allowlist == {"users": ["id", "email"], "jobs": ["id"]}


def test_load_allowlist_missing_file_returns_empty(job, capsys):
    path = "/tmp/does-not-exist.json"

    assert job._load_allowlist(path) == {}
    captured = capsys.readouterr()
    assert f"Allowlist file not found at {path}" in captured.err


def test_load_allowlist_logs_error_on_bad_json(tmp_path, job, capsys):
    bad_file = tmp_path / "allow_list.json"
    bad_file.write_text("{not valid json}", encoding="utf-8")

    result = job._load_allowlist(str(bad_file))

    assert result == {}
    captured = capsys.readouterr()
    assert "Error loading allowlist file" in captured.err


def test_fake_expression_char_column(job):
    expr = job._fake_expression("users", "email", {"data_type": "character varying"})

    assert "fake_users_email" in expr
    assert "random" in expr


def test_fake_expression_integer_column(job):
    expr = job._fake_expression("stats", "count", {"data_type": "integer"})

    assert expr == "0"


def test_fake_expression_timestamp_column(job):
    expr = job._fake_expression("events", "created_at", {"data_type": "timestamp"})

    assert expr == "now()"


def test_fake_expression_unknown_type(job):
    with pytest.raises(ValueError):
        job._fake_expression("invalid", "payload", {"data_type": "bytea"})


def test_valid_ident(job):
    assert job._valid_ident("safe_name")
    assert not job._valid_ident("1starts_with_digit")
    assert not job._valid_ident("danger!zone")


def test_normalize_table_name_with_schema(job):
    schema, table = job._normalize_table_name("special.schema_table")

    assert schema == "special"
    assert table == "schema_table"


def test_normalize_table_name_without_schema(job):
    schema, table = job._normalize_table_name("plain_table")

    assert schema == "public"
    assert table == "plain_table"


def test_normalize_table_name_rejects_invalid_identifiers(job):
    with pytest.raises(ValueError):
        job._normalize_table_name("bad-schema.bad$table")


def test_get_column_metadata_returns_list(job):
    cursor = StubCursor([("id", "integer"), ("email", "character varying")])

    cols, meta = job._get_column_metadata(cursor, "public", "users")

    assert cols == ["id", "email"]
    assert meta["email"]["data_type"] == "character varying"
    assert cursor.executed


def test_get_column_metadata_handles_missing_table(job):
    cols, meta = job._get_column_metadata(StubCursor([]), "public", "nonexistent")

    assert cols == []
    assert meta == {}


def test_build_allowed_set_returns_unique_columns(job):
    allowed = job._build_allowed_set("table", ["col_a", "col_b", "col_a"])

    assert allowed == {"col_a", "col_b"}


def test_build_allowed_set_rejects_invalid_columns(job):
    with pytest.raises(ValueError):
        job._build_allowed_set("table", ["valid", "not-ok!"])


def test_create_safe_table_builds_sql(job):
    cursor = RecordingCursor()

    job._create_safe_table(cursor, '"public"."users"', '"temp"."users"')

    assert cursor.executed
    assert "CREATE TABLE IF NOT EXISTS" in cursor.executed[0]


def test_build_select_expressions_copies_allowed(job):
    cols = ["id", "email"]
    allowed = {"id"}
    meta = {"id": {"data_type": "integer"}, "email": {"data_type": "text"}}

    select_exprs, quoted_cols = job._build_select_expressions(
        "users", cols, allowed, meta
    )
    assert quoted_cols == '"id", "email"'
    assert select_exprs[0] == '"id"'
    assert "fake_users_email" in select_exprs[1]
