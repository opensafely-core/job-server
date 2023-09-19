from tests.factories import AuditableEventFactory


def test_auditableevent_str_with_changed_by():
    event = AuditableEventFactory(
        old="[foo]",
        new="[]",
        target_model="User",
        target_field="roles",
        target_id="123",
        created_by="beng",
    )

    assert str(event) == "User(pk=123) beng changed roles from '[foo]' to '[]'"


def test_auditableevent_str_without_changed_by():
    event = AuditableEventFactory(
        old="[]",
        new="[foo]",
        target_model="ProjectMembership",
        target_field="roles",
        target_id="123",
    )

    assert str(event) == "ProjectMembership(pk=123) roles changed from '[]' to '[foo]'"
