from django import forms


def codelists_to_choices(codelists):
    return [(c["slug"], c["name"]) for c in codelists]


class AnalysisRequestForm(forms.Form):
    def __init__(self, *args, **kwargs):
        events = kwargs.pop("events")
        medications = kwargs.pop("medications")

        super().__init__(*args, **kwargs)

        # combine both lists of codelists into a single set of choices.  Both
        # codelist fields need to be able to accept a codelist from either list.
        codelists = codelists_to_choices(events + medications)

        self.fields["codelist_a"] = forms.ChoiceField(choices=codelists)
        self.fields["codelist_b"] = forms.ChoiceField(choices=codelists)
