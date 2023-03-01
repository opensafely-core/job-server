import copy
import shutil
import typing
from pathlib import Path

from attrs import define
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from . import dates, opencodelists


@define
class Codelist:
    label: str
    slug: str
    type: str  # noqa: A003

    # TODO: what are these again?
    path: str | None = None
    description: str | None = None


@define
class Analysis:
    """
    Encapsulate all the data for an analysis to pass between layers

    We expect to need a different object of this sort for each different analysis,
    to capture all the details for a given analysis.
    """

    codelist_1: Codelist
    codelist_2: Codelist | None
    created_by: str
    demographics: str
    filter_population: str
    repo: str
    time_scale: str
    time_value: str
    title: str
    id: str | None = None  # noqa: A003
    frequency: str = "monthly"
    time_event: str = "before"
    start_date: str = dates.START_DATE
    end_date: str = dates.END_DATE


@define
class AnalysisTemplate:
    """Handle rendering teh templated analysis code.

    - directory: the dir containing the source template files
    - codelists: the keys in form_data of any codelists that will need fetchin
                 as part of the rendering
    """

    directory: Path
    codelist_keys: list
    codelist_api: typing.Callable = opencodelists._get_opencodelists_api

    EXCLUDES = ["__pycache__", "metadata"]

    @property
    def environment(self):
        return Environment(
            loader=FileSystemLoader(str(self.directory)), undefined=StrictUndefined
        )

    def write_codelist(self, output_dir, key, slug):
        path = output_dir / "codelists" / f"{key}.csv"

        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        api = self.codelist_api()
        codelist = api.get_codelist(slug)
        path.write_text(codelist)
        return path

    def _render_to(self, output_dir, context, src_dir):
        """Recursively walk the src tree, and copy/render files across to the output_dir."""

        for src in src_dir.iterdir():
            if src.name in self.EXCLUDES or src.name.startswith("."):
                continue

            if src.is_dir():
                output_subdir = output_dir / src.name
                self._render_to(output_subdir, context, src)
            else:
                dst = output_dir / src.name
                if not dst.parent.exists():
                    dst.parent.mkdir()

                if src.suffix in [".tmpl", ".j2"]:
                    dst = output_dir / src.stem
                    relative_template_path = src.relative_to(self.directory)
                    template = self.environment.get_template(
                        str(relative_template_path)
                    )
                    content = template.render(**context)
                    dst.write_text(content)
                else:
                    shutil.copyfile(src, dst)

    def render(self, output_dir, form_data):
        """Render the templated code to output_dir using form_data as context."""
        context = copy.deepcopy(form_data)

        for codelist_key in self.codelist_keys:
            codelist = context[codelist_key]
            assert "slug" in codelist
            path = self.write_codelist(output_dir, codelist_key, codelist["slug"])

            # add path to context
            codelist["path"] = str(path.relative_to(output_dir))

        self._render_to(output_dir, context, self.directory)
