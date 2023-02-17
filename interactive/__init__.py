from attrs import define


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
    frequency: str
    repo: str
    time_event: str
    time_scale: str
    time_value: str
    title: str
    id: str | None = None  # noqa: A003
