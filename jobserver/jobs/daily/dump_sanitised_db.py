import json
import os
import pathlib
import subprocess
import sys
import tempfile

from django.conf import settings
from django.db import connection
from django_extensions.management.jobs import DailyJob
from sentry_sdk.crons.decorator import monitor

from services.sentry import monitor_config


# Temporary schema to hold safe copies
TEMP_SCHEMA = "temp_scrubbed_schema"
OUTPUT_PATH = pathlib.Path("/storage/sanitised_jobserver.dump")
ALLOWLIST_PATH = pathlib.Path(__file__).with_name("allow_list.json")
OUT_DIR = OUTPUT_PATH.parent


class Job(DailyJob):
    help = "Dump a safe copy of the DB with non-allowlisted columns replaced by fake values"

    # Keeping the job at 2pm right now to test this script in production. Will change to 7pm once the testing is done.
    @monitor(
        monitor_slug="dump_sanitised_db", monitor_config=monitor_config("0 14 * * *")
    )
    def execute(self):
        db = settings.DATABASES["default"]
        allowlist = self._load_allowlist(ALLOWLIST_PATH)
        allowlist_exists = bool(allowlist)

        if not OUT_DIR.is_dir():
            print(f"Unknown output directory: {OUT_DIR}", file=sys.stderr)
            sys.exit(1)

        with tempfile.NamedTemporaryFile(
            prefix="jobserver-", dir=str(OUT_DIR), delete=False
        ) as tmp:
            tmp_name = tmp.name

        try:
            if allowlist_exists:
                self._create_safe_schema_and_copy(allowlist)
                try:
                    self._run_pg_dump_for_schema(tmp_name, TEMP_SCHEMA, db)
                finally:
                    self._drop_temp_schema()
            else:
                self._run_pg_dump_schema_only(tmp_name, db)

            os.chmod(tmp_name, 0o600)
            os.replace(tmp_name, OUTPUT_PATH)
        except Exception:
            try:
                if os.path.exists(tmp_name):
                    os.remove(tmp_name)
            except Exception:
                pass
            raise

    def _load_allowlist(self, path: str | None) -> dict[str, list[str]]:
        if not path:
            return {}

        try:
            with open(path, encoding="utf-8") as file:
                data = json.load(file)
            allowlist_dict: dict[str, list[str]] = {}
            for table_name, cols in data.items():
                if isinstance(cols, list) and cols:
                    allowlist_dict[str(table_name)] = [str(c) for c in cols]
            return allowlist_dict
        except FileNotFoundError:
            print(
                f"Allowlist file not found at {path}; proceeding with schema-only dump",
                file=sys.stderr,
            )
            return {}
        except Exception as exc:
            print(f"Error loading allowlist file {path}: {exc}", file=sys.stderr)
            return {}

    def _fake_expression(self, table: str, col: str, meta: dict) -> str:
        dtype = (meta.get("data_type") or "").lower()

        if "char" in dtype or "text" in dtype:
            return f"'fake_{table}_{col}_' || FLOOR(random() * 1000000)::bigint"

        if "integer" in dtype or "bigint" in dtype or "smallint" in dtype:
            return "0"

        if "timestamp" in dtype or "date" in dtype:
            return "now()"

        raise ValueError(
            f"Unsupported data type '{dtype}' for {table}.{col}; add handling or allowlist it"
        )

    def _valid_ident(self, x: str) -> bool:
        return bool(x) and (x.replace("_", "").isalnum()) and (not x[0].isdigit())

    def _normalize_table_name(self, table: str) -> tuple[str, str]:
        if "." in table:
            schema_name, table_name = table.split(".", 1)
        else:
            schema_name = "public"
            table_name = table

        if not self._valid_ident(table_name) or not self._valid_ident(schema_name):
            raise ValueError(f"Invalid table name in allowlist: {table}")

        return schema_name, table_name

    def _get_column_metadata(
        self, cur, schema_name: str, table_name: str
    ) -> tuple[list[str], dict[str, dict[str, str]]]:
        cur.execute(
            """
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position;
            """,
            [schema_name, table_name],
        )
        rows = cur.fetchall()
        if not rows:
            return [], {}

        existing_cols = [row[0] for row in rows]
        col_meta = {
            row[0]: {"is_nullable": row[1], "data_type": row[2]} for row in rows
        }
        return existing_cols, col_meta

    def _build_allowed_set(self, table: str, columns: list[str]) -> set[str]:
        allowed_set: set[str] = set()
        for col in columns:
            if not self._valid_ident(col):
                raise ValueError(f"Invalid column name in allowlist for {table}: {col}")
            allowed_set.add(col)
        return allowed_set

    def _create_safe_table(self, cur, src_table: str, dst_table: str) -> None:
        create_sql = (
            f"CREATE TABLE IF NOT EXISTS {dst_table} (LIKE {src_table} INCLUDING ALL);"
        )
        try:
            cur.execute(create_sql)
        except Exception as exc:
            raise RuntimeError(f"Failed to create table {dst_table}: {exc}")

    def _build_select_expressions(
        self,
        table_name: str,
        existing_cols: list[str],
        allowed_set: set[str],
        col_meta: dict[str, dict[str, str]],
    ) -> tuple[list[str], str]:
        select_exprs: list[str] = []
        for col in existing_cols:
            if col in allowed_set:
                select_exprs.append(f'"{col}"')
            else:
                expr = self._fake_expression(table_name, col, col_meta[col])
                select_exprs.append(f'{expr} AS "{col}"')
        quoted_all_cols = ", ".join(f'"{c}"' for c in existing_cols)
        return select_exprs, quoted_all_cols

    def _create_safe_schema_and_copy(self, allowlist: dict[str, list[str]]):
        with connection.cursor() as cur:
            cur.execute(f"DROP SCHEMA IF EXISTS {TEMP_SCHEMA} CASCADE;")
            cur.execute(f"CREATE SCHEMA {TEMP_SCHEMA};")
            cur.execute(
                f"COMMENT ON SCHEMA {TEMP_SCHEMA} IS %s;",
                (
                    "Temporary scrubbed copy of jobserver; used by dump_sanitised_db and dropped after the job finishes.",
                ),
            )

            for table, columns in allowlist.items():
                if not columns:
                    continue

                schema_name, table_name = self._normalize_table_name(table)
                existing_cols, col_meta = self._get_column_metadata(
                    cur, schema_name, table_name
                )
                if not existing_cols:
                    continue

                allowed_set = self._build_allowed_set(table, columns)
                original_table = f'"{schema_name}"."{table_name}"'
                temp_table = f'"{TEMP_SCHEMA}"."{table_name}"'

                self._create_safe_table(cur, original_table, temp_table)

                select_exprs, quoted_all_cols = self._build_select_expressions(
                    table_name, existing_cols, allowed_set, col_meta
                )

                insert_sql = (
                    f"INSERT INTO {temp_table} ({quoted_all_cols}) "
                    f"SELECT {', '.join(select_exprs)} FROM {original_table};"
                )
                cur.execute(insert_sql)

    def _drop_temp_schema(self):
        with connection.cursor() as cur:
            cur.execute(f"DROP SCHEMA IF EXISTS {TEMP_SCHEMA} CASCADE;")

    def _run_pg_dump_for_schema(self, outfile: str, schema: str, db: dict):
        conn_uri = f"postgresql://{db['USER']}@{db['HOST']}:{db['PORT']}/{db['NAME']}"
        env = os.environ.copy()
        if db.get("PASSWORD"):
            env["PGPASSWORD"] = db["PASSWORD"]

        cmd = [
            "pg_dump",
            "--format=c",
            "--no-acl",
            "--no-owner",
            f"--file={outfile}",
            f"--schema={schema}",
            conn_uri,
        ]
        res = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(
                f"pg_dump failed: returncode={res.returncode}; stderr={res.stderr}"
            )

    def _run_pg_dump_schema_only(self, outfile: str, db: dict):
        conn_uri = f"postgresql://{db['USER']}@{db['HOST']}:{db['PORT']}/{db['NAME']}"
        env = os.environ.copy()
        if db.get("PASSWORD"):
            env["PGPASSWORD"] = db["PASSWORD"]

        cmd = [
            "pg_dump",
            "--format=c",
            "--no-acl",
            "--no-owner",
            "--schema-only",
            f"--file={outfile}",
            conn_uri,
        ]
        res = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(
                f"pg_dump (schema-only) failed: returncode={res.returncode}; stderr={res.stderr}"
            )
