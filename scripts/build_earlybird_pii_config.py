#!/usr/bin/env python3
"""Build a local Earlybird config directory containing only PII rules."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

import yaml


CATEGORY_RE = re.compile(r"^Category:\s*['\"]?([^'\"]+)['\"]?\s*$", re.IGNORECASE)
CODE_RE = re.compile(r"^-\s*Code:\s*(\d+)\s*$")


def parse_ignore_label_specs(ignore_labels_file: Path) -> list[str]:
    if not ignore_labels_file.exists():
        return []

    specs: list[str] = []
    for raw_line in ignore_labels_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        specs.append(line)

    return specs


def load_label_code_map(labels_dir: Path) -> dict[str, set[int]]:
    label_code_map: dict[str, set[int]] = {}

    for labels_file in sorted(labels_dir.glob("*.yaml")):
        data = yaml.safe_load(labels_file.read_text(encoding="utf-8")) or {}
        for entry in data.get("labels", []):
            if not isinstance(entry, dict):
                continue

            label = str(entry.get("label", "")).strip().lower()
            if not label:
                continue

            codes: set[int] = set()
            for code in entry.get("codes", []):
                try:
                    codes.add(int(code))
                except (TypeError, ValueError):
                    continue

            if label in label_code_map:
                label_code_map[label].update(codes)
            else:
                label_code_map[label] = codes

    return label_code_map


def resolve_ignored_codes(
    ignore_specs: list[str],
    label_code_map: dict[str, set[int]],
) -> set[int]:
    ignored_codes: set[int] = set()

    for spec in ignore_specs:
        labels = [part.strip().lower() for part in spec.split("/") if part.strip()]
        if not labels:
            continue

        code_sets: list[set[int]] = []
        for label in labels:
            codes = label_code_map.get(label, set())
            if not codes:
                code_sets = []
                break
            code_sets.append(codes)

        if not code_sets:
            continue

        shared_codes = set.intersection(*code_sets)
        ignored_codes.update(shared_codes)

    return ignored_codes


def extract_rule_category(rule_block: list[str]) -> str | None:
    for line in rule_block:
        match = CATEGORY_RE.match(line.strip())
        if match:
            return match.group(1).strip().lower()
    return None


def extract_rule_code(rule_block: list[str]) -> int | None:
    for line in rule_block:
        match = CODE_RE.match(line.strip())
        if match:
            return int(match.group(1))
    return None


def filter_rule_file(rule_file: Path, ignored_codes: set[int]) -> None:
    lines = rule_file.read_text(encoding="utf-8").splitlines(keepends=True)
    rules_idx = next(
        (i for i, line in enumerate(lines) if line.strip() == "rules:"), None
    )

    if rules_idx is None:
        return

    header = lines[: rules_idx + 1]
    body = lines[rules_idx + 1 :]

    blocks: list[list[str]] = []
    current_block: list[str] = []
    outside_block_lines: list[str] = []

    for line in body:
        if re.match(r"^\s*-\s", line):
            if current_block:
                blocks.append(current_block)
            current_block = [line]
            continue

        if current_block:
            current_block.append(line)
        else:
            outside_block_lines.append(line)

    if current_block:
        blocks.append(current_block)

    pii_blocks: list[list[str]] = []
    for block in blocks:
        category = extract_rule_category(block)
        if category != "pii":
            continue

        code = extract_rule_code(block)
        if code is not None and code in ignored_codes:
            continue

        pii_blocks.append(block)

    output_lines = header + outside_block_lines
    for block in pii_blocks:
        output_lines.extend(block)

    if output_lines and not output_lines[-1].endswith("\n"):
        output_lines[-1] += "\n"

    rule_file.write_text("".join(output_lines), encoding="utf-8")


def build_pii_config(source: Path, dest: Path, ignore_specs: list[str]) -> set[int]:
    if not source.exists():
        raise FileNotFoundError(f"Source config directory not found: {source}")

    label_code_map = load_label_code_map(source / "labels")
    ignored_codes = resolve_ignored_codes(ignore_specs, label_code_map)

    if dest.exists():
        shutil.rmtree(dest)

    shutil.copytree(source, dest)

    rules_dir = dest / "rules"
    for rule_file in sorted(rules_dir.glob("*.yaml")):
        filter_rule_file(rule_file, ignored_codes)

    return ignored_codes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an Earlybird config dir with only Category: pii rules.",
    )
    parser.add_argument(
        "--source",
        default=str(Path.home() / ".go-earlybird"),
        type=Path,
        help="Source Earlybird config directory (default: ~/.go-earlybird).",
    )
    parser.add_argument(
        "--dest",
        default=".earlybird-pii-config",
        type=Path,
        help="Destination directory for generated PII-only config.",
    )
    parser.add_argument(
        "--ignore-labels-file",
        default=".earlybird_ignore_labels",
        type=Path,
        help="Optional file of labels or slash-separated label groups to suppress.",
    )
    parser.add_argument(
        "--ignore-label",
        action="append",
        default=[],
        help="Label or slash-separated label group to suppress (can be repeated).",
    )
    args = parser.parse_args()

    ignore_specs = parse_ignore_label_specs(args.ignore_labels_file) + args.ignore_label
    ignored_codes = build_pii_config(args.source, args.dest, ignore_specs)
    print(
        f"Wrote PII-only Earlybird config to {args.dest}"
        + (f" (ignored {len(ignored_codes)} code(s))" if ignored_codes else "")
    )


if __name__ == "__main__":
    main()
