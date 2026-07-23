import os
import time

import pytest
from django.test import override_settings

from jobserver.jobs.quarter_hourly import delete_raw_dump


@pytest.fixture(autouse=True)
def frozen_time(freezer):
    """Use a fixed current time when calculating dump ages."""
    freezer.move_to("2026-07-22 12:00:00")


@pytest.fixture
def raw_dump_path(tmp_path):
    """Configure the job to use a temporary file."""
    path = tmp_path / "jobserver.dump"

    with override_settings(RAW_DATABASE_DUMP_PATH=path):
        yield path


def create_dump_with_age(path, dump_age):
    """Create a test dump with the requested age."""
    path.write_bytes(b"test dump")
    modified_at = time.time() - dump_age
    os.utime(path, (modified_at, modified_at))


def test_does_nothing_when_raw_dump_does_not_exist(raw_dump_path, log_output):
    delete_raw_dump.Job().execute()

    assert not raw_dump_path.exists()
    assert len(log_output.entries) == 1
    assert log_output.entries[0]["event"] == "Raw database dump does not exist"
    assert log_output.entries[0]["path"] == raw_dump_path


def test_does_not_delete_dump_below_age_limit(raw_dump_path, log_output):
    dump_age = delete_raw_dump.RAW_DUMP_AGE_LIMIT - 1
    create_dump_with_age(raw_dump_path, dump_age)

    delete_raw_dump.Job().execute()

    assert raw_dump_path.exists()
    assert (
        log_output.entries[0]["event"]
        == "Raw database dump not deleted as it had not reached deletion age"
    )
    assert log_output.entries[0]["dump_age"] == dump_age
    assert log_output.entries[0]["deletion_age"] == delete_raw_dump.RAW_DUMP_AGE_LIMIT
    assert log_output.entries[0]["path"] == raw_dump_path


def test_deletes_dump_at_age_limit(raw_dump_path, log_output):
    dump_age = delete_raw_dump.RAW_DUMP_AGE_LIMIT
    create_dump_with_age(raw_dump_path, dump_age)

    delete_raw_dump.Job().execute()

    assert not raw_dump_path.exists()
    assert (
        log_output.entries[0]["event"]
        == "Deleted raw database dump as it had reached deletion age"
    )
    assert log_output.entries[0]["dump_age"] == dump_age
    assert log_output.entries[0]["path"] == raw_dump_path
