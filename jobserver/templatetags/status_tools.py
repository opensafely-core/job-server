import os

import structlog
from django import template
from django.utils.safestring import mark_safe


logger = structlog.get_logger()
register = template.Library()


def nonzero_exit(job):
    path = os.path.join(
        job.job_request.backend.parent_directory,
        job.job_request.workspace.name,
        "metadata",
        f"{job.action}.log",
    )

    return mark_safe(
        f"""
        <small class="d-block mb-1">
          The job exited with an error. You can check the log output by logging
          into the {job.job_request.backend.display_name} server and looking at:
        </small>

        <pre>{path}</pre>
        """
    )


#  A mapping of Job status codes -> descriptions of how to fix them
status_hints = {
    "tpp": {
        "waiting_on_dependencies": lambda j: "",
        "dependency_failed": lambda j: "",
        "waiting_on_workers": lambda j: "",
        "nonzero_exit": nonzero_exit,
    },
}


@register.simple_tag
def status_hint(job):
    """
    Convert a status code into a description or empty string

    A helpter tag for mapping a Job's status_code to the description of what to
    do.  Descriptions are backend specific.
    """
    backend = job.job_request.backend

    description_lut = status_hints.get(backend.slug, None)
    if not description_lut:
        logger.info(f"Unknown backend: {backend.slug}")
        return ""

    description_func = description_lut.get(job.status_code, None)
    if not description_func:
        logger.info(f"Unknown status code: {job.status_code}", backend=backend)
        return ""

    return description_func(job)
