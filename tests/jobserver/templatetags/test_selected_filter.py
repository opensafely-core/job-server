from jobserver.templatetags.selected_filter import is_filter_selected


def test_isfilterselected_different_value(rf):
    context = {"request": rf.get("/")}

    output = is_filter_selected(context, key="key", value="value")

    assert output is False


def test_isfilterselected_missing_filter(rf):
    context = {"request": rf.get("/?key=another-value")}

    output = is_filter_selected(context, key="key", value="value")

    assert output is False


def test_isfilterselected_success(rf):
    context = {"request": rf.get("/?key=value")}

    output = is_filter_selected(context, key="key", value="value")

    assert output is True
