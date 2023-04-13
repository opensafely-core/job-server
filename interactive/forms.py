import functools

from django import forms


def list_to_choices(lst):
    return [(item, item) for item in lst]


def field_to_choices(codelists, field):
    return [(c[field], "") for c in codelists]


class AnalysisRequestForm(forms.Form):
    purpose = forms.CharField()
    demographics = forms.MultipleChoiceField(
        choices=list_to_choices(
            [
                "age",
                "ethnicity",
                "imd",
                "region",
                "sex",
            ]
        ),
        required=False,
    )
    filter_population = forms.ChoiceField(
        choices=list_to_choices(["all", "adults", "children"])
    )
    time_ever = forms.BooleanField(required=False)
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
            self.fields["time_scale"].required = True
            self.fields["time_value"].required = True

    def clean(self):
        cleaned_data = super().clean()

        if not self.has_codelist_2:
            return

        time_ever = cleaned_data["time_ever"]
        time_scale = cleaned_data["time_scale"]
        time_value = cleaned_data["time_value"]

        if time_ever and (time_scale or time_value):
            raise forms.ValidationError(
                "Time ever cannot be set with either time scale or value"
            )

        # time_value must be less than 10 years but it's paired with time_scale
        # so we have to check it for each of the choices of that field.

        weeks_over = time_scale == "weeks" and time_value > 520
        months_over = time_scale == "months" and time_value > 120
        years_over = time_scale == "years" and time_value > 10

        if any([weeks_over, months_over, years_over]):
            raise forms.ValidationError("Time scale cannot be longer than 10 years")
