from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[1]


def test_requirements_are_consistent():
    # The production and development dependencies aren't intended to overlap (the dev
    # dependencies are supposed to be _extra_ packages needed for development) but
    # due to transitive dependencies the `requirements.dev.txt` file can end up
    # including packages which are also included in `requirements.prod.txt`.
    #
    # We use a `--constraint` argument in `requirements.dev.in` to ensure that whenever
    # we compile the development dependencies we stay consistent with the current
    # production dependencies. However it's still possible, by doing things in a certain
    # order, to accidentally end up with divergent versions. This can lead to confusion
    # and makes the actual installed set of packages dependent on the order in which the
    # files are read, which is bad.
    #
    # The below test ensures that wherever the two files specify the same dependency
    # they agree on the version.
    prod_packages = parse_requirements(PROJECT_ROOT / "requirements.prod.txt")
    dev_packages = parse_requirements(PROJECT_ROOT / "requirements.dev.txt")
    common_packages = prod_packages.keys() & dev_packages.keys()
    for package in common_packages:
        assert prod_packages[package] == dev_packages[package], (
            f"Inconsistent versions of '{package}' in "
            f"requirements.prod.txt and requirements.dev.txt"
        )


def parse_requirements(filename):
    packages = {}
    for line in filename.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "--")):
            continue
        package, _, version = line.partition(" ")[0].partition("==")
        packages[package] = version
    return packages
