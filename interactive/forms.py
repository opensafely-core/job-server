import functools

from django import forms


def list_to_choices(lst):
    return [(item, item) for item in lst]


def field_to_choices(codelists, field):
    return [(c[field], "") for c in codelists]


class AnalysisRequestForm(forms.Form):
    demographics = forms.MultipleChoiceField(
        choices=list_to_choices(
            [
                "age",
                "ethnicity",
                "imd",
                "region",
                "sex",
            ]
        )
    )
    filter_population = forms.ChoiceField(
        choices=list_to_choices(["all", "adults", "children"])
    )
    frequency = forms.ChoiceField(
        choices=list_to_choices(["monthly", "quarterly", "yearly"])
    )
    time_event = forms.ChoiceField(
        choices=list_to_choices(["before", "after"]), required=False
    )
    time_scale = forms.ChoiceField(
        choices=list_to_choices(["weeks", "months", "years"]), required=False
    )
    time_value = forms.IntegerField(min_value=1, required=False)

    def __init__(self, *args, **kwargs):
        codelists = kwargs.pop("codelists")
        choices = functools.partial(field_to_choices, codelists)

        super().__init__(*args, **kwargs)

        self.fields["codelist_1_label"] = forms.ChoiceField(choices=choices("name"))
        self.fields["codelist_1_slug"] = forms.ChoiceField(choices=choices("slug"))

        self.has_codelist_2 = any(
            [
                "codelist_2_label" in kwargs.get("data", {}),
                "codelist_2_slug" in kwargs.get("data", {}),
            ]
        )

        if self.has_codelist_2:
            self.fields["codelist_2_label"] = forms.ChoiceField(choices=choices("name"))
            self.fields["codelist_2_slug"] = forms.ChoiceField(choices=choices("slug"))
            self.fields["time_event"].required = True
            self.fields["time_scale"].required = True
            self.fields["time_value"].required = True

    def clean(self):
        cleaned_data = super().clean()

        if not self.has_codelist_2:
            return

        time_scale = cleaned_data["time_scale"]
        time_value = cleaned_data["time_value"]

        # time_value must be less than 5 years but it's paired with time_scale
        # so we have to check it for each of the choices of that field.

        if time_scale == "weeks" and time_value > 260:
            raise forms.ValidationError("")

        if time_scale == "months" and time_value > 60:
            raise forms.ValidationError("")

        if time_scale == "years" and time_value > 5:
            raise forms.ValidationError("")
