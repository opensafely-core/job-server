# Sanitised Database Dump Job

This job exists so developers can work with a production‑like dataset without exposing sensitive information. Instead of copying the raw production database, it creates a temporary schema containing only safe columns (non‑allow‑listed columns are replaced with fake values) and dumps that schema for local use.

The code lives in `jobserver/jobs/yearly/dump_sanitised_db.py` alongside its allow list (`allow_list.json`). The job currently inherits from `YearlyJob` so it only runs when triggered manually; once we are confident it is safe, we can switch it back to `DailyJob`.

## High-Level Algorithm

1. **Load configuration**
   - Read `settings.DATABASES["default"]` to connect to production.
   - Load `allow_list.json` (table → allowed columns). If it’s empty or missing, exit.
2. **Prepare output**
   - Ensure `/storage` exists, then create a temporary file there (`tmp-sanitised-jobserver-dump-*`) so we never overwrite the existing dump until the job succeeds.
3. **Scratch schema lifecycle**
   - Drop any leftover `temp_scrubbed_schema`.
   - Inside a `try/finally`, create `temp_scrubbed_schema`, add a descriptive comment, and copy each allow-listed table:
     * For each table, fetch the real column metadata from `information_schema`.
     * Validate the table/column names (to avoid SQL injection) and create a matching table in the scratch schema using `CREATE TABLE … LIKE`.
     * Build a single `INSERT … SELECT` per table. Allowed columns are copied verbatim; everything else gets a deterministic fake.
   - After copying all tables, run `pg_dump --schema=temp_scrubbed_schema` into the temp file, then drop the scratch schema in the `finally` block so nothing remains on production.
4. **Publish the dump**
   - Flush the temp file, `chmod 600`, and `shutil.copy2` it to `/storage/sanitised_jobserver.dump`. The temporary file is automatically deleted when the context manager exits.

## Allow List

`allow_list.json` is a manually curated mapping of tables to the columns we want to keep verbatim. Everything else gets faked. To build it we:

1. Dumped the production schema (`schema.sql`) and annotated each table with comments about which columns might contain sensitive data.
2. For each table, either marked it “looks good” (everything is safe) or listed the exact columns we wanted to retain. Any column omitted from the list is automatically replaced with fake values in the scratch schema.
3. Stored the final allow list under `jobserver/jobs/yearly/allow_list.json`. The integration test `tests/integration/test_dump_sanitised_db.py` checks that every table/column in the allow list still exists in the current schema so we notice if migrations drift.

When adding new columns/tables, update the allow list accordingly. If a column is sensitive but referenced by the UI, we keep it in the schema but set its values to fake data (so the schema stays intact).

## Notes & Decisions

- We are leaving the legacy `dump_db` raw-dump script untouched for now; once the sanitised job proves itself we can move `dump_db` to the yearly bucket so a full, unsanitised dump is still available on demand (via an explicit run) when a debugging emergency requires it.
- SQL safety: all dynamic identifiers are validated and interpolated via `psycopg.sql.Identifier`/`sql.SQL`. Values use parameterized queries. This protects us against accidental SQL injection in allow list entries.
- Fake expressions use `ROW_NUMBER()` so they remain unique within each table copy (no collisions with `random()`).
- Tests:
  * Unit tests cover helper functions (`tests/unit/jobserver/jobs/test_dump_sanitised_db.py`).
  * Integration tests ensure each allow-listed table/column exists and that the scrubbed schema actually contains fake values (`tests/integration/test_dump_sanitised_db.py`).
- When ready to schedule this job automatically, switch the class back to `DailyJob`, update the Sentry monitor cron string, and add a `python manage.py runjobs daily` entry in `app.json`. Until then, keep running it manually after backups and verify the sanitised dump before distributing it to developers.

## FAQs

**What happens if a column is renamed/removed or its type changes?**
The integration test (`tests/integration/test_dump_sanitised_db.py`) queries `information_schema` to ensure every table/column in `allow_list.json` still exists. If a column is missing, the test fails before deployment. If it slips through and the job hits a missing column or unknown type, `_build_select_expressions`/`_fake_expression` raises an error, so the job aborts instead of producing a partial dump. This forces us to update the allow list (and fake-expression logic) whenever the schema changes.

**What if a new column is added but not added to the allow list?**
The job treats it as “sensitive” by default: it copies the column but fills it with fake values. The dump remains structurally valid, but developers won’t see real data for that column until we explicitly add it to the allow list. This is an intentional safe default.
