from django import forms

from applications.forms import YesNoField


def test_yesnofield_coerce():
    class Form(forms.Form):
        yes_no_field = YesNoField()

    # "True" coerces to True
    form = Form({"yes_no_field": "True"})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["yes_no_field"]

    # "False" coerces to False
    form = Form({"yes_no_field": "False"})
    assert form.is_valid(), form.errors
    assert not form.cleaned_data["yes_no_field"]
