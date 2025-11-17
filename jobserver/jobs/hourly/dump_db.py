# dump_db.py
import json
import os
import pathlib
import subprocess
import sys
import tempfile

from django.conf import settings
from django.db import connection
from django_extensions.management.jobs import HourlyJob
from sentry_sdk.crons.decorator import monitor

from services.sentry import monitor_config


# Temporary schema to hold safe copies
TEMP_SCHEMA = "safe_dump"
# OUTPUT_PATH = pathlib.Path("/storage/jobserver.dump")
OUTPUT_PATH = pathlib.Path("./jobserver.dump")
# ALLOWLIST_ENV = "DUMP_DB_ALLOWLIST_FILE"
ALLOWLIST_SETTING = "DUMP_DB_ALLOWLIST_FILE"


class Job(HourlyJob):
    help = "Dump an allowlisted subset of the DB suitable for local dev (missing cols -> NULL)"

    @monitor(monitor_slug="dump_db", monitor_config=monitor_config("0 * * * *"))
    def execute(self):
        db = settings.DATABASES["default"]

        # allowlist_path = os.environ.get(ALLOWLIST_ENV) or getattr(settings, ALLOWLIST_SETTING, None)
        allowlist_path = pathlib.Path(__file__).with_name("allow_list.json")
        allowlist = self._load_allowlist(allowlist_path)
        # print(f"Loaded allowlist for {len(allowlist)} tables")

        # If allowlist empty -> conservative schema-only dump
        dump_rows = bool(allowlist)
        # print("dump_rows:", dump_rows)

        # Ensure output directory exists
        out_dir = OUTPUT_PATH.parent
        if not out_dir.is_dir():
            print(f"Unknown output directory: {out_dir}", file=sys.stderr)
            sys.exit(1)

        # Temporary output file (atomic replace later)
        with tempfile.NamedTemporaryFile(
            prefix="jobserver-", dir=str(out_dir), delete=False
        ) as tmp:
            tmp_name = tmp.name
            # print(tmp_name)

        try:
            if dump_rows:
                self._create_safe_schema_and_copy(allowlist)
                try:
                    self._run_pg_dump_for_schema(tmp_name, TEMP_SCHEMA, db)
                finally:
                    # Always drop the temp schema
                    self._drop_temp_schema()
            else:
                # No allowlist -> schema-only dump (no row data)
                self._run_pg_dump_schema_only(tmp_name, db)

            os.chmod(tmp_name, 0o600)
            os.replace(tmp_name, OUTPUT_PATH)
        except Exception:
            # Cleanup on error
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
            clean: dict[str, list[str]] = {}
            for table, cols in data.items():
                if isinstance(cols, list) and cols:
                    clean[str(table)] = [str(c) for c in cols]
            return clean
        except FileNotFoundError:
            print(
                f"Allowlist file not found at {path}; proceeding with schema-only dump",
                file=sys.stderr,
            )
            return {}
        except Exception as exc:
            print(f"Error loading allowlist file {path}: {exc}", file=sys.stderr)
            return {}

    def _create_safe_schema_and_copy(self, allowlist: dict[str, list[str]]):
        """Create TEMP_SCHEMA and copy data while preserving full table schema.

        - TEMP_SCHEMA tables are created using LIKE source_table INCLUDING ALL, so all
          columns and constraints are present.
        - Columns listed in the allowlist are populated from the source.
        - Columns not listed in the allowlist remain in the schema but are populated as NULL.
        """
        with connection.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {TEMP_SCHEMA};")

            for table_name, columns in allowlist.items():
                if not columns:
                    continue

                # Support "schema.table" or just "table" (default schema public)
                if "." in table_name:
                    schema_name, short_table = table_name.split(".", 1)
                else:
                    schema_name = "public"
                    short_table = table_name

                # Basic identifier validation
                def _valid_ident(x: str) -> bool:
                    return (
                        bool(x)
                        and (x.replace("_", "").isalnum())
                        and (not x[0].isdigit())
                    )

                if not _valid_ident(short_table) or not _valid_ident(schema_name):
                    raise ValueError(f"Invalid table name in allowlist: {table_name}")

                # Get existing columns for the source table
                cur.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s;
                    """,
                    [schema_name, short_table],
                )
                existing_cols = [row[0] for row in cur.fetchall()]

                if not existing_cols:
                    continue

                # Validate allowlisted columns and build lookup set
                allowed_set: set[str] = set()
                for col in columns:
                    if not _valid_ident(col):
                        raise ValueError(
                            f"Invalid column name in allowlist for {table_name}: {col}"
                        )
                    allowed_set.add(col)

                # Qualified names
                src_table_q = f'"{schema_name}"."{short_table}"'
                dst_table_q = f'"{TEMP_SCHEMA}"."{short_table}"'

                # Create table in TEMP_SCHEMA with full schema of source table
                create_sql = (
                    f"CREATE TABLE IF NOT EXISTS {dst_table_q} "
                    f"(LIKE {src_table_q} INCLUDING ALL);"
                )

                try:
                    cur.execute(create_sql)
                except Exception as exc:
                    raise RuntimeError(f"Failed to create table {dst_table_q}: {exc}")

                # Build SELECT list: allowed columns as real values, others as NULL
                select_exprs: list[str] = []
                for col in existing_cols:
                    if col in allowed_set:
                        select_exprs.append(f'"{col}"')
                    else:
                        select_exprs.append(f'NULL AS "{col}"')

                select_list = ", ".join(select_exprs)
                quoted_all_cols = ", ".join(f'"{c}"' for c in existing_cols)
                insert_sql = (
                    f"INSERT INTO {dst_table_q} ({quoted_all_cols}) "
                    f"SELECT {select_list} FROM {src_table_q};"
                )
                try:
                    cur.execute(insert_sql)
                except Exception as exc:
                    raise RuntimeError(f"Failed to populate table {dst_table_q}: {exc}")

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
