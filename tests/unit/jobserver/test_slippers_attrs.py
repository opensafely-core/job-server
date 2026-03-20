from django.template import Context, Template


# Tests that our hotfix has been correctly applied
def test_slippers_attrs_escapes_html():
    template = Template("<input {% attrs my-attr=some_value %}>")
    context = Context({"some_value": '">'})
    assert template.render(context) == '<input my-attr="&quot;&gt;">'


# Tests for coverage
def test_slippers_attrs_handles_booleans():
    template = Template("<input {% attrs bool-1=bool1 bool-2=bool2 %}>")
    context = Context({"bool1": True, "bool2": False})
    assert template.render(context) == "<input bool-1>"
