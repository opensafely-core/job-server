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
OUTPUT_PATH = pathlib.Path("/storage/jobserver.dump")
# OUTPUT_PATH = pathlib.Path("./jobserver_scrubbed.dump") #for testing


class Job(HourlyJob):
    help = "Dump a safe copy of the DB with non-allowlisted columns replaced by fake values"

    @monitor(monitor_slug="dump_db", monitor_config=monitor_config("0 19 * * *"))
    def execute(self):
        db = settings.DATABASES["default"]
        allowlist_path = pathlib.Path(__file__).with_name("allow_list.json")
        allowlist = self._load_allowlist(allowlist_path)
        allowlist_exists = bool(allowlist)
        out_dir = OUTPUT_PATH.parent

        if not out_dir.is_dir():
            print(f"Unknown output directory: {out_dir}", file=sys.stderr)
            sys.exit(1)

        with tempfile.NamedTemporaryFile(
            prefix="jobserver-", dir=str(out_dir), delete=False
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
            return f"'fake_{table}_{col}_' || id::text"

        if "boolean" in dtype:
            return "false"

        if "integer" in dtype or "bigint" in dtype or "smallint" in dtype:
            return "0"

        if "timestamp" in dtype or "date" in dtype:
            return "now()"

        if "json" in dtype:
            return "'{}'::jsonb"

        return "NULL"

    def _valid_ident(x: str) -> bool:
        return bool(x) and (x.replace("_", "").isalnum()) and (not x[0].isdigit())

    def _create_safe_schema_and_copy(self, allowlist: dict[str, list[str]]):
        with connection.cursor() as cur:
            cur.execute(f"DROP SCHEMA IF EXISTS {TEMP_SCHEMA} CASCADE;")
            cur.execute(f"CREATE SCHEMA {TEMP_SCHEMA};")

            for table_name, columns in allowlist.items():
                if not columns:
                    continue

                # Table name could be like "schema.table" or just "table"
                if "." in table_name:
                    schema_name, short_table = table_name.split(".", 1)
                else:
                    schema_name = "public"
                    short_table = table_name

                if not self._valid_ident(short_table) or not self._valid_ident(
                    schema_name
                ):
                    raise ValueError(f"Invalid table name in allowlist: {table_name}")

                cur.execute(
                    """
                    SELECT column_name, is_nullable, data_type
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s;
                    """,
                    [schema_name, short_table],
                )
                rows = cur.fetchall()
                if not rows:
                    continue

                existing_cols = [row[0] for row in rows]
                col_meta = {
                    row[0]: {"is_nullable": row[1], "data_type": row[2]} for row in rows
                }

                # validate allowlisted columns and build lookup set
                allowed_set: set[str] = set()
                for col in columns:
                    if not self._valid_ident(col):
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

                select_exprs: list[str] = []
                for col in existing_cols:
                    meta = col_meta[col]

                    if col in allowed_set:
                        select_exprs.append(f'"{col}"')
                    else:
                        expr = self._fake_expression(short_table, col, meta)
                        select_exprs.append(f'{expr} AS "{col}"')

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
