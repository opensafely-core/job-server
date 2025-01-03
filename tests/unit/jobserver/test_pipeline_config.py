import textwrap

import pytest
from furl import furl
from pipeline.models import Pipeline

from jobserver.pipeline_config import (
    ActionPermissionError,
    check_cohortextractor_permission,
    check_sqlrunner_permission,
    get_actions,
    get_codelists_status,
    get_database_actions,
    get_project,
    link_run_scripts,
    map_run_scripts_to_links,
    render_definition,
)

from ...factories import ProjectFactory
from ...fakes import FakeGitHubAPI, FakeOpenCodelistsAPI


dummy_project = {
    "version": "3.0",
    "expectations": {"population_size": 1000},
    "actions": {
        "generate_study_population": {
            "run": "cohortextractor:latest generate_cohort --study-definition study_definition",
            "outputs": {"highly_sensitive": {"cohort": "output/input.csv"}},
        },
        "run_model": {
            "run": "stata-mp:latest analysis/model.do",
            "needs": ["generate_study_population"],
            "outputs": {"moderately_sensitive": {"log": "logs/model.log"}},
        },
    },
}


def link_func(path):
    f = furl("example.com")
    f.path /= path
    return f.url


def test_check_cohortextractor_permission():
    config = Pipeline.build(
        **{
            "version": 3,
            "expectations": {"population_size": 1000},
            "actions": {
                "generate_study_population": {
                    "run": "cohortextractor:latest generate_cohort",
                    "outputs": {"highly_sensitive": {"cohort": "some/path.csv"}},
                },
            },
        }
    )

    # The internal project has permission
    check_cohortextractor_permission(ProjectFactory(id=28), config)

    # Project 2 has permission
    check_cohortextractor_permission(ProjectFactory(id=101, number=2), config)

    with pytest.raises(ActionPermissionError):
        # Project 1 doesn't have permission
        check_cohortextractor_permission(ProjectFactory(id=102, number=1), config)


def test_check_cohortextractor_permission_no_cohort_extractor_actions():
    config = Pipeline.build(
        **{
            "version": 3,
            "expectations": {"population_size": 1000},
            "actions": {
                "generate_study_population": {
                    "run": "ehrql:v1 generate-dataset --output some/path.csv",
                    "outputs": {"highly_sensitive": {"dataset": "some/path.csv"}},
                },
            },
        }
    )

    # Project 1 doesn't have permission to run cohort-extractor, but there are no
    # cohort-extractor actions in the pipeline, so no error will be raised
    check_cohortextractor_permission(ProjectFactory(id=101, number=1), config)


def test_check_sqlrunner_permission():
    config = Pipeline.build(
        **{
            "version": 3,
            "expectations": {"population_size": 1000},
            "actions": {
                "query": {
                    "run": "sqlrunner:latest",
                    "outputs": {"highly_sensitive": {"output": "some/path.csv"}},
                },
            },
        }
    )

    # The internal project has permission
    check_sqlrunner_permission(ProjectFactory(id=28), config)

    with pytest.raises(ActionPermissionError):
        # Project 1 doesn't have permission
        check_sqlrunner_permission(ProjectFactory(id=102, number=1), config)


def test_check_sqlrunner_permission_no_sqlrunner_actions():
    config = Pipeline.build(
        **{
            "version": 3,
            "expectations": {"population_size": 1000},
            "actions": {
                "generate_study_population": {
                    "run": "ehrql:v1 generate-dataset --output some/path.csv",
                    "outputs": {"highly_sensitive": {"dataset": "some/path.csv"}},
                },
            },
        }
    )

    # Project 1 doesn't have permission to run SQL Runner, but there are no SQL Runner,
    # so no error will be raised
    check_sqlrunner_permission(ProjectFactory(id=101, number=1), config)


def test_get_actions_missing_needs():
    dummy = Pipeline.build(
        **{
            "version": 3,
            "expectations": {"population_size": 1000},
            "actions": {
                "frobnicate": {
                    "run": "test:latest",
                    "outputs": {"highly_sensitive": {"cohort": "some/path.csv"}},
                },
            },
        }
    )
    output = list(get_actions(dummy))

    expected = [
        {"name": "frobnicate", "needs": []},
        {"name": "run_all", "needs": ["frobnicate"]},
    ]
    assert output == expected


def test_get_actions_no_run_all():
    dummy = Pipeline.build(
        **{
            "version": 3,
            "expectations": {"population_size": 1000},
            "actions": {
                "frobnicate": {
                    "run": "test1:latest",
                    "outputs": {"highly_sensitive": {"cohort": "some/path1.csv"}},
                },
                "run_all": {
                    "needs": ["frobnicate"],
                    "run": "test2:latest",
                    "outputs": {"highly_sensitive": {"cohort": "some/path2.csv"}},
                },
            },
        }
    )

    output = list(get_actions(dummy))

    expected = [
        {"name": "frobnicate", "needs": []},
        {"name": "run_all", "needs": ["frobnicate"]},
    ]
    assert output == expected


def test_get_actions_success():
    content = Pipeline.build(
        **{
            "version": 3,
            "expectations": {"population_size": 1000},
            "actions": {
                "frobnicate": {
                    "run": "test:latest",
                    "outputs": {"highly_sensitive": {"cohort": "some/path.csv"}},
                },
            },
        }
    )
    output = list(get_actions(content))

    expected = [
        {"name": "frobnicate", "needs": []},
        {"name": "run_all", "needs": ["frobnicate"]},
    ]
    assert output == expected


def test_get_project_no_branch():
    class BrokenGitHubAPI:
        def get_branch(self, *args):
            return None

        def get_file(self, *args):
            pass

    with pytest.raises(Exception, match="Missing branch: 'main'"):
        get_project("opensafely", "test", "main", get_github_api=BrokenGitHubAPI)


def test_get_project_no_project_yaml():
    class BrokenGitHubAPI:
        def get_branch(self, *args):
            return True

        def get_file(self, *args):
            pass

    with pytest.raises(Exception, match="Could not find project.yaml"):
        get_project("opensafely", "test", "main", get_github_api=BrokenGitHubAPI)


def test_get_project_success():
    pipeline_config = get_project(
        "opensafely", "test", "main", get_github_api=FakeGitHubAPI
    )

    expected = textwrap.dedent(
        """
        actions:
          frobnicate:
        """
    )

    assert pipeline_config == expected


class BrokenOpenCodelistsAPI:
    def check_codelists(self, *args):
        return {"status": "error"}


def test_get_codelists_status():
    codelists_status = get_codelists_status(
        "opensafely",
        "test",
        "main",
        get_github_api=FakeGitHubAPI,
        get_opencodelists_api=FakeOpenCodelistsAPI,
    )
    assert codelists_status == "ok"


def test_get_codelists_status_stale_codelists():
    codelists_status = get_codelists_status(
        "opensafely",
        "test",
        "main",
        get_github_api=FakeGitHubAPI,
        get_opencodelists_api=BrokenOpenCodelistsAPI,
    )
    assert codelists_status == "error"


def test_get_codelists_no_branch():
    class BrokenGitHubAPI:
        def get_branch(self, *args):
            return None

        def get_file(self, *args, **kwargs): ...

    with pytest.raises(Exception, match="Missing branch.*"):
        get_codelists_status(
            "opensafely",
            "test",
            "main",
            get_github_api=BrokenGitHubAPI,
            get_opencodelists_api=BrokenOpenCodelistsAPI,
        )


def test_get_codelists_status_missing_codelists_file():
    class BrokenGitHubAPI:
        def __init__(self):
            self.call_count = 0

        def get_branch(self, *args):
            return True

        def get_file(self, *args, **kwargs):
            # Called 3x, to fetch:
            # 1) codelists.txt
            # 2) codelists.json
            # 3) check that the codelists directory exists
            if self.call_count < 1:
                self.call_count += 1
                return None
            return True

    with pytest.raises(
        Exception, match="Could not find codelists.txt or codelists.json"
    ):
        get_codelists_status(
            "opensafely",
            "test",
            "main",
            get_github_api=BrokenGitHubAPI,
            get_opencodelists_api=BrokenOpenCodelistsAPI,
        )


def test_get_codelists_status_empty_codelists_file():
    class BrokenGitHubAPI:
        def __init__(self):
            self.call_count = 0

        def get_file(self, *args, **kwargs):
            # Called 3x, to fetch:
            content = {
                # codelists.txt, empty file
                0: "",
                # codelists.json, the result of running `opensafely codelists update`
                # on an empty codelists.txt file
                1: '{"files": {}}',
                # check that the codelists directory exists
                2: True,
            }
            response = content[self.call_count]
            self.call_count += 1
            return response

    codelists_status = get_codelists_status(
        "opensafely",
        "test",
        "main",
        get_github_api=BrokenGitHubAPI,
        get_opencodelists_api=FakeOpenCodelistsAPI,
    )
    assert codelists_status == "ok"


def test_get_codelists_status_no_codelist_dir():
    class BrokenGitHubAPI:
        def get_branch(self, *args):
            return True

        def get_file(self, *args, **kwargs):
            return None

    codelists_status = get_codelists_status(
        "opensafely",
        "test",
        "main",
        get_github_api=BrokenGitHubAPI,
        get_opencodelists_api=FakeOpenCodelistsAPI,
    )
    # Codelists.txt and codelists.json don't exist, but as the codelists
    # dir also doesn't exist, the check is ok
    assert codelists_status == "ok"


def test_link_run_scripts():
    line = "some:command --a-switch /output/super-sekret.log /workspace/script1.py ./analysis/script2.do /script3"

    # maintain the line above's readability
    output = list(link_run_scripts(line, link_func))

    expected = [
        "some:command",
        "--a-switch",
        "/output/super-sekret.log",
        '<a href="example.com/script1.py">/workspace/script1.py</a>',
        '<a href="example.com/analysis/script2.do">./analysis/script2.do</a>',
        '<a href="example.com/script3">/script3</a>',
    ]

    assert output == expected


def test_map_run_scripts_to_links():
    content = """
    version: "3.0"

    expectations:
      population_size: 100000

    actions:
      generate_cohort:
        run: cohortextractor:latest generate_cohort
        outputs:
          highly_sensitive:
            cohort1: output/input_af.csv
            cohort2: output/input_af_population_flow_chart.csv
            cohort3: output/input_general_population.csv
            cohort4: output/input_general_population_flow_chart.csv

      # Flowchart for AF population
      flowchart_af:
        run: stata-mp:latest analysis/flow_chart_af_population.do af_population_flowchart
    """

    output = map_run_scripts_to_links(content, link_func)

    expected = {
        "cohortextractor:latest generate_cohort": "cohortextractor:latest generate_cohort",
        "stata-mp:latest analysis/flow_chart_af_population.do af_population_flowchart": 'stata-mp:latest <a href="example.com/analysis/flow_chart_af_population.do">analysis/flow_chart_af_population.do</a> af_population_flowchart',
    }

    assert output == expected


def test_render_definition():
    dummy_yaml = """
    version: "3.0"

    expectations:
      population_size: 100000

    actions:
      generate_cohort:
        run: cohortextractor:latest generate_cohort --study-definition study_definition
        outputs:
          highly_sensitive:
            cohort: output/input.csv

      run_model:
        run: stata-mp:latest analysis/model.do
        needs: [generate_cohortMAIN]
        outputs:
          moderately_sensitive:
            log: logs/model.log

      draw_graphs:
        run: python:latest python analysis/time_series_plots.py
        needs: [run_model]
        outputs:
          moderately_sensitive:
            log: logs/analysis.log
    """

    expected = """<div class="card-body my-0 rounded-0 highlight"><pre><span></span><span class="nt">version</span><span class="p">:</span><span class="w"> </span><span class="s">&quot;3.0&quot;</span>

<span class="w">    </span><span class="nt">expectations</span><span class="p">:</span>
<span class="w">      </span><span class="nt">population_size</span><span class="p">:</span><span class="w"> </span><span class="l l-Scalar l-Scalar-Plain">100000</span>

<span class="w">    </span><span class="nt">actions</span><span class="p">:</span>
<span class="w">      </span><span class="nt">generate_cohort</span><span class="p">:</span>
<span class="w">        </span><span class="nt">run</span><span class="p">:</span><span class="w"> </span><span class="l l-Scalar l-Scalar-Plain">cohortextractor:latest generate_cohort --study-definition study_definition</span>
<span class="w">        </span><span class="nt">outputs</span><span class="p">:</span>
<span class="w">          </span><span class="nt">highly_sensitive</span><span class="p">:</span>
<span class="w">            </span><span class="nt">cohort</span><span class="p">:</span><span class="w"> </span><span class="l l-Scalar l-Scalar-Plain">output/input.csv</span>

<span class="w">      </span><span class="nt">run_model</span><span class="p">:</span>
<span class="w">        </span><span class="nt">run</span><span class="p">:</span><span class="w"> </span><span class="l l-Scalar l-Scalar-Plain">stata-mp:latest <a href="example.com/analysis/model.do">analysis/model.do</a></span>
<span class="w">        </span><span class="nt">needs</span><span class="p">:</span><span class="w"> </span><span class="p p-Indicator">[</span><span class="nv">generate_cohortMAIN</span><span class="p p-Indicator">]</span>
<span class="w">        </span><span class="nt">outputs</span><span class="p">:</span>
<span class="w">          </span><span class="nt">moderately_sensitive</span><span class="p">:</span>
<span class="w">            </span><span class="nt">log</span><span class="p">:</span><span class="w"> </span><span class="l l-Scalar l-Scalar-Plain">logs/model.log</span>

<span class="w">      </span><span class="nt">draw_graphs</span><span class="p">:</span>
<span class="w">        </span><span class="nt">run</span><span class="p">:</span><span class="w"> </span><span class="l l-Scalar l-Scalar-Plain">python:latest python <a href="example.com/analysis/time_series_plots.py">analysis/time_series_plots.py</a></span>
<span class="w">        </span><span class="nt">needs</span><span class="p">:</span><span class="w"> </span><span class="p p-Indicator">[</span><span class="nv">run_model</span><span class="p p-Indicator">]</span>
<span class="w">        </span><span class="nt">outputs</span><span class="p">:</span>
<span class="w">          </span><span class="nt">moderately_sensitive</span><span class="p">:</span>
<span class="w">            </span><span class="nt">log</span><span class="p">:</span><span class="w"> </span><span class="l l-Scalar l-Scalar-Plain">logs/analysis.log</span>
</pre></div>\n"""

    output = render_definition(dummy_yaml, link_func)

    assert output == expected


@pytest.mark.parametrize(
    "actions,expected_db_actions",
    [
        # ehrql action
        (
            {
                "generate_dataset": {
                    "run": "ehrql:v0 generate-dataset --dataset-definition some/path --output some/other/path.csv",
                    "outputs": {"highly_sensitive": {"dataset": "some/other/path.csv"}},
                }
            },
            ["generate_dataset"],
        ),
        # cohort-extractor action
        (
            {
                "generate_cohort": {
                    "run": "cohortextractor:latest generate_cohort --study-definition some/path --output some/other/path.csv",
                    "outputs": {"highly_sensitive": {"cohort": "some/other/path.csv"}},
                }
            },
            ["generate_cohort"],
        ),
        # multiple actions, some non-database ones
        (
            {
                "generate_cohort": {
                    "run": "cohortextractor:latest generate_cohort --study-definition some/path --output some/cohort/path.csv",
                    "outputs": {"highly_sensitive": {"cohort": "some/cohort/path.csv"}},
                },
                "generate_cohort_measures": {
                    "run": "cohortextractor:latest generate_measures --study-definition some/path --output some/measures/path.csv",
                    "outputs": {
                        "highly_sensitive": {"cohort": "some/measures/path.csv"}
                    },
                },
                "generate_dataset": {
                    "run": "ehrql:v0 generate-dataset --dataset-definition some/path --output some/dataset/path.csv",
                    "outputs": {
                        "highly_sensitive": {"dataset": "some/dataset/path.csv"}
                    },
                },
                "generate_ehrql_measures": {
                    "run": "ehrql:v0 generate-measures --measures-definition some/path --output some/ehrql/measures/path.csv",
                    "outputs": {
                        "highly_sensitive": {"dataset": "some/ehrql/measures/path.csv"}
                    },
                },
                "make_chart": {
                    "run": "python:latest make-chart.py",
                    "outputs": {
                        "moderately_sensitive": {"chart": "some/chart/path.png"}
                    },
                },
            },
            ["generate_cohort", "generate_dataset", "generate_ehrql_measures"],
        ),
        # ehrql/cohort-extractor actions, but not
        (
            {
                "generate_cohort": {
                    "run": "cohortextractor:latest cohort_report",
                    "outputs": {"moderately_sensitive": {"cohort": "some/path.csv"}},
                },
                "generate_dataset": {
                    "run": "ehrql:v0 dump-dataset-sql --dataset-definition some/path --output some/dataset/path.csv",
                    "outputs": {
                        "moderately_sensitive": {"dataset": "some/dataset/path.csv"}
                    },
                },
            },
            [],
        ),
    ],
)
def test_get_database_actions(actions, expected_db_actions):
    content = Pipeline.build(
        **{
            "version": 3,
            "expectations": {"population_size": 1000},
            "actions": actions,
        }
    )
    assert list(get_database_actions(content)) == expected_db_actions
