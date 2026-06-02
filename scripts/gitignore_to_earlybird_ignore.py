#!/usr/bin/env python3
"""Convert .gitignore patterns to an Earlybird-compatible ignore file."""

from __future__ import annotations

import argparse
from pathlib import Path


COMMON_HIDDEN_DIRS = {
    ".venv",
    ".idea",
    ".ipynb_checkpoints",
    ".pytest_cache",
    ".playwright-browsers",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    ".git",
}


def normalize_gitignore_line(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    # Earlybird ignore patterns do not support gitignore un-ignore semantics.
    if stripped.startswith("!"):
        return None

    stripped = stripped.replace("\\", "/")
    if stripped.startswith("./"):
        stripped = stripped[2:]
    return stripped


def normalize_extra_line(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    return stripped.replace("\\", "/")


def is_directory_pattern(pattern: str, root: Path) -> bool:
    candidate = pattern
    if candidate.endswith("/*"):
        return True
    if candidate.endswith("/"):
        return True

    candidate = candidate.lstrip("/")
    if candidate.startswith("**/"):
        candidate = candidate[3:]

    wildcard = any(ch in candidate for ch in "*?[]")
    base_name = candidate.rsplit("/", maxsplit=1)[-1]

    if base_name in COMMON_HIDDEN_DIRS:
        return True
    if not wildcard and (root / candidate).is_dir():
        return True
    if not wildcard and "." not in base_name:
        return True

    return False


def to_earlybird_pattern(pattern: str, root: Path) -> str:
    candidate = pattern.lstrip("/")
    is_dir = is_directory_pattern(candidate, root)

    if is_dir:
        if candidate.endswith("/*"):
            candidate = candidate[:-2]
        candidate = candidate.rstrip("/")
        if candidate.startswith("**/"):
            candidate = candidate[3:]
        return f"**/{candidate}/**"

    if candidate.startswith("**/"):
        return candidate
    if "/" in candidate:
        return f"**/{candidate}"
    return candidate


def convert_gitignore_to_earlybird(
    input_path: Path,
    output_path: Path,
    extra_paths: list[Path],
) -> None:
    root = input_path.parent.resolve()
    converted: list[str] = []
    seen: set[str] = set()

    def add_pattern(pattern: str) -> None:
        if pattern in seen:
            return
        converted.append(pattern)
        seen.add(pattern)

    for line in input_path.read_text(encoding="utf-8").splitlines():
        maybe_pattern = normalize_gitignore_line(line)
        if maybe_pattern is None:
            continue

        converted_pattern = to_earlybird_pattern(maybe_pattern, root)
        add_pattern(converted_pattern)

    for extra_path in extra_paths:
        if not extra_path.exists():
            continue
        for line in extra_path.read_text(encoding="utf-8").splitlines():
            maybe_pattern = normalize_extra_line(line)
            if maybe_pattern is None:
                continue
            add_pattern(maybe_pattern)

    output_path.write_text("\n".join(converted) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert .gitignore patterns to Earlybird ignore patterns.",
    )
    parser.add_argument(
        "--input",
        default=".gitignore",
        type=Path,
        help="Path to source gitignore file (default: .gitignore).",
    )
    parser.add_argument(
        "--output",
        default=".ge_ignore",
        type=Path,
        help="Path to output Earlybird ignore file (default: .ge_ignore).",
    )
    parser.add_argument(
        "--extra",
        action="append",
        default=[],
        type=Path,
        help=(
            "Path to an optional file with extra Earlybird-only ignore patterns. "
            "Can be provided more than once."
        ),
    )
    args = parser.parse_args()

    convert_gitignore_to_earlybird(args.input, args.output, args.extra)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
