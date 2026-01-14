# 34. Switch Job Server dependency management from pip and pip-tools to uv

Date: 2026-01-13

## Status

Accepted

## Context

Historically, Job Server has used [`pip`](https://packaging.python.org/en/latest/key_projects/#pip), [`pip-tools`](https://packaging.python.org/en/latest/key_projects/#pip-tools) (`pip-compile`), and `requirements.*.in` / `requirements.*.txt` files to manage Python dependencies, and `venv` to create the virtual environments into which those dependencies are installed.

[`uv`](https://docs.astral.sh/uv/) is a single tool that can replace `pip`, `pip-tools`, and [`venv`](https://docs.python.org/3/library/venv.html#module-venv). Other OpenSAFELY repositories, including [`airlock`](https://github.com/opensafely-core/airlock), [`ehrql`](https://github.com/opensafely-core/ehrql), [`job-runner`](https://github.com/opensafely-core/job-runner), and [`repo-template`](https://github.com/opensafely-core/repo-template), have already successfully migrated to `uv` at the time of writing this ADR. These migrations began in [September 2025](https://github.com/opensafely-core/repo-template/pull/306), and an [example checklist](https://github.com/opensafely-core/airlock/issues/1008) for a migration process has been documented as part of this work.

While the existing `pip`-based workflow is well understood, `uv` provides a modern alternative with several advantages:

- **Performance**: Dependency resolution and installation are significantly [faster](https://github.com/astral-sh/uv/blob/main/BENCHMARKS.md).
- **File maintenance**: Dependency management moves from four files  (`requirements.*.in` / `.txt`) to two (`pyproject.toml`, `uv.lock`), while still allowing production (prod) and development (dev) dependencies to be declared separately in `pyproject.toml`.
- **Tooling surface**: The need for `pip-tools` is removed.
- **Policy alignment**: A dependency cool-down period can be consistently applied using `uv`’s [timestamp cut-off mechanism](https://docs.astral.sh/uv/reference/settings/#pip_exclude-newer), aligning with the Bennett Institute [Dependency Updates Policy](https://docs.google.com/document/d/1s1zQ_312d7Fy89j5H8AHJSCeLK-rLBBls3XIQJGP9fw/edit?usp=sharing).
- **Environment management**: `uv` automatically creates and manages [virtual environments](https://docs.astral.sh/uv/concepts/projects/layout/#the-project-environment), removing the need for separate `python -m venv` commands.
- **Organisational alignment**: Adopting `uv` aligns Job Server’s dependency management approach with other OpenSAFELY repositories.

## Alternatives

### Continue with the existing pip / pip-tools workflow
We could have continued using `pip`, `pip-tools`, and `requirements.*.in` / `requirements.*.txt` files. This approach is well understood, but it requires maintaining multiple files, offers slower dependency resolution, and does not align with the dependency management approach now used in other OpenSAFELY repositories.

### Poetry
[Poetry](https://python-poetry.org/) is a popular alternative for Python dependency management that also uses `pyproject.toml` and a lockfile. Similarly to `uv`, Poetry can also handle multiple functions in one tool (for example, dependency management, virtual environment creation), and has [several advantages over pip](https://betterstack.com/community/guides/scaling-python/poetry-vs-pip/#poetry-vs-pip-a-quick-comparison). However, adopting Poetry would introduce new tooling that would differ from the rest of the OpenSAFELY ecosystem, meaning developers would need to familiarise themselves with another new tool.

### Other tooling
Other tools that `uv` can replace (e.g. `virtualenv`, `pipx`, `pyenv`, `twine`)address narrower parts of the dependency management workflow and are not complete alternatives to the existing `pip` / `pip-tools`–based dependency management workflow on their own.

Given that `uv` is already in use across multiple OpenSAFELY projects and provides a single, consistent replacement for existing tooling, it was chosen over the aforementioned alternatives.

## Decision

Job Server will use `uv` for Python dependency management, replacing `pip`, `pip-compile`, and the existing `requirements.*` files.

**Specifically:**

- Job Server will adopt a phased migration approach (`pip`/`pip-compile` -> `uv pip compile` -> [`uv lock`](https://docs.astral.sh/uv/reference/cli/#uv-lock)/ [`uv sync`](https://docs.astral.sh/uv/reference/cli/#uv-sync)), which differs slightly from the approach taken by other OpenSAFELY repositories.
- All dependencies will be declared in `pyproject.toml` and constrained where required.
    - Prod dependencies will be declared in the [`project.dependencies`](https://docs.astral.sh/uv/concepts/projects/dependencies/#project-dependencies) table
    - Dev dependencies will be declared in the [`[dependency-groups]`](https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies) table, in the `dev = [...]` group.
- A single `uv.lock` file will be used to lock resolved dependencies.
- Dependency installation will be performed via `uv sync`.
- Virtual environment creation will be performed via [`uv venv`](https://docs.astral.sh/uv/reference/cli/#uv-venv).
- `justfile` recipes for dependency management will be updated to use `uv`
- The existing `requirements.dev.in`, `requirements.dev.txt`, `requirements.prod.in`, and `requirements.prod.txt` files will be removed.
- Automated dependency updates and Docker builds will use `uv`.
- Where appropriate, Job Server will follow established `uv` usage patterns from other OpenSAFELY repositories (e.g. [`repo-template`](https://github.com/opensafely-core/repo-template) and [`airlock`](https://github.com/opensafely-core/airlock)).

## Consequences

### Positive
- Dependency resolution and installation are faster both locally and in CI.
- The dependency management workflow is simplified, with fewer files and less duplication.
- Deterministic builds are enforced via `uv.lock`.
- A dependency cool-down period is consistently applied via the `just update-dependencies` recipe and the [`exclude-newer` setting](https://docs.astral.sh/uv/reference/settings/#exclude-newer) in `pyproject.toml`, aligning with the Bennett Institute [Dependency Updates Policy](https://docs.google.com/document/d/1s1zQ_312d7Fy89j5H8AHJSCeLK-rLBBls3XIQJGP9fw/edit?usp=sharing).
- Job Server’s tooling is aligned with other OpenSAFELY projects, reducing cognitive overhead for developers working across repositories.

### Neutral
- Existing workflows and documentation reflect the new approach.
- Dependabot and the update-dependencies action should both continue to work exactly the same.

### Negative
- Developers must install and become familiar with `uv`.
- Some third party tools that we use, and their associated documentation, may assume `pip`-based workflows that require translation to `uv` equivalents, adjustment of those tools to use `uv` commands, or [generation of `requirements.txt` files from `uv.lock`](https://docs.astral.sh/uv/reference/cli/#uv-export) if necessary.
