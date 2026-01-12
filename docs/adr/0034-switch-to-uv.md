# 34. Switch Job Server dependency management from pip and pip-tools to uv

Date: 2026-01-12

## Status

Accepted

## Context

Historically, Job Server has used `pip`, `pip-tools` (`pip-compile`), and `requirements.*.in` / `requirements.*.txt` files to manage Python dependencies, and `venv` to create the virtual environments in which those dependencies are installed.

`uv` is a single tool that can replace `pip`, `pip-tools`, and `venv`. Other OpenSAFELY repositories, including `airlock`, `ehrql`, `job-runner` and `repo-template`, have already successfully migrated to `uv` at the time of writing this ADR.

While the existing pip-based workflow is well understood, `uv` provides a modern alternative with several advantages:

- Dependency resolution and installation are significantly [faster](https://github.com/astral-sh/uv/blob/main/BENCHMARKS.md).
- Using a single input file (`pyproject.toml`) and a single output file (`uv.lock`) reduces duplication and maintenance overhead.
- A dependency cool-down period can be consistently applied using `uv`’s [timestamp cut-off mechanism](https://docs.astral.sh/uv/reference/settings/#pip_exclude-newer), aligning with the Bennett Institute Dependency Updates Policy.
- `uv` automatically creates and manages [virtual environments](https://docs.astral.sh/uv/concepts/projects/layout/#the-project-environment), removing the need for separate `python -m venv` commands.
- The dependency management approach aligns with other OpenSAFELY repositories, reducing divergence across projects.

## Decision

Job Server will use `uv` for Python dependency management, replacing `pip`, `pip-compile`, and the existing `requirements.*` files.

**Specifically:**

- All dependencies are declared in `pyproject.toml` and constrained where required.
- A single `uv.lock` file is used to lock resolved dependencies.
- Dependency installation is performed via `uv sync`.
- Virtual environment creation is performed via `uv venv`.
- The existing `requirements.dev.in`, `requirements.dev.txt`, `requirements.prod.in`, and `requirements.prod.txt` files are removed.
- Automated dependency updates and Docker builds use `uv`.
- Where appropriate, Job Server follows established `uv` usage patterns from other OpenSAFELY repositories (e.g. [`repo-template`](https://github.com/opensafely-core/repo-template) and [`airlock`](https://github.com/opensafely-core/airlock)).

## Consequences

- Dependency resolution and installation are faster both locally and in CI.
- The dependency management workflow is simplified, with fewer files and less duplication.
- Deterministic builds are enforced via `uv.lock`.
- A dependency cool-down period is consistently applied, aligning with the Bennett Institute [Dependency Updates Policy](https://docs.google.com/document/d/1s1zQ_312d7Fy89j5H8AHJSCeLK-rLBBls3XIQJGP9fw/edit?usp=sharing).
- Job Server’s tooling is aligned with other OpenSAFELY projects, reducing cognitive overhead for developers working across repositories.
- Developers must install and become familiar with `uv`.
- Existing workflows and documentation require maintenance to reflect the new approach.
- Some ecosystem tools and documentation assume `pip`-based workflows and may require translation to `uv` equivalents.
