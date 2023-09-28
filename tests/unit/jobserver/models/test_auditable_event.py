from jobserver.models import AuditableEvent
from tests.factories import AuditableEventFactory


def test_auditableevent_str():
    event = AuditableEventFactory(
        type=AuditableEvent.Type.PROJECT_MEMBER_ADDED,
        old="[foo]",
        new="[]",
        target_model="User",
        target_field="roles",
        target_id="123",
        created_by="beng",
    )

    assert str(event) == f"pk={event.pk} type=project_member_added"
