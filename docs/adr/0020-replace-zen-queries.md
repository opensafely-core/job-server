# 20. Replace Zen Queries

Date: 2024-07-10

## Status

Accepted

## Context

Zen Queries is a third-party library that throws an exception if a database query is made unexpectedly in a template. We've been using it in Job Server for a [year](https://github.com/opensafely-core/job-server/commit/baee5890f2652aab9d1a95faf0651cd8ec8dd304), as we encountered some [performance issues](https://github.com/opensafely-core/job-server/pull/3591/commits/0ebf4e7bd8d2a3621d27e5ee1091e0d1f114d5af) when accidentally making additional database calls in some of our templates and we need some way of being alerted when this happens.

However, Zen Queries throws an exception in both production and development mode. As a result, users have encountered this error before developers. The exception message is also not very informative and it's not always clear what action to take (see [here](https://bennettoxford.slack.com/archives/C069SADHP1Q/p1708035538382269) and [here](https://bennettoxford.slack.com/archives/C069SADHP1Q/p1708946787197529)).

Options:
1. Keep Zen Queries and add tests to check the template is rendered without exceptions being thrown.
1. Remove Zen Queries and add tests to check the number of database queries in the rendered template is what we expect.
1. Remove Zen Queries and do nothing, as before.

## Decision

We will remove Zen Queries and add tests to check the number of database queries in the rendered template is what we expect.

We will use `django_assert_num_queries` to check the view and rendered template. For example this test will fail if the number of database queries in the view changes from the expected eight or 10 when including the rendered template:

```python
def test_jobrequestdetail_count_db_queries(
    client, rf, django_assert_num_queries
):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, updated_at=minutes_ago(timezone.now(), 31))
    request = rf.get("/")
    request.user = UserFactory()

    with django_assert_num_queries(8):
        response = JobRequestDetail.as_view()(
            request,
            project_slug=job_request.workspace.project.slug,
            workspace_slug=job_request.workspace.name,
            pk=job_request.pk,
        )

    with django_assert_num_queries(10):
        response = client.get(job_request.get_absolute_url())
        assert response.status_code == 200
        assert job_request.identifier in response.rendered_content
```

## Consequences

We now have one less dependency. We've already using `django_assert_num_queries` as it comes with pytest-django, which we use as standard with our Django projects.

This approach is more transparent. It's easy to see from the above code the number of database queries being made and where they're being made. If something changes, then the developer receives a clear error message, with an option to see the generated queries, and the affected code doesn't make it into production.

This removes extraneous (and somewhat mysterious) code from our views and templates. e.g the decorator `@queries_dangerously_enabled()` and `{% queries_dangerously_enabled %}` codeblocks.
