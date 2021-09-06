import pytest
from furl import furl
from yaml.scanner import ScannerError

from jobserver.project import (
    get_actions,
    get_project,
    link_run_scripts,
    load_yaml,
    map_run_scripts_to_links,
    render_definition,
)


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


def test_get_actions_empty_needs():
    dummy = {
        "actions": {
            "frobnicate": {
                "needs": None,
            }
        }
    }
    output = list(get_actions(dummy, {"frobnicate": "test"}))

    expected = [
        {"name": "frobnicate", "needs": [], "status": "test"},
        {"name": "run_all", "needs": ["frobnicate"], "status": "-"},
    ]
    assert output == expected


def test_get_actions_no_run_all():
    dummy = {
        "actions": {
            "frobnicate": {},
            "run_all": {
                "needs": ["frobnicate"],
            },
        }
    }

    action_status_lut = {
        "frobnicate": "running",
        "twiddle": "pending",
    }

    output = list(get_actions(dummy, action_status_lut))

    expected = [
        {"name": "frobnicate", "needs": [], "status": "running"},
        {"name": "run_all", "needs": ["frobnicate"], "status": "-"},
    ]
    assert output == expected


def test_get_actions_success():
    content = {
        "actions": {
            "frobnicate": {},
        }
    }
    output = list(get_actions(content, {"frobnicate": "test"}))

    expected = [
        {"name": "frobnicate", "needs": [], "status": "test"},
        {"name": "run_all", "needs": ["frobnicate"], "status": "-"},
    ]
    assert output == expected


def test_get_project_no_branch(mocker):
    mocker.patch("jobserver.project.get_file", autospec=True, return_value=None),
    mocker.patch("jobserver.project.get_branch", autospec=True, return_value=None)

    with pytest.raises(Exception, match="Missing branch: 'main'"):
        get_project("opensafely", "test", "main")


def test_get_project_no_project_yaml(mocker):
    mocker.patch("jobserver.project.get_file", autospec=True, return_value=None),
    mocker.patch("jobserver.project.get_branch", autospec=True, return_value=True)

    with pytest.raises(Exception, match="Could not find project.yaml"):
        get_project("opensafely", "test", "main")


def test_get_project_success(mocker):
    dummy = """
    actions:
      frobnicate:
    """
    mocker.patch("jobserver.project.get_file", autospec=True, return_value=dummy)
    mocker.patch("jobserver.project.get_branch", autospec=True, return_value=True)

    assert get_project("opensafely", "test", "main") == dummy


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


def test_load_yaml_invalid_yaml():
    dummy_yaml = """
    <<<<<<< HEAD
    actions:
      frobnicate:
    """
    with pytest.raises(ScannerError):
        load_yaml(dummy_yaml)


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

    expected = """<div class="card-body my-0 rounded-0 highlight"><pre><span></span><span class="nt">version</span><span class="p">:</span> <span class="s">&quot;3.0&quot;</span>

    <span class="nt">expectations</span><span class="p">:</span>
      <span class="nt">population_size</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">100000</span>

    <span class="nt">actions</span><span class="p">:</span>
      <span class="nt">generate_cohort</span><span class="p">:</span>
        <span class="nt">run</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">cohortextractor:latest generate_cohort --study-definition study_definition</span>
        <span class="nt">outputs</span><span class="p">:</span>
          <span class="nt">highly_sensitive</span><span class="p">:</span>
            <span class="nt">cohort</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">output/input.csv</span>

      <span class="nt">run_model</span><span class="p">:</span>
        <span class="nt">run</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">stata-mp:latest <a href="example.com/analysis/model.do">analysis/model.do</a></span>
        <span class="nt">needs</span><span class="p">:</span> <span class="p p-Indicator">[</span><span class="nv">generate_cohortMAIN</span><span class="p p-Indicator">]</span>
        <span class="nt">outputs</span><span class="p">:</span>
          <span class="nt">moderately_sensitive</span><span class="p">:</span>
            <span class="nt">log</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">logs/model.log</span>

      <span class="nt">draw_graphs</span><span class="p">:</span>
        <span class="nt">run</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">python:latest python <a href="example.com/analysis/time_series_plots.py">analysis/time_series_plots.py</a></span>
        <span class="nt">needs</span><span class="p">:</span> <span class="p p-Indicator">[</span><span class="nv">run_model</span><span class="p p-Indicator">]</span>
        <span class="nt">outputs</span><span class="p">:</span>
          <span class="nt">moderately_sensitive</span><span class="p">:</span>
            <span class="nt">log</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">logs/analysis.log</span>
</pre></div>\n"""

    output = render_definition(dummy_yaml, link_func)

    assert output == expected
