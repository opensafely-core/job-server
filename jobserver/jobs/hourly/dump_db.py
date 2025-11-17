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
        """
        Create TEMP_SCHEMA and copy allowlisted columns.
        For allowlisted columns missing on the source table, emit plain NULL AS "col".
        To avoid type inference errors when all columns are NULL, if none of the requested columns
        exist in the source table we create the destination table with TEXT columns explicitly.
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
                existing_cols = {row[0] for row in cur.fetchall()}

                # Build select expressions: real column if exists, else plain NULL AS "col"
                select_exprs = []
                safe_col_names = []
                real_column_present = False

                for col in columns:
                    if not _valid_ident(col):
                        raise ValueError(
                            f"Invalid column name in allowlist for {table_name}: {col}"
                        )
                    safe_col_names.append(col)

                    if col in existing_cols:
                        # Use the real column (quoted)
                        select_exprs.append(f'"{col}"')
                        real_column_present = True
                    else:
                        # Missing column -> plain NULL (no cast)
                        select_exprs.append(f'NULL AS "{col}"')

                # Qualified names
                src_table_q = f'"{schema_name}"."{short_table}"'
                dst_table_q = f'"{TEMP_SCHEMA}"."{short_table}"'

                # Normalise select expressions: ensure quoted columns have explicit alias to guarantee column names
                normalized_selects = []
                for expr in select_exprs:
                    expr_strip = expr.strip()
                    if expr_strip.startswith('"') and expr_strip.endswith('"'):
                        # plain column name -> add alias
                        colname = expr_strip.strip('"')
                        normalized_selects.append(f'{expr_strip} AS "{colname}"')
                    else:
                        # expression already has alias form like NULL AS "col"
                        normalized_selects.append(expr)

                select_list = ", ".join(normalized_selects)

                # CREATE TABLE step:
                if real_column_present:
                    # Use CREATE TABLE AS SELECT ... WITH NO DATA to preserve real types for existing columns.
                    create_sql = f"CREATE TABLE IF NOT EXISTS {dst_table_q} AS SELECT {select_list} FROM {src_table_q} WITH NO DATA;"
                else:
                    # No real columns present in source table for these allowlisted columns:
                    # create table with explicit TEXT columns so plain NULL can be inserted.
                    col_defs = ", ".join(f'"{c}" text' for c in safe_col_names)
                    create_sql = (
                        f"CREATE TABLE IF NOT EXISTS {dst_table_q} ({col_defs});"
                    )

                try:
                    cur.execute(create_sql)
                except Exception as exc:
                    raise RuntimeError(f"Failed to create table {dst_table_q}: {exc}")

                # Insert rows: use plain NULL expressions where appropriate
                # Build insert column list using safe_col_names
                quoted_cols = ", ".join(f'"{c}"' for c in safe_col_names)
                insert_select_list = ", ".join(normalized_selects)
                insert_sql = f"INSERT INTO {dst_table_q} ({quoted_cols}) SELECT {insert_select_list} FROM {src_table_q};"
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
