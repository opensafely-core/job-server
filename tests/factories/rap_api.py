from tests.utils import minutes_ago, seconds_ago


def isoformat_datetime(dt):
    if dt is not None:
        dt = dt.isoformat()
    return dt


def rap_status_response_factory(jobs, unrecognised_rap_ids, now):
    jobs_response = []
    for job in jobs:
        jobs_response.append(
            {
                "identifier": job.get("identifier", "identifier-0"),
                "rap_id": job.get("rap_id", "rap-identifier-0"),
                "action": job.get("action", "test-action1"),
                "backend": job.get("backend", "test"),
                "run_command": job.get("run_command", "do-research"),
                "requires_db": job.get("requires_db", "false"),
                "status": job.get("status", "succeeded"),
                "status_code": "",
                "status_message": "",
                # datetimes in the json response from the RAP API are received as isoformat strings
                "created_at": isoformat_datetime(
                    job.get("created_at", minutes_ago(now, 2))
                ),
                "started_at": isoformat_datetime(
                    job.get("started_at", minutes_ago(now, 1))
                ),
                "updated_at": now.isoformat(),
                "completed_at": isoformat_datetime(
                    job.get("completed_at", seconds_ago(now, 30))
                ),
                "metrics": {"cpu_peak": 99},
            }
        )
    return {
        "jobs": jobs_response,
        "unrecognised_rap_ids": unrecognised_rap_ids,
    }
