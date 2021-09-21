from applications.forms import ApplicationFormBase
from applications.models import Application

from ...factories import ApplicationFactory


class ApplicationForm(ApplicationFormBase):
    class Meta:
        fields = [
            "email",
            "is_study_research",
            "need_record_level_data",
        ]
        model = Application


form_spec = {
    "key": 1,
    "title": "title",
    "sub_title": "subtitle",
    "rubric": "rubric",
    "fieldsets": [
        {
            "label": "Fieldset 1",
            "fields": [
                {
                    "name": "email",
                    "label": "Email",
                },
                {
                    "name": "is_study_research",
                    "label": "Is Study Research?",
                },
            ],
        },
        {
            "label": "Fieldset 2",
            "fields": [
                {
                    "name": "need_record_level_data",
                    "label": "Need Record Level Data?",
                },
            ],
        },
    ],
}


def test_applicationformbase():
    application = ApplicationFactory()

    form = ApplicationForm(instance=application)
    form.spec = form_spec

    output = form.as_html()

    assert output.count("<fieldset") == 2

    # is_study_research is a BooleanField so we should have a checkbox input
    assert output.count('type="checkbox"') == 1
    assert "Is Study Research?" in output

    # email is a CharField so we should have a text input
    assert output.count('type="text"') == 1
    assert "Email" in output

    # need_record_level_data is a TypedChoiceField so we should have two radio
    # inputs (one each for Yes and No)
    assert output.count('type="radio"') == 2
    assert "Need Record Level Data?" in output
