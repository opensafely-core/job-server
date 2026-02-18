#!/usr/bin/env python
"""
Print the columns that are excluded (i.e., faked) by dump_sanitised_db.

Usage:
  1. Create a database and restore the latest production database dump into it.

  2. Run the helper SQL query against your database to list all columns:
     psql "$PROD_DATABASE_URL" -tAc "
         SELECT table_name, column_name
         FROM information_schema.columns
         WHERE table_schema = 'public';
     " > all_columns.txt

  3. Then run this script, pointing it at that column list:
     python scripts/get_excluded_columns.py all_columns.txt
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


ALLOW_LIST_PATH = Path("jobserver/jobs/yearly/allow_list.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "column_file",
        type=Path,
        help="Path to a text file containing 'table|column' lines.",
    )
    args = parser.parse_args()

    with ALLOW_LIST_PATH.open(encoding="utf-8") as f:
        allow = json.load(f)

    allowed = {table: set(cols) for table, cols in allow.items()}
    excluded: dict[str, list[str]] = defaultdict(list)

    with args.column_file.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            table, column = line.split("|", 1)
            allowed_cols = allowed.get(table, set())
            if not allowed_cols or column not in allowed_cols:
                excluded[table].append(column)

    output_path = Path("excluded_columns.txt")
    with output_path.open("w", encoding="utf-8") as out:
        for table in sorted(excluded):
            cols = ", ".join(sorted(excluded[table]))
            out.write(f"{table}: {cols}\n")
    print(f"Wrote excluded column list to {output_path.resolve()}")


if __name__ == "__main__":
    main()
